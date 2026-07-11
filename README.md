---
title: StylePilot Backend
emoji: 👗
colorFrom: pink
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# StylePilot — AI Fashion Pose & Style Finder

Upload photos of your outfit, tattoos, and accessories. The app classifies the aesthetic with
CLIP zero-shot tagging, ranks visually similar inspiration images (Pinterest official API + Pexels)
by real image similarity to your upload, and generates Instagram captions for any reference you pick.

> The frontmatter block above is read by **Hugging Face Spaces** (Docker SDK) — it is ignored by the
> app itself. See `PROJECT_STATUS.md` for the full roadmap and current status.

## Architecture

- **Frontend** — React + Vite, deployed as a static site on **Vercel**.
- **Backend** — FastAPI + PyTorch + CLIP, deployed as a **Docker Hugging Face Space** (`Dockerfile`).
  Kept off Vercel because `torch`/`transformers` exceed Vercel's serverless size limit.
- The frontend calls the backend via `VITE_API_BASE` (absolute Space URL in production; empty in dev,
  where Vite proxies `/api` to the local server).

## Run locally

### Backend
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server.app.main:app --reload --port 8000
```

Create a `.env` in the project root (gitignored) — see `.env.example`:
```
PEXELS_API_KEY=your-pexels-key
PINTEREST_ACCESS_TOKEN=your-pinterest-token   # optional, once the developer app is approved
CLIP_MODEL=openai/clip-vit-base-patch32       # optional override
CAPTION_MODEL=google/flan-t5-base             # optional override
```

### Frontend
```bash
npm install
npm run dev   # proxies /api -> http://127.0.0.1:8000
```

## Deployment

### Backend → Hugging Face Space (Docker)
1. Create a **Docker** Space at huggingface.co (any name).
2. Add it as a git remote and push this repo — HF builds from the root `Dockerfile` and serves on port 7860.
3. In the Space **Settings → Variables and secrets**, add `PEXELS_API_KEY` (and `PINTEREST_ACCESS_TOKEN` once approved).
4. Note the public URL, e.g. `https://<user>-<space>.hf.space`.

### Frontend → Vercel (static)
1. Import this repo in Vercel. Build command `npm run build`, output `dist` (already in `vercel.json`).
2. Set env var **`VITE_API_BASE`** = the Space URL from above.
3. Deploy. The static site calls the Space for all `/api/*` requests.

## Inspiration sourcing (Pexels + official Pinterest API — no scraping)

Pinterest's Developer Guidelines prohibit "using any automated means or form of scraping or data
extraction to access information from Pinterest, except as expressly permitted." This app **never**
scrapes pinterest.com. Instead:

1. If `PINTEREST_ACCESS_TOKEN` is set, it reads the authenticated user's own Pins via Pinterest's
   official **v5 API** (`GET /v5/pins`). The public API has no site-wide pin search, so first-party
   saved Pins are used as inspiration material.
2. Otherwise it uses the [Pexels API](https://www.pexels.com/api/) (free, no scraping) for
   lifestyle/outfit photography.

Every candidate image is run through a single CLIP forward pass that both classifies it
("a lifestyle photo of a person wearing a fashion outfit" vs. "a product photo of a single clothing
item on a plain background") to filter out flat-lay/product shots, and produces the embedding used to
rank the remainder by visual similarity to the uploaded photo.
