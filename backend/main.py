import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.orm import Session

from app.core.database import engine, SessionLocal
from app.core import database as _db_module
from app.core.config import settings
from app.core.security import hash_password
import app.models  # ensure all models are registered before create_all
from app.models.user import User
from app.api import auth, traffic, devices, sessions, alerts, reports, internal
from app.websocket.manager import router as ws_router
import app.aggregator as aggregator

logger = logging.getLogger(__name__)


def _migrate_processed_column():
    """Add the `processed` column to traffic_logs if it was created before Phase 2."""
    try:
        existing = [c["name"] for c in sa_inspect(engine).get_columns("traffic_logs")]
        if "processed" not in existing:
            with engine.connect() as conn:
                if settings.DATABASE_URL.startswith("sqlite"):
                    conn.execute(text(
                        "ALTER TABLE traffic_logs "
                        "ADD COLUMN processed BOOLEAN NOT NULL DEFAULT 0"
                    ))
                else:
                    conn.execute(text(
                        "ALTER TABLE traffic_logs "
                        "ADD COLUMN processed BOOLEAN NOT NULL DEFAULT FALSE"
                    ))
                conn.commit()
            logger.info("Migration: added 'processed' column to traffic_logs")
    except Exception:
        logger.exception("Migration failed — aggregator may not work correctly")


def _bootstrap_admin():
    """Create the first admin user if the users table is empty."""
    try:
        db: Session = SessionLocal()
        try:
            if db.query(User).count() == 0:
                admin = User(
                    email=settings.FIRST_ADMIN_EMAIL,
                    password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
                    role="admin",
                )
                db.add(admin)
                db.commit()
                logger.info(
                    "Bootstrap: created first admin user <%s>",
                    settings.FIRST_ADMIN_EMAIL,
                )
        finally:
            db.close()
    except Exception:
        logger.exception("Bootstrap admin failed")


# Initialize DB synchronously before app starts
_db_module.Base.metadata.create_all(bind=engine)
_migrate_processed_column()
_bootstrap_admin()

@asynccontextmanager
async def lifespan(app: FastAPI):
    aggregator.start()
    yield
    aggregator.stop()


app = FastAPI(title="Network Analyzer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(traffic.router, prefix="/api/traffic", tags=["traffic"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(internal.router, prefix="/api/internal", tags=["internal"])
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
