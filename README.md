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
city/date filter bar with real list-view pagination, a calendar view
scoped to whatever date range is visible, a Spotify-backed artist search
(pick-from-cards, Spotify-onboarding style) for the watchlist, a show/hide
toggle on password fields, and multi-city support (a user's profile can
have several home cities, not just one). Phase 3+ (LLM scoring, full
"Connect Spotify" account import, Google sign-in, calendar export, Celery)
is still ahead — see "Roadmap".

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
- **The watchlist picker is cards, not a dropdown.** `GET /api/artists/search/`
  is backed by Spotify's artist search
  ([apps/core/spotify_client.py](backend/apps/core/spotify_client.py)), so
  each suggestion carries a photo — `ArtistCard.jsx` renders them as
  tap-to-follow cards (Spotify's own "follow some artists" onboarding
  step is the reference). `WatchedArtist.image_url` is copied from the
  search result at add-time, so already-followed artists render as cards
  without re-searching; a failed image load falls back to an initial
  letter rather than a broken-image icon. The whole search-and-tap
  interaction is `ArtistSearchPicker.jsx`, shared as-is between onboarding
  (`StepArtists.jsx`) and the Profile page — editing your watchlist later
  works exactly like following artists did the first time.

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

Unlike Ticketmaster and Spotify, Quicket's account approval isn't instant —
in practice it came back "Your account isn't active or hasn't been approved
yet" right after signup. Nothing to do but wait; the app runs fine without
it in the meantime (`fetch_events` just logs a skip for Quicket and keeps
going — see `apps/events/fetchers/quicket.py`).

The fetcher is verified against the real docs at https://docs.quicket.com
(base URL, query-string auth, `/events` params, response envelope and field
names all match) — the one open question is which `locality` level an
event's venue city actually is; see the comment in
`apps/core/quicket_client.py`.

**Spotify** (powers the artist watchlist's search — pick from cards with
photos, same idea as Spotify's own "follow some artists" onboarding step):

1. Create a free app at https://developer.spotify.com/dashboard.
2. Put its Client ID and Client Secret in `backend/.env` as
   `SPOTIFY_CLIENT_ID=...` / `SPOTIFY_CLIENT_SECRET=...`.

This uses the [Client Credentials
flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)
— public catalog search only, no Spotify user login involved, and nothing
is written back to Spotify.

Without keys, the app still runs: onboarding, auth, manual events, save/hide
all work — the artist-search autocomplete and the fetchers just return empty
results or a logged failure.

**Instagram** (watch specific pages — e.g. a promoter who announces lineups
on Instagram before, or instead of, any ticketing platform):

Instagram's own API only grants access to accounts that connect themselves
to your app, which a promoter's page never would — there's no key to get
here. Instead:

1. Pick a page-to-RSS proxy — e.g. [rss.app](https://rss.app) or
   [Bazaar](https://bazaar.app) — and generate an RSS feed URL for the
   Instagram page you want to watch. This usually needs a paid plan on the
   proxy's side; that's between you and them, not something this app needs
   credentials for.
2. `POST /api/instagram-pages/` with `{"handle": "...", "feed_url": "..."}`
   (see the cURL walkthrough below). `fetch_instagram_posts` (next section)
   picks it up from there.

## Running the fetcher

Events don't appear by magic — run the management command (in Phase 1 this
is a manual/cron job; Phase 3 moves it to Celery beat):

```bash
python manage.py fetch_events            # all active sources
python manage.py fetch_events --source ticketmaster
python manage.py fetch_events --source quicket
python manage.py fetch_instagram_posts   # every distinct watched Instagram feed
```

In Docker: `docker compose exec backend python manage.py fetch_events`.

Set up a local cron entry to run it periodically, e.g. every 30 minutes:

```
*/30 * * * * cd /path/to/mzansi-lineup/backend && .venv/bin/python manage.py fetch_events >> fetch.log 2>&1
*/30 * * * * cd /path/to/mzansi-lineup/backend && .venv/bin/python manage.py fetch_instagram_posts >> fetch.log 2>&1
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

# Watch an Instagram page (feed_url from rss.app/Bazaar/etc — see "Getting API keys")
curl -s -X POST $BASE/instagram-pages/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"handle": "milkandcookies", "feed_url": "https://rss.app/feeds/xxxxx.xml"}'

# Posts from pages you watch, newest first
curl -s $BASE/instagram-posts/ -H "$AUTH"

curl -s -X PATCH $BASE/profile/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"cities": ["Cape Town", "Durban"], "onboarding_complete": true}'

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
   default one). Pick **Postgres database** only — none of Neon's other
   add-ons (object storage, functions, AI gateway, Better Auth) are used
   here.
2. **Region**: neither Neon nor Render has an Africa region; of what they
   offer, Europe (Frankfurt) has the best-connected path to South Africa.
   Pick it for Neon now, and pick it again for Render in step 2 — put the
   backend in the *same* region as the database. DB↔backend latency (every
   request round-trips to Postgres, often more than once) matters far more
   than frontend↔backend, so this isn't a minor detail.
3. Copy the connection string it gives you — it already looks like
   `postgres://user:pass@ep-xxx.aws.neon.tech/dbname?sslmode=require`.
   `django-environ` parses the `sslmode=require` (and Neon's
   `channel_binding=require`, if present) query params automatically, so
   you don't need to configure SSL separately.

### 2. API — Render

This repo includes a [`render.yaml`](render.yaml) Blueprint.

1. In the Render dashboard: **New → Blueprint**, point it at this repo. If
   the repo doesn't show up in the search, Render's GitHub App usually only
   has access to a subset of your repos — fix it at
   [github.com/settings/installations](https://github.com/settings/installations)
   → Render → Configure → add the repo (or switch to "All repositories").
2. Render finds `render.yaml` and creates a `mzansi-lineup-api` web service
   (`rootDir: backend`, `./build.sh` as the build command — installs deps,
   runs `collectstatic`, then `migrate` — and `gunicorn` as the start
   command) in `region: frankfurt`, matching Neon. If you already have an
   existing service that was created before this field existed, it's
   likely in Render's default region (Oregon) instead — check its Settings
   tab for a region change, and if that's not offered, delete and
   recreate it via Blueprint to pick up the correct region.
3. `DJANGO_SECRET_KEY` is auto-generated by the blueprint. If you leave any
   of the rest blank at this step, Render may skip creating that key
   entirely rather than creating it empty — if so, add it later from the
   **Environment** tab's "Add Environment Variable" rather than looking
   for an existing (but missing) row to edit:
   - `DATABASE_URL` — the Neon connection string from step 1
   - `DJANGO_ALLOWED_HOSTS` — your Render URL's host, e.g.
     `mzansi-lineup-api.onrender.com` (Render's own external hostname is
     also added automatically — see `config/settings/prod.py`). You won't
     know the exact hostname until the first deploy; `*` works as a
     temporary bootstrap value, tighten it once you know the real one.
   - `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` — your Vercel URL
     once you have it from step 3 (with `https://` for the latter), e.g.
     `https://mzansi-lineup.vercel.app`
   - `TICKETMASTER_API_KEY`, `QUICKET_API_KEY`, `SPOTIFY_CLIENT_ID`,
     `SPOTIFY_CLIENT_SECRET` — see "Getting API keys" above. The app runs
     fine with any of these unset; those features just degrade to empty
     results.
4. Deploy. `/healthz/` is the health check path Render polls.

Two things worth knowing about what you'll see once it's live:

- **Free-tier web services spin down after 15 minutes idle** — the first
  request after a quiet spell takes a few seconds to wake up. Not fixable
  without a paid plan; nothing to do here.
- **Every DB-touching endpoint was taking 3-5 seconds even when warm** the
  first time this got deployed — not a cold start (DB-free endpoints like
  `/healthz/` stayed under 1s), and not just the first request after idle
  either. Two separate causes, found live by process of elimination:
  1. Django opens a brand-new connection (full TCP+TLS+auth handshake
     against Neon) on *every single request* by default (`CONN_MAX_AGE=0`).
     Fixed in `config/settings/base.py` with `CONN_MAX_AGE=60` +
     `CONN_HEALTH_CHECKS=True` — this only shaved ~1s off the *first*
     request in a burst, not the real problem.
  2. **The actual dominant cost**: `render.yaml` had no `region` set, so
     the service defaulted to Oregon against a Frankfurt database. A
     single request like `GET /api/events/` makes ~8-10 sequential DB
     round trips (scoring context + event query + listings prefetch +
     hidden/saved lookups), each paying the full US↔EU network latency —
     that's what produced the flat ~3.4s plateau that *didn't* improve
     after the connection-reuse fix. Fixed by adding `region: frankfurt`
     to `render.yaml` (see step 2 above).

  If you ever see "DB endpoints consistently slow, non-DB endpoints fine"
  again: check `CONN_MAX_AGE` first, but if the numbers don't move much,
  it's very likely a region mismatch, not connection overhead — confirm
  Render's service region matches Neon's.

### 3. Frontend — Vercel

1. Import this repo in Vercel. It may offer an "Import multi-service
   project" flow with a suggested root-level `vercel.json` — that's Vercel
   auto-detecting the `backend/` folder and offering to also host Django
   *on Vercel* via its internal service-bindings mechanism. Don't use it;
   Django lives on Render, not Vercel, and the frontend already talks to
   it over a plain HTTPS API call, not a Vercel service binding. Instead,
   set **Root Directory** to `frontend` directly — this clears the
   multi-service prompt and picks up `frontend/vercel.json` (which handles
   the SPA rewrite so client-side routes like `/onboarding` don't 404 on
   refresh).
2. Add an environment variable: `VITE_API_BASE_URL` =
   `https://<your-render-service>.onrender.com/api`.
3. Deploy, then go back and set `CORS_ALLOWED_ORIGINS` /
   `CSRF_TRUSTED_ORIGINS` on Render to the URL Vercel gives you (step 2
   above) and redeploy the API.

### 4. Scheduled fetching — GitHub Actions

[`.github/workflows/fetch-events-cron.yml`](.github/workflows/fetch-events-cron.yml)
runs `manage.py fetch_events` and `manage.py fetch_instagram_posts` directly
against the Neon database every 30 minutes — no extra endpoint on the API
needed. Add these as **repository secrets** (Settings → Secrets and
variables → Actions):

- `DJANGO_SECRET_KEY` — any value works here (no HTTP server runs in CI);
  reuse the one Render generated if you want one source of truth
- `DATABASE_URL` — the same Neon connection string
- `TICKETMASTER_API_KEY`
- `QUICKET_API_KEY` — once your Quicket account is approved (it isn't
  instant — see "Getting API keys" above)

`fetch_instagram_posts` needs no secret of its own — every feed URL it
polls comes from the `WatchedInstagramPage` rows already in the database
(added via `POST /api/instagram-pages/`), not from an API key.

Spotify is **not** needed here — it's only used by the live artist-search
endpoint (Render), never by this cron job.

Each of these needs two things, not just one: the secret itself (Settings →
Secrets and variables → Actions) *and* a matching line in the workflow's
`env:` block (`KEY: ${{ secrets.KEY }}`) — adding only the secret without
wiring it into the workflow file silently does nothing (the command just
logs "KEY is not configured" and moves on, which looks like a real failure
but isn't one).

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
onboarding sources), city/cities and date range, backed by query params on
`GET /api/events/` (`genre`, `source`, `city`, `date_from`, `date_to`,
`sort`, `page`/`page_size`). Several things worth knowing if you touch this:

- `UserProfile.cities` is a list now (a user can live in — or just care
  about — more than one city), stored as canonical display names
  (`"Cape Town"`, not a slug) so it compares directly against `Event.city`
  with no translation step.
- `city` on `GET /api/events/` is comma-separated (`?city=Durban,Pretoria`)
  and always means "exactly these cities, overriding the profile
  default" — including `city=` (empty), which means "any city". An
  **absent** `city` param is the only way to get the profile's default
  cities applied.
- The frontend has to actively distinguish "the user hasn't touched the
  city filter" from "the user explicitly chose every city" to make that
  override rule work — `FilterBar`'s `filters.city` is `null` for
  "untouched" (so `CalendarPage.jsx`'s `buildForYouParams` omits the
  param and the profile default applies) vs. a string (possibly `""`) once
  the user interacts with the `CityMultiSelect` dropdown. Collapsing this
  to always-send-a-string (what an earlier single-city version did) is
  the bug that shipped before: the profile's city default silently never
  applied to the main feed, because the filter bar always overrode it to
  "any city" on first render.
- `source` only ever narrows *within* the sources you selected during
  onboarding (requesting one you didn't select returns zero results,
  rather than expanding beyond your selection).
- The list view paginates with a real "Load more" button, fetching
  `page`/`page_size` from the API as you go (`LIST_PAGE_SIZE = 20` in
  `CalendarPage.jsx`). The calendar view instead scopes its fetch to
  whatever date range is currently visible in the grid, re-fetching as you
  navigate between months/weeks/days (`CalendarView`'s `datesSet` →
  `CalendarPage`'s `handleRangeChange`) — no cap on total matches, just a
  generous `CALENDAR_PAGE_SIZE = 500` per-page ceiling for one visible
  grid's worth of events. An explicit date filter in the filter bar wins
  over the visible-range scoping when both are present.
  - One subtlety this surfaced: re-fetching must **never** flip the
    page's "first load" spinner back on, or it unmounts `<CalendarView>`
    and FullCalendar loses its own navigation state (every month
    navigation would instantly snap back to the current month once new
    data arrived). `initialLoading` in `CalendarPage.jsx` only ever gates
    the very first paint for exactly this reason.

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
- **The calendar's per-grid fetch (500 events) is a sanity ceiling, not a
  real limit** — a user matched to more than 500 events within one visible
  month/week/day grid would silently miss some. Not a realistic volume.
- **Instagram posts are raw, not parsed into events.** `InstagramPost`
  stores the caption/link/image as-is — nothing extracts a date, venue or
  lineup from the caption text, and posts never feed into `Event` or the
  scoring pipeline. It's a "this page just posted something" feed for a
  human to read, not an announcement-to-event pipeline (that's the Phase 4
  "Artist-announcement alerts" item below). It also depends on a
  third-party Instagram-to-RSS proxy (rss.app, Bazaar, ...) staying up and
  the page you're watching staying public — nothing here talks to Instagram
  directly.

## Roadmap

- **Rest of Phase 2** — confirm the Quicket `locality` mapping against a
  real response.
- **Phase 3** — LLM classifier scoring step, "Connect Spotify" (OAuth user
  login to import their top artists automatically, vs. today's search-only
  Client Credentials use), Google sign-in, .ics/Google Calendar export,
  Celery + Redis scheduling.
- **Phase 4** — Artist-announcement alerts, Howler fetcher (pending API
  access), production deployment.
