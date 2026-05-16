# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NetAnalyzer** — a Network Observability + Security Monitoring web application (PFE project). Full product requirements are in `PRD.md`.

Three runtime services communicate over Docker networking:
- **Backend** (FastAPI) — REST API + WebSocket + Celery workers
- **Capture** (Scapy) — packet sniffer that POSTs batches to the backend
- **Frontend** (React + Vite) — dark-theme dashboard served by nginx

## Commands

### Docker (recommended — runs everything)
```bash
cp .env.example .env          # first time only; edit SECRET_KEY
docker compose up --build     # start all services
docker compose down           # stop
docker compose logs -f backend  # tail a specific service
```

After first boot, create the admin user:
```bash
docker compose exec backend python create_admin.py admin@example.com mypassword
```

App is at **http://localhost** · API at **http://localhost:8000** · Swagger at **http://localhost:8000/docs**

### Backend (local dev)
```bash
cd backend
pip install -r requirements.txt
# Needs a running PostgreSQL and Redis (or use Docker for those)
uvicorn main:app --reload
celery -A app.workers.celery_app worker -l info   # background tasks
python create_admin.py                             # seed admin user
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev       # http://localhost:3000 (proxies /api and /ws to :8000)
npm run build
npm run lint
```

### Capture (local dev — requires root)
```bash
cd capture
pip install -r requirements.txt
sudo BACKEND_URL=http://localhost:8000 python main.py
```

## Architecture

### Data Flow
```
[Network interface]
       │ Scapy sniff
       ▼
  capture/main.py
       │ POST /api/internal/batch  (x-api-key header)
       ▼
  backend/main.py (FastAPI)
       │ writes → PostgreSQL
       │ triggers → Celery task (anomaly check via Redis)
       ▼
  WebSocket /ws/live  ←── frontend polls every 1 second
```

### Backend Layout (`backend/`)
| Path | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS, DB init on startup |
| `app/core/config.py` | Settings via `pydantic-settings` (reads `.env`) |
| `app/core/database.py` | SQLAlchemy engine + `get_db()` dependency |
| `app/core/security.py` | JWT encode/decode, bcrypt, `get_current_user` dependency |
| `app/models/` | SQLAlchemy ORM models (one file per table) |
| `app/schemas/` | Pydantic request/response models |
| `app/api/` | FastAPI routers — one file per resource |
| `app/api/internal.py` | Endpoints for capture service only (protected by `x-api-key`) |
| `app/workers/celery_app.py` | Celery + Beat configuration |
| `app/workers/tasks.py` | Anomaly detection, device offline sweep, log cleanup |
| `app/websocket/manager.py` | WebSocket endpoint `/ws/live`, pushes metrics every second |

### Frontend Layout (`frontend/src/`)
| Path | Responsibility |
|---|---|
| `App.jsx` | Router; `PrivateRoute` wrapper |
| `api/client.js` | Axios instance — injects JWT, redirects on 401 |
| `hooks/useWebSocket.js` | Auto-reconnecting WebSocket hook |
| `hooks/useAuth.js` | Login / logout / current user |
| `components/` | `Layout`, `StatCard`, `LiveBandwidthChart`, `ProtocolChart`, `AlertBadge`, `DataTable` |
| `pages/` | Dashboard, Devices, Sessions, Alerts, Reports, Settings, Login |

### Capture Layout (`capture/`)
| File | Responsibility |
|---|---|
| `main.py` | Entry point, drain loop, send batches to backend |
| `capture_engine.py` | Scapy sniffer in a background thread, parsed packets into a queue |
| `classifier.py` | Port-based Layer 7 category mapping |
| `geoip.py` | Free GeoIP lookup via ip-api.com (cached per IP) |

## Key Design Decisions

- **Capture runs with `network_mode: host` + `privileged: true`** in Docker so Scapy can access raw sockets. On the host it requires `sudo`.
- **Internal endpoints** (`/api/internal/*`) are protected by `x-api-key: INTERNAL_API_KEY` — not JWT. Never expose port 8000 directly in production.
- **WebSocket** at `/ws/live` is polled by the frontend every second. It queries the DB directly (no separate pub/sub). For high-traffic deployments, add a Redis pub/sub layer between Celery tasks and the WS endpoint.
- **Anomaly detection** runs as a Celery task triggered per packet batch. Counters are stored in Redis with TTL. Thresholds: 50 connections/min → scanning alert; 10 MB/min → bandwidth alert; 200 DNS queries/min → protocol anomaly.
- **Session aggregation** is not implemented in the capture engine yet — the `sessions` table and API exist but sessions must be built from `traffic_logs` in a Celery beat task (Phase 2 work).
- **GeoIP** uses ip-api.com free tier (1500 req/min). For production, switch to a local MaxMind GeoLite2 DB via `geoip2`.

## Database Schema

Tables: `traffic_logs`, `devices`, `sessions`, `alerts`, `users`. All created automatically via `Base.metadata.create_all()` on backend startup — no migrations needed for development. For production use Alembic.

## User Roles
`admin` → full access including user management  
`analyst` → read/write on traffic, devices, sessions, alerts  
`viewer` → read-only
