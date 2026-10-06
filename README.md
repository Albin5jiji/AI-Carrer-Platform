# AI Career Platform

Student career readiness and placement management platform.

- **Frontend:** React 19 + Vite + TypeScript (hash router, no UI framework)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (Python 3.11+, verified on 3.12)
- **AI advisory:** optional OpenAI-compatible endpoint for skill-gap analysis (disabled by default)

---

## Launch it every time

Three terminals: database + API, then seed (first run only), then frontend.

### 0. Prerequisites

| Tool      | Version            | Check            |
| --------- | ------------------ | ---------------- |
| Docker    | any recent Desktop | `docker --version` |
| Node.js   | 20+ (verified 24)  | `node --version` |
| Python    | 3.11+ (verified 3.12) | `python3 --version` |

### 1. Start PostgreSQL + the API

From the repository root:

```bash
docker compose up --build -d
```

This starts:

| Service    | Port  | Notes                                  |
| ---------- | ----- | -------------------------------------- |
| `postgres` | 5432  | db `career_platform`, user `career_user` |
| `api`      | 8000  | FastAPI, waits for postgres to be healthy |

On startup the API auto-creates all tables (`AUTO_CREATE_TABLES=true`) and seeds the
reference dataset (role skill matrix, learning resources, interview question bank).

Check it is up:

```bash
curl http://127.0.0.1:8000/health        # {"status":"ok",...}
open http://127.0.0.1:8000/docs          # Swagger UI
```

### 2. Seed demo data (first run, or after resetting the database)

The API container does not include the demo seed script, so run it from the host.
One-time setup of the Python environment:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then, **with the database running** (step 1):

```bash
cd backend
. .venv/bin/activate
python -m scripts.seed_demo
```

Idempotent — safe to re-run. Output:

```
Demo dataset ready.
  admin@campus.edu        / Admin@12345
  mentor@campus.edu       / Mentor@12345
  mentor2@campus.edu      / Mentor@12345
  albin@vitstudent.ac.in  / Student@12345
  priya@vitstudent.ac.in  / Student@12345
```

### 3. Start the frontend

One-time install, then dev server (every time):

```bash
npm install       # first time only
npm run dev
```

### 4. Open the app

<http://localhost:5173/>

> Use `localhost`, not `127.0.0.1` — Vite binds to `localhost` (IPv6 on some machines).

Sign in with a demo account above, or use **Create account** to register a student or
mentor. The frontend stores the JWT in `localStorage` and validates the session against
`/auth/me`.

### Everyday command cheat sheet

```bash
# start everything
docker compose up --build -d
npm run dev

# stop API + database (keeps data)
docker compose down

# stop and wipe the database (then re-run step 2)
docker compose down -v

# follow API logs
docker compose logs -f api

# backend tests
cd backend && . .venv/bin/activate && pytest

# production build check
npm run build
```

---

## Configuration

### Backend (`backend/.env`)

Docker Compose injects these automatically — you only need a `.env` for a local
(non-Docker) API run:

```bash
cd backend
cp .env.example .env
```

| Variable             | Default / example                                        | Purpose |
| -------------------- | -------------------------------------------------------- | ------- |
| `DATABASE_URL`       | `postgresql+psycopg://career_user:career_pass@localhost:5432/career_platform` | Postgres DSN |
| `JWT_SECRET_KEY`     | *(change it)*                                             | Signing key for access tokens |
| `ACCESS_TOKEN_MINUTES` | `60`                                                   | Token lifetime |
| `CORS_ORIGINS`       | `["http://localhost:5173", …]`                           | Allowed frontend origins |
| `AUTO_CREATE_TABLES` | `true`                                                   | Dev convenience: create schema on boot. Set `false` once Alembic owns the schema. |
| `SEED_REFERENCE_DATA`| `true`                                                   | Load role matrix / resources / questions on first boot |
| `AI_ENABLED`         | `false`                                                  | Must be `true` **and** `AI_API_KEY` set for real AI output |
| `AI_API_KEY` / `AI_MODEL` / `AI_BASE_URL` | —                          | OpenAI-compatible chat-completions settings |

### Frontend

| Variable        | Default                 | Purpose |
| --------------- | ----------------------- | ------- |
| `VITE_API_URL`  | `http://127.0.0.1:8000` | Backend base URL (optional — this default works out of the box) |

---

## Run without Docker

1. Start a local PostgreSQL and create the database:

   ```sql
   CREATE DATABASE career_platform;
   ```

2. Start the API:

   ```bash
   cd backend
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env          # adjust DATABASE_URL if needed
   python -m scripts.seed_demo   # demo accounts
   uvicorn app.main:app --reload
   ```

3. Frontend as usual: `npm run dev`.

---

## Backend API surface

All feature routes are mounted under `/api` (`/auth/*` and `/health` also exist at the
root for compatibility). Routers:

| Area            | Prefix                    | Highlights |
| --------------- | ------------------------- | ---------- |
| Auth            | `/auth` (+ root)          | register, login, me — JWT + bcrypt |
| Students        | `/students`               | profile, skills, projects, certifications |
| Resumes         | `/resumes`                | CRUD, submit for mentor review |
| Readiness       | `/readiness`              | PRS breakdown, skill gap, AI skill gap, history |
| Learning        | `/learning`               | path, refresh, item progress |
| Interview       | `/interview`              | questions, practice, mock interviews |
| Companies       | `/companies`              | admin-managed company directory |
| Jobs            | `/jobs`                   | postings, publish/close |
| Drives          | `/drives`                 | drives, eligibility, status lifecycle |
| Applications    | `/applications`           | apply, withdraw, mentor decision |
| Mentor          | `/mentor`                 | dashboard, students, reviews, feedback |
| Admin           | `/admin`                  | users, assignments, monitoring, audit log |
| Notifications   | `/notifications`          | list, unread count, mark read |

### Database migrations

Schema is auto-created on startup in development. Alembic is wired up
(`backend/alembic.ini`, `migrations/`) but currently contains **only one migration**
(`ai_skill_gap_results`). See “Remaining” below — do not run `alembic upgrade head`
against an auto-created database; the migration would collide with the existing table.

---

## Tests

```bash
cd backend
. .venv/bin/activate
pytest            # 18 tests: AI validation/failure handling, readiness weights
```

```bash
npm run build     # production build — verified passing
npm run lint      # currently FAILING (10 errors) — see “Remaining”
```

---

## What works today

- Registration + login for students and mentors; admin accounts via seed or admin API
- Full **student workspace**: dashboard, profile (skills/projects/certifications),
  readiness score + history, skill gap (+ optional AI analysis), learning path,
  interview practice questions and mock-interview logging, placement drives with eligibility,
  applications, notifications
- **Backend complete for mentor and admin** (13 admin endpoints, 9 mentor endpoints,
  plus companies/jobs/drives management) with typed clients `src/api/mentorApi.ts` and
  `src/api/adminApi.ts`
- Demo seed with realistic data; reference data auto-seeded on first boot
- 18 backend unit tests passing; production build passing

---

## Remaining to be implemented

Ordered by user impact. Everything below was verified against the running system.

### Frontend — missing pages

1. **Mentor workspace has zero pages.** `navConfig.ts` defines 5 mentor routes
   (dashboard, assigned students, resume reviews, application approvals, feedback) and
   `mentorApi.ts` is fully written, but `App.tsx` renders “Workspace unavailable” for
   mentor logins. Backend `/api/mentor/*` already works.
2. **Admin workspace has zero pages.** 9 admin routes defined (dashboard, users,
   students, mentor assignment, companies, jobs, drives, applications, audit log),
   `adminApi.ts` fully written, backend fully implemented — but no pages exist.
   Admin login currently shows “Workspace unavailable”.
3. **Student Resumes page missing.** The sidebar link `/student/resumes` has no route
   → clicking it shows “Page not found”. `resumeApi` CRUD (create/edit/submit/delete)
   is written but has no UI; only `resumeApi.list()` is used on the drives page, so
   students cannot create or submit a resume through the app.

   The backend resume pipeline is more complete than the UI suggests: `/api/resumes/me`
   returns a parsed resume with education, skills, experience, projects, certifications,
   achievements and links, and readiness reads those parsed skills to compute the skill
   gap and PRS. There is no resume **file upload / parsing** endpoint yet — `file_url` is
   a free-form string, so resumes are created by hand via the API, not uploaded as PDFs.
4. **Notifications page missing.** `/notifications` currently renders the student
   dashboard (and “unavailable” for other roles). The bell dropdown works, but there is
   no full-page notification list.
### Quality gates

5. **No frontend tests.** No test runner (vitest/jest) is configured.
6. **Thin backend coverage:** 18 unit tests cover only the AI service and readiness
   weights. No endpoint/integration tests for auth, drives, applications, mentor or
   admin (one `TestClient` test exists).
7. **No CI.** No `.github/` or equivalent pipeline.

### Backend / platform

8. **AI is a stub by default.** With `AI_ENABLED=false` (default) the API returns a
    canned `FakeAIProvider` response. Real AI covers **only** skill-gap analysis;
    learning paths and interview questions are static seeded data — no AI generation,
    no personalised question selection.
9. **No email delivery.** Notifications are in-app only; nothing sends email
    (invitations, password reset, drive alerts).
10. **No resume file upload.** `file_url` is a free-form string — no file storage, no
    PDF parsing, no upload endpoint.
11. **Auth hardening:** no refresh tokens (60-minute access token only), no
    self-service password reset, no email verification, no rate limiting on
    login/register.
12. **Alembic coverage incomplete:** 1 of 25 tables has a migration; the rest rely on
    the `AUTO_CREATE_TABLES` dev flag. A fresh database cannot be built from Alembic
    alone, and the existing migration collides with auto-created tables.
13. **No production deployment story:** `docker-compose.yml` is dev-only (hard-coded
    `JWT_SECRET_KEY`, debug CORS), there is no frontend service in Compose, no SPA
    production image, no reverse proxy/HTTPS config.

### Product gaps vs. a full placement platform

14. **Drive/application lifecycle is manual** — no automatic eligibility notifications
    when new drives open, no bulk application actions for admins.
15. **Mentor feedback has no realtime delivery** — students see it only when they
    happen to load notifications.
16. **SRS document is not in the repo** (`work_srs/` is gitignored), so requirement
    traceability cannot be checked from source alone.

---

## Recommended demo scenario (one integrated student journey)

This is the flow the reviewer should be able to run start to finish:

1. Login as `albin@vitstudent.ac.in` / `Student@12345`
2. Dashboard → profile is incomplete, target role is **Full-Stack Developer**
3. **Student Profile** → add skills (React already there, add TypeScript/Node.js), projects, certifications
4. **Skill Gap** (`/readiness/me/skill-gap`) → shows 4 of 10 required skills covered; missing TypeScript, Node.js, REST API, Git, Docker, Testing
5. **Learning Path** (`/learning/me/path`) → recommends REST API (MDN, 8h) and TypeScript (Microsoft Handbook, 12h) to close the gaps
6. **Readiness** (`/readiness/me`) → PRS 54/100, components: academics 15%, skills 30%, projects 20%, certs 10%, resume 10%, interview 15%
7. **Resume** (`/api/resumes/me`) → existing parsed resume already carries skills from step 3
8. **Placement Drives** → view open drives + eligibility
9. **Apply** → create an application against a drive
10. **Notifications** → bell + list, mark read
11. Then log in as mentor / admin and show those workspaces

Plus the reviewer-facing checks:
- RBAC boundaries: mentor cannot read `/students/1/profile` (403), student cannot hit
  `/api/admin/users` or `/api/mentor/dashboard` (403), admin can create companies/jobs/drives
- Auth: passwords hashed (bcrypt), JWT issued/validated, no raw DB errors leaked
- Docker clean start: `docker compose down -v && docker compose up --build -d` → Postgres
  healthy, API up, no manual DB repair; then host-side `python -m scripts.seed_demo` for
  demo accounts

---

## Project layout

```
.
├── docker-compose.yml        # postgres + api
├── index.html / vite.config.ts / package.json
├── src/                      # React frontend
│   ├── api/                  # typed API clients (auth, student, mentor, admin)
│   ├── components/           # layout, ui primitives, charts, student panels
│   ├── context/              # AuthContext, ToastContext
│   ├── pages/                # auth/, student/  (mentor/, admin/ not built yet)
│   ├── router/router.ts      # hash router
│   └── types/ hooks/ utils/
└── backend/
    ├── app/
    │   ├── api/              # 13 feature routers (see API surface)
    │   ├── models/           # 25 tables
    │   ├── schemas/          # Pydantic request/response models
    │   ├── services/         # readiness, learning, interview, AI, seed, audit…
    │   ├── config.py database.py security.py deps.py main.py
    ├── migrations/           # Alembic (partial — see Remaining #14)
    ├── scripts/seed_demo.py  # demo accounts + sample data
    ├── tests/                # pytest (18 tests)
    └── requirements.txt Dockerfile .env.example
```
