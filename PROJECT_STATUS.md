# StylePilot — Project Status & Roadmap

> Living document. Updated on **every** change. Source of truth for what this project is,
> what is done, and what remains. Last updated: 2026-07-12.

---

## 1. Core Idea

**AI Fashion Pose & Style Finder** (brand: *StylePilot*).

Users upload photos of their **outfit, tattoos, accessories, and body/pose**. The app uses AI to
understand the *complete aesthetic* (not just colors), then returns:

1. A structured **style analysis** — aesthetic tags, colors, fit guidance.
2. **Visually similar inspiration images** ranked by real image similarity (Pinterest official API + Pexels).
3. **Instagram captions** for any chosen reference image.

> The goal is **NOT** image generation. It is **AI-powered visual inspiration** —
> "Pinterest search powered by AI instead of keywords."

Legal stance: **never scrape Pinterest.** Only the official Pinterest v5 API + Pexels API are used,
to stay inside Pinterest Developer Guidelines and qualify for API access.

---

## 2. Architecture (target — the "strong base")

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + Vite (static build) | Deploys as static on Vercel |
| Backend | FastAPI (serverless on Vercel) | `api/index.py` entry |
| AI backend | **FastAPI + PyTorch + CLIP** on a **Docker Hugging Face Space** | Real image embeddings for visual similarity; `torch`/`transformers` won't fit in Vercel's 250 MB serverless limit |
| Frontend | React + Vite static site on **Vercel** | Calls the Space via `VITE_API_BASE` |
| Image sources | Pinterest v5 API (primary) → Pexels API (fallback) | No scraping; guideline-compliant |

**Decision (2026-07-12):** AI runs on a free HF Space, not on Vercel. Vercel serverless can't hold
`torch`+CLIP, and HF's new Inference Providers router has poor support for CLIP image embeddings —
which are the core of the visual-similarity engine. Keeping a real FastAPI+torch backend on a Space
preserves that feature. Frontend stays static on Vercel and proxies to the Space.

Models (run locally inside the Space, free):
- Style tags + image embeddings: `openai/clip-vit-base-patch32` (zero-shot + feature extraction)
- Captions: `google/flan-t5-base` (text2text)

---

## 3. Done

- [x] Project scaffold: FastAPI backend, React/Vite frontend, Vercel config.
- [x] Upload flow: 4 categories (upper / lower / accessories / tattoo), multipart to `/api/analyze`.
- [x] CLIP zero-shot aesthetic tagging + image embedding (currently local torch — being moved to HF API).
- [x] Inspiration ranking: fetch candidates → lifestyle-vs-product filter → cosine-similarity rank vs upload.
- [x] Instagram caption generation (normal + trendy variants).
- [x] Pexels API integration (key provided).
- [x] Graceful fallbacks: no model → heuristic tags; no caption model → templates; no key → empty.
- [x] Marketing/info pages (About, Company, Testing, FitCheck, Contact) + Privacy Policy page & public route.
- [x] Backend tests: analysis + caption payload structure.

---

## 4. In Progress / Current Sprint — "Strong Base"

Goal: make the app **actually deployable** (real backend that runs) + be **Pinterest-approval-ready**.

- [x] **Split architecture**: FastAPI+CLIP backend → Docker HF Space; static frontend → Vercel.
- [x] Frontend calls backend via `VITE_API_BASE` (absolute Space URL in prod, Vite proxy in dev).
- [x] `Dockerfile` + `.dockerignore` for the HF Space (non-root UID 1000, port 7860, writable model cache).
- [x] `vercel.json` reduced to static build + SPA rewrite (dropped the Python function).
- [x] Fix Pinterest integration: read authed user's Pins via `GET /v5/pins`, largest image, real pin URLs.
- [x] Pinterest guideline compliance documented (README no-scraping statement + first-party Pins use-case).
- [x] Repo hygiene: untracked `dist/` + `*.pyc`, removed `tmp_test_image.png` and redundant `api/index.py`.
- [x] Added `.env.example`.
- [x] Verified: 7 backend tests pass, `npm run build` succeeds.
- [ ] **Deploy**: create the HF Space + set Vercel `VITE_API_BASE` (needs your HF account — see §6).
- [ ] Commit the base (this change set).

---

## 5. Backlog (from Project Overview vision)

**Phase 1 completeness**
- [ ] Replace hardcoded `recommendation.results` stub (`score: 0.92`) with real data.
- [ ] Multi-factor analysis: tattoo *placement*, lighting, background, body areas (spec wanted more than CLIP tags).
- [ ] Pose analysis (OpenCV / pose model) — a core spec item, not yet started.
- [ ] TailwindCSS (spec) vs current hand-written CSS — decide & align.

**Phase 2**
- [ ] Auth (Firebase) + user accounts.
- [ ] Saved collections / moodboards.
- [ ] Filters (gym / casual / streetwear).
- [ ] Persistence: database (MongoDB) + vector store (FAISS / Chroma) for a local image DB and cached embeddings.
- [ ] Cloud storage for uploads (Cloudinary).

**Phase 3**
- [ ] AI virtual try-on, personalized stylist, outfit combinations, automatic aesthetic scoring.

---

## 6. Needed From You (action items)

| # | Item | Why | Status |
|---|------|-----|--------|
| 1 | **Hugging Face account** → create a **Docker Space**, push this repo to it, add `PEXELS_API_KEY` secret | Hosts the FastAPI+CLIP backend for free | ⏳ pending |
| 2 | Give me the **Space URL** (e.g. `https://<user>-<space>.hf.space`) | To set as Vercel `VITE_API_BASE` | ⏳ pending |
| 3 | **Vercel**: import repo, set env `VITE_API_BASE` = Space URL, deploy | Hosts the frontend | ⏳ pending |
| 4 | **Pinterest Developer app** (developers.pinterest.com) — create app once the site is live, get access token | Enables the official Pinterest inspiration source (needs a live privacy-policy URL, which Vercel gives us) | ⏳ pending (needs live URL first) |
| 5 | Pexels API key | Fallback image source | ✅ provided |

---

## 7. Changelog

- **2026-07-12** — Created this status doc. Diagnosed Vercel deploy blocker (torch/transformers exceed
  serverless size limit).
- **2026-07-12** — Built the strong base: split architecture (Docker HF Space backend + Vercel static
  frontend). Added `Dockerfile`, `.dockerignore`, `.env.example`; env-based `VITE_API_BASE`; static-only
  `vercel.json`; fixed Pinterest to official v5 `/pins`; repo hygiene (untracked `dist/`+`*.pyc`, removed
  stray files + redundant `api/index.py`); rewrote README with architecture + deploy steps. All tests
  pass, frontend builds. Remaining: create the Space + wire Vercel env (needs HF account).
