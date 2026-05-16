"""Run once to seed the first admin user: python create_admin.py"""
import sys
from app.core.database import engine, SessionLocal
from app.core import database as _db
from app.core.security import hash_password
import app.models  # registers all models

_db.Base.metadata.create_all(bind=engine)

email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
password = sys.argv[2] if len(sys.argv) > 2 else "admin123"

from app.models.user import User

db = SessionLocal()
try:
    if db.query(User).filter(User.email == email).first():
        print(f"User {email} already exists.")
    else:
        db.add(User(email=email, password_hash=hash_password(password), role="admin"))
        db.commit()
        print(f"Admin user created: {email} / {password}")
finally:
    db.close()
