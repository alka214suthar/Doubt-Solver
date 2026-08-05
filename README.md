# AI Doubt Solver

Full-stack app for students to ask academic doubts, get AI solutions, bookmark questions, and track progress.

## Project structure

```text
Doubt-Solver/
├── backend/                 # FastAPI API
│   ├── alembic/
│   ├── routes/ service/ repo/ models/
│   ├── uploads/
│   ├── Dockerfile
│   ├── Procfile
│   ├── .env.example
│   └── requirements.txt
├── src/                     # React (Vite) frontend
├── Dockerfile               # Frontend production image (nginx)
├── docker-compose.yml
├── nginx.conf
├── .env.example             # Frontend env template
└── package.json
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL (or Docker)

## Local development

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
# edit .env with DATABASE_URL and GEMINI_API_KEY
uvicorn main:app --reload
```

API: `http://localhost:8000`  
Health: `http://localhost:8000/health`

### 2. Frontend

```bash
cp .env.example .env   # optional; defaults to http://localhost:8000
npm install
npm run dev
```

App: `http://localhost:5173`

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `CORS_ORIGINS` | Yes (prod) | Exact frontend origin(s), comma-separated. Never `*` |
| `JWT_SECRET` | Yes (prod) | Secret used to sign access tokens |
| `APP_ENV` | No | `development` or `production` |
| `PORT` | No | Default `8000` |
| `UPLOAD_DIR` | No | Default `uploads` |

### Frontend (`.env` / host build settings)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes (prod) | Public backend API URL, no trailing slash |

Never commit `.env`, `venv/`, `node_modules/`, `dist/`, or uploaded files.

## Deploy with Docker

```bash
# set secrets in backend/.env first
docker compose up --build -d
```

- Frontend: `http://localhost`
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`

## Deploy without Docker

### Backend (Render / Railway / any VPS)

1. Set root directory to `backend`
2. Install: `pip install -r requirements.txt`
3. **Release / migrate (run once per deploy, not on every web replica):** `alembic upgrade head`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configure env vars: `DATABASE_URL`, `GEMINI_API_KEY`, `CORS_ORIGINS`, `APP_ENV=production`, `JWT_SECRET`

On Heroku-compatible hosts the `Procfile` already defines:

```text
release: alembic upgrade head
web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend (Vercel / Netlify / Cloudflare Pages)

1. Build command: `npm run build`
2. Output directory: `dist`
3. Set `VITE_API_BASE_URL` to your live backend URL
4. Redeploy after changing API URL (Vite bakes it in at build time)

## Production checklist

- [ ] `DATABASE_URL` points to managed Postgres
- [ ] `GEMINI_API_KEY` set
- [ ] `JWT_SECRET` set
- [ ] `CORS_ORIGINS` is exact production domain(s), never `*`
- [ ] `VITE_API_BASE_URL` points to your live backend
- [ ] Run `alembic upgrade head` via release command / one-shot migrate job
- [ ] Confirm `/health/live` returns ok
- [ ] Confirm uploads volume/storage is persistent

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start frontend |
| `npm run build` | Build frontend |
| `npm run preview` | Preview production build |
| `npm test` | Frontend Vitest suite |
| `npm run lint` | Frontend ESLint |
| `uvicorn main:app --reload` | Start backend locally |
| `alembic upgrade head` | Apply DB migrations (release/migrate job) |
| `docker compose up --build` | Run full stack (migrate runs once before backend) |

## Testing

### Backend

From `backend/` (recommended with the venv activated):

```bash
cd backend
pytest
```

Or from the repo root:

```bash
pytest
```

### Frontend

From the repo root:

```bash
npm test
npm run lint
npm run build
```

