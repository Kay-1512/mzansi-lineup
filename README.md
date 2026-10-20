# Mzansi Lineup

A personalised music events calendar for South Africa. Users pick the genres,
artists and ticketing platforms they care about during onboarding; a
scheduled fetcher pulls every SA music event into one shared table, and each
user sees only the events that match their taste, with a reason why
("Because you follow Tyla").

**Status: Phase 2.** Phase 1 (auth, onboarding, the Ticketmaster fetcher,
per-user scoring, the calendar/list UI, save/hide, manual events, the
profile page and match-reason labels) is done. Phase 2 adds a Quicket
fetcher (verified against the real API docs), cross-source de-duplication
with a city-alias table for near-miss venue matching, the genre/source/
city/date filter bar with real list-view pagination, and a calendar view
that fetches its full matched set up front. Phase 3+ (LLM scoring, Spotify
import, Google sign-in, calendar export, Celery) is still ahead — see
"Roadmap".

## Architecture

- **Fetch once, filter per user.** A management command (`fetch_events`)
  pulls every SA music event from each active source into one shared
  `Event` table. The API never calls an external ticketing platform on a
  request — it only reads from Postgres.
- **One fetcher class per platform**, behind `BaseFetcher.fetch()` /
  `.normalise()` ([apps/events/fetchers/base.py](backend/apps/events/fetchers/base.py)).
  Ticketmaster and Quicket both implement it now; Howler is still a stub.
- **Scoring is computed per request, not stored.** A pluggable pipeline
  ([apps/events/scoring/](backend/apps/events/scoring)) scores a `(user,
  event)` pair: watched artist (100) > genre keyword match (50) =
  international act (50). Swap in an LLM classifier later without touching
  the other steps.
- **Genres are admin-managed.** Each `Genre` has hidden `GenreKeyword`s
  matched case-insensitively against an event's title/description/artists —
  source genre tags (when platforms even have them) aren't trusted.
- **Cross-source de-duplication has two tiers**
  ([apps/events/fetchers/dedupe.py](backend/apps/events/fetchers/dedupe.py)):
  an exact title+date+venue key, and a fallback that matches on title+date+
  city alone, so the same show listed on two platforms under slightly
  different venue strings (e.g. "Grand Arena" vs "GrandWest Grand Arena")
  still collapses into one `Event` with two `EventListing`s instead of a
  duplicate row.
- **City strings are normalised at ingestion, not filter time.** A
  `CityAlias` table (admin-managed, seeded with a starter set — Sandton,
  Centurion, Umhlanga, etc.) maps a venue's raw city string to one of the
  four canonical cities before an `Event` is ever saved, so the de-dup
  fallback above and the city filter both just compare canonical strings.

## Project layout

```
backend/    Django + DRF API (apps/accounts, apps/catalog, apps/events)
frontend/   React + Vite + FullCalendar
docker-compose.yml   local dev: Postgres + backend + frontend
render.yaml           Render Blueprint for the API (see "Deployment")
```

## Setup

### With Docker (recommended)

```bash
cp backend/.env.example backend/.env
# edit backend/.env and add your TICKETMASTER_API_KEY (see below)
docker compose up --build
```

- Backend: http://localhost:8000 (admin at `/admin/`, docs at `/api/docs/`)
- Frontend: http://localhost:5173

The backend container runs migrations on startup. Create an admin user once
it's up:

```bash
docker compose exec backend python manage.py createsuperuser
```

### Without Docker

Backend (needs Python 3.12 and a local Postgres, or just omit `DATABASE_URL`
to fall back to SQLite):

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # add TICKETMASTER_API_KEY; drop DATABASE_URL for SQLite
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Getting API keys

**Ticketmaster:**

1. Create a free account at https://developer.ticketmaster.com/
2. Create an "App" — you get a Consumer Key immediately (no approval wait).
3. Put it in `backend/.env` as `TICKETMASTER_API_KEY=...`.

**Quicket:**

1. Register at https://developer.quicket.co.za for an API key.
2. Put it in `backend/.env` as `QUICKET_API_KEY=...`.

The fetcher is verified against the real docs at https://docs.quicket.com
(base URL, query-string auth, `/events` params, response envelope and field
names all match) — the one open question is which `locality` level an
event's venue city actually is; see the comment in
`apps/core/quicket_client.py`.

Without keys, the app still runs: onboarding, auth, manual events, save/hide
all work — the artist-search autocomplete and the fetchers just return empty
results or a logged failure.

## Running the fetcher

Events don't appear by magic — run the management command (in Phase 1 this
is a manual/cron job; Phase 3 moves it to Celery beat):

```bash
python manage.py fetch_events            # all active sources
python manage.py fetch_events --source ticketmaster
python manage.py fetch_events --source quicket
```

In Docker: `docker compose exec backend python manage.py fetch_events`.

Set up a local cron entry to run it periodically, e.g. every 30 minutes:

```
*/30 * * * * cd /path/to/mzansi-lineup/backend && .venv/bin/python manage.py fetch_events >> fetch.log 2>&1
```

(In production, this is the GitHub Actions workflow under "Deployment"
instead of a local cron entry.)

Genres, keywords and the three `Source` rows (Ticketmaster and Quicket
active, Howler inactive until it has a fetcher) are seeded automatically by
a data migration — no fixtures to load by hand.

## API docs

Swagger UI: http://localhost:8000/api/docs/
Redoc: http://localhost:8000/api/redoc/
Raw schema: http://localhost:8000/api/schema/

## Sample cURL walkthrough

```bash
BASE=http://localhost:8000/api

# Register + log in
curl -s -X POST $BASE/auth/register/ -H 'Content-Type: application/json' \
  -d '{"email": "jo@example.com", "password": "correct-horse-1"}'

ACCESS=$(curl -s -X POST $BASE/auth/token/ -H 'Content-Type: application/json' \
  -d '{"username": "jo@example.com", "password": "correct-horse-1"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access"])')

AUTH="Authorization: Bearer $ACCESS"

# Onboarding
curl -s -X PUT $BASE/onboarding/sources/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"sources": ["ticketmaster"]}'

curl -s -X PUT $BASE/onboarding/genres/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"genres": ["amapiano", "jazz"], "international_acts": true}'

curl -s -X POST $BASE/artists/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name": "Tyla"}'

curl -s -X PATCH $BASE/profile/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"city": "cape_town", "onboarding_complete": true}'

# Your matched events
curl -s $BASE/events/ -H "$AUTH"

# Save / hide / manual events
curl -s -X POST $BASE/events/1/save/ -H "$AUTH"
curl -s -X POST $BASE/events/2/hide/ -H "$AUTH"
curl -s -X POST $BASE/manual-events/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"title": "Friend'"'"'s birthday set", "venue": "My house", "start": "2026-12-05T19:00:00Z"}'
```

## Deployment

Frontend on Vercel, API on Render, database on Neon, scheduled fetching via
GitHub Actions — all free-tier friendly.

### 1. Database — Neon

1. Create a project at https://neon.tech. Create a database (or use the
   default one).
2. Copy the connection string it gives you — it already looks like
   `postgres://user:pass@ep-xxx.aws.neon.tech/dbname?sslmode=require`.
   `django-environ` parses the `sslmode=require` query param automatically,
   so you don't need to configure SSL separately.

### 2. API — Render

This repo includes a [`render.yaml`](render.yaml) Blueprint.

1. In the Render dashboard: **New → Blueprint**, point it at this repo.
   Render finds `render.yaml` and creates a `mzansi-lineup-api` web service
   (`rootDir: backend`, `./build.sh` as the build command — installs deps,
   runs `collectstatic`, then `migrate` — and `gunicorn` as the start
   command).
2. `DJANGO_SECRET_KEY` is auto-generated by the blueprint. Fill in the rest
   by hand in the service's **Environment** tab:
   - `DATABASE_URL` — the Neon connection string from step 1
   - `DJANGO_ALLOWED_HOSTS` — your Render URL's host, e.g.
     `mzansi-lineup-api.onrender.com` (Render's own external hostname is
     also added automatically — see `config/settings/prod.py`)
   - `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` — your Vercel URL
     once you have it from step 3 (with `https://` for the latter), e.g.
     `https://mzansi-lineup.vercel.app`
   - `TICKETMASTER_API_KEY`
3. Deploy. `/healthz/` is the health check path Render polls.

Free-tier web services spin down after 15 minutes idle — the first request
after a quiet spell takes a few seconds to wake up.

### 3. Frontend — Vercel

1. Import this repo in Vercel. Set **Root Directory** to `frontend`
   (`frontend/vercel.json` handles the SPA rewrite so client-side routes
   like `/onboarding` don't 404 on refresh).
2. Add an environment variable: `VITE_API_BASE_URL` =
   `https://<your-render-service>.onrender.com/api`.
3. Deploy, then go back and set `CORS_ALLOWED_ORIGINS` /
   `CSRF_TRUSTED_ORIGINS` on Render to the URL Vercel gives you (step 2
   above) and redeploy the API.

### 4. Scheduled fetching — GitHub Actions

[`.github/workflows/fetch-events-cron.yml`](.github/workflows/fetch-events-cron.yml)
runs `manage.py fetch_events` directly against the Neon database every 30
minutes — no extra endpoint on the API needed. Add these as **repository
secrets** (Settings → Secrets and variables → Actions):

- `DJANGO_SECRET_KEY` — any value works here (no HTTP server runs in CI);
  reuse the one Render generated if you want one source of truth
- `DATABASE_URL` — the same Neon connection string
- `TICKETMASTER_API_KEY`

The workflow also has `workflow_dispatch`, so you can trigger a run by hand
from the Actions tab instead of waiting for the schedule. Note that GitHub's
`schedule` trigger is best-effort — on a busy queue a run can start a few
minutes late.

## Tests

```bash
cd backend
pytest                  # fetchers (mocked HTTP) + scoring logic + full API flow
pytest --cov=apps       # with coverage
```

## Filter bar

The "For you" tab has filter controls for genre, source (within your own
onboarding sources), city and date range, backed by query params on
`GET /api/events/` (`genre`, `source`, `city`, `date_from`, `date_to`,
`sort`, `page`/`page_size`). Two things worth knowing if you touch this:

- `city=` sent as an **empty string** explicitly means "any city" and
  overrides the profile's default city filter; an **absent** `city` param
  falls back to the profile default. The frontend always sends `city`
  (even empty) once the filter bar has rendered, specifically to hit the
  override case — see the comment in `CalendarPage.jsx`'s `loadForYou`.
- `source` only ever narrows *within* the sources you selected during
  onboarding (requesting one you didn't select returns zero results,
  rather than expanding beyond your selection).
- The list view paginates with a real "Load more" button, fetching
  `page`/`page_size` from the API as you go (`LIST_PAGE_SIZE = 20` in
  `CalendarPage.jsx`). The calendar view instead fetches one larger page
  up front (`CALENDAR_PAGE_SIZE = 500`), since it needs the whole matched
  set to render correctly as you navigate between months.

## Known limitations

- **Quicket's `locality` → city mapping is a best guess.** Everything else
  about the fetcher (base URL, auth, endpoint, params, field names) is
  verified against the real docs at https://docs.quicket.com, but an
  event's `locality` object has undocumented `levelOne`/`levelTwo`/
  `levelThree` fields. `levelThree` is used as the city (country > province
  > city is the most plausible reading) — fix it in
  `apps/core/quicket_client.py` / `apps/events/fetchers/quicket.py` if a
  real response shows otherwise.
- **"International act" detection is a manual flag.** Neither Ticketmaster
  nor Quicket expose attraction nationality, so `Event.is_international`
  defaults to `False` from both fetchers — correct it per-event in the
  admin until a better signal is wired up.
- **City matching relies on the `CityAlias` table being kept up to date.**
  It ships with a small starter set of well-known suburbs; a venue city
  with no matching alias is stored as-is and won't line up with the four
  canonical cities in filters or de-dup. Add aliases in the admin as real
  fetched data reveals gaps.
- **The calendar view's single large fetch (500 events) isn't true
  pagination** — a user matched to more than 500 upcoming events would
  silently miss some on the calendar (the list view has no such cap). Not
  a realistic volume yet, but worth revisiting before go-live.

## Roadmap

- **Rest of Phase 2** — confirm the Quicket `locality` mapping against a
  real response, a real cap/strategy for the calendar view's fetch size.
- **Phase 3** — LLM classifier scoring step, Spotify import, Google sign-in,
  .ics/Google Calendar export, Celery + Redis scheduling.
- **Phase 4** — Artist-announcement alerts, Howler fetcher (pending API
  access), production deployment.
