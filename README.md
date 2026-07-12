# StylePilot — AI Fashion Pose & Style Finder

Upload photos of your outfit, tattoos, and accessories. A vision-language model reads the look and
returns structured style tags and fit guidance, pulls matching inspiration images (Pinterest official
API + Pexels), and generates Instagram captions for any reference you pick.

See `PROJECT_STATUS.md` for the roadmap and current status.

## Architecture

Everything deploys to **Vercel** as one project:

- **Frontend** — React + Vite, built to `dist/` and served as static files.
- **Backend** — FastAPI on a Vercel Python serverless function (`api/index.py`).
- **AI** — **Hugging Face Inference Providers** over HTTPS. No `torch`/`transformers` in the bundle,
  so the function stays well under Vercel's size limit.
  - Image analysis: `google/gemma-3-27b-it` (vision-language model) → style tags, colors, search query.
  - Captions: the same model, text-only.
- **Images** — Pinterest official v5 API (if a token is set) → Pexels API fallback. Never scrapes.

If no HF token is configured, the app degrades gracefully to local heuristics and caption templates
rather than failing.

## Environment

Copy `.env.example` → `.env` (gitignored):

```
HF_TOKEN=hf_...            # Hugging Face token — powers image analysis + captions
PEXELS_API_KEY=...         # free image source
PINTEREST_ACCESS_TOKEN=... # optional, once the developer app is approved
```

The same variables must be set in **Vercel → Project → Settings → Environment Variables**.

## Run locally

```bash
# backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server.app.main:app --reload --port 8000

# frontend (separate terminal)
npm install
npm run dev     # proxies /api -> http://127.0.0.1:8000
```

## Deploy

Push to `main` — Vercel builds the frontend and the Python function automatically.
`vercel.json` sets the build, routes `/api/*` to the function, and gives it a 60s budget
(the vision model round-trip is the slow part).

## Inspiration sourcing (no scraping)

Pinterest's Developer Guidelines prohibit "using any automated means or form of scraping or data
extraction to access information from Pinterest, except as expressly permitted." This app **never**
scrapes pinterest.com:

1. With `PINTEREST_ACCESS_TOKEN` set, it reads the authenticated user's own Pins via the official
   **v5 API** (`GET /v5/pins`). The public API exposes no site-wide pin search, so first-party saved
   Pins serve as inspiration material.
2. Otherwise it uses the [Pexels API](https://www.pexels.com/api/) (free, no scraping) for
   lifestyle/outfit photography.

The vision model turns your upload into a targeted search phrase, so results are matched on the
semantics of the look rather than raw keywords.
