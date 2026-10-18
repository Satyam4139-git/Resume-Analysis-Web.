# Deploying to Render (free)

The backend serves the website too, so ONE Render service is the whole site.

1. Put this folder on GitHub (`.env` is git-ignored - never upload it).
2. Render > New > Blueprint (or Web Service) > pick the repo. `render.yaml` is read automatically.
   Manual settings if you skip the Blueprint:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
   - Health check path: `/healthz`
3. Environment variables (Render > Environment):
   `OPENROUTER_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `GOOGLE_CLIENT_ID`,
   `GOOGLE_CLIENT_SECRET`, `SESSION_SECRET` (long random text; the Blueprint generates it).
   Do NOT set `PUBLIC_URL`, `FRONTEND_URL` or `GOOGLE_REDIRECT_URI` - they are taken from Render's own address.
4. Google Cloud Console > your OAuth client > Authorized redirect URIs: add
   `https://YOUR-NAME.onrender.com/auth/callback`
5. Open `https://YOUR-NAME.onrender.com` once. That link is what you give Jooble (main address only).

Notes
- Free Render sleeps after ~15 min idle; first load afterwards takes 30-60 s.
- Saved applications: set `DATABASE_URL` (a free Neon Postgres connection string) in Render > Environment so they
  survive restarts and redeploys. Without it the app falls back to a SQLite file, which the free plan wipes.
- There is a single `frontend/` folder; the backend serves it, so nothing else needs hosting.
- Run locally: copy `.env.example` to `.env`, then `uvicorn app.api.main:app --reload` and open http://127.0.0.1:8000

## Other hosts (Docker)
A `Dockerfile` is included, so any container host works (Google Cloud Run, SnapDeploy, Koyeb, ...).
Typical Cloud Run command: `gcloud run deploy ai-career-platform --source . --region asia-south1 --allow-unauthenticated`
then set the same environment variables, plus `PUBLIC_URL=https://<your-service-url>`
(only Render fills the public address automatically).

## Changing the colors
All brand colors live in `frontend/theme.css`. The website, the API docs page (`/docs`) and the error
pages all read that one file, so edit it there and everything updates together.

## Speed settings (optional, in .env / Render environment)
- `AI_PARSE_BUDGET_SECONDS` (default 8): longest the AI may take to polish the resume parse. The instant local parse is used if it is slower.
- `AI_REVIEW_BUDGET_SECONDS` (default 30): longest for the AI tips. Results appear first; the tips fill in afterwards.
- `AI_TIMEOUT_SECONDS`: per-request timeout for the AI provider.
After updating the site, press Ctrl+Shift+R once to clear the browser's cached copy of the old design.
