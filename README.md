# AI Career Platform

Review 1 implements one real vertical slice from the SRS: User Registration & Authentication.

## What Works

- React register and login screens
- FastAPI `/auth/register`, `/auth/login`, and protected `/auth/me`
- PostgreSQL-backed `accounts`, `students`, `mentors`, and `administrators` tables
- Password hashing with bcrypt
- JWT issue and validation
- Existing prototype dashboard remains available after login

## Run Locally

Start PostgreSQL and FastAPI:

```bash
docker compose up --build
```

Start React in another terminal:

```bash
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173/
```

Use the register screen first, then log in. The frontend stores the JWT in `localStorage` and calls `/auth/me` to validate the session.

## Without Docker

If Docker is unavailable, run PostgreSQL locally, create the `career_platform` database, then start the API:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
# AI-Carrer-Platform
