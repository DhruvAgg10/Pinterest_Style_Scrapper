# StylePilot — Project Status & Roadmap

> Living document. Updated on **every** change. Source of truth for what this project is,
> what is done, and what remains. Last updated: 2026-07-12.

---

## 1. Core Idea

**AI Fashion Pose & Style Finder** (brand: *StylePilot*).

Users upload photos of their **outfit, tattoos, accessories, and body/pose**. The app uses AI to
understand the *complete aesthetic* (not just colors), then returns:

1. A structured **style analysis** — aesthetic tags, colors, fit guidance.
2. **Matching inspiration images** (Pinterest official API + Pexels), found via a search phrase the
   vision model writes from your photo.
3. **Instagram captions** for any chosen reference image.

> The goal is **NOT** image generation. It is **AI-powered visual inspiration** —
> "Pinterest search powered by AI instead of keywords."

Legal stance: **never scrape Pinterest.** Only the official Pinterest v5 API + Pexels API are used,
to stay inside Pinterest Developer Guidelines and qualify for API access.

---

## 2. Architecture (target — the "strong base")

Everything ships as **one Vercel project**.

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + Vite, static build → `dist/` | Served by Vercel |
| Backend | FastAPI on a **Vercel Python serverless function** (`api/index.py`) | Fits the size limit now that torch is gone |
| AI | **Hugging Face Inference Providers** over HTTPS (`huggingface_hub`) | Free tier; no heavy ML deps in the bundle |
| Image sources | Pinterest v5 API (if token) → Pexels API | No scraping; guideline-compliant |

Models (remote, free tier):
- Image analysis: `google/gemma-3-27b-it` — a **vision-language model**. It reads the photo and returns
  `{aesthetic_tags, colors, search_query}` as JSON.
- Captions: same model, text-only.

**Key rule:** the serverless function must never import `torch`/`transformers`.
If `HF_TOKEN` is absent the app degrades to local heuristics + caption templates instead of failing.

### How we got here (two dead ends, recorded so we don't retry them)
1. **torch + CLIP on Vercel** — impossible. `torch` alone blows past Vercel's 250 MB function limit.
   This is why the app never actually deployed before.
2. **torch + CLIP on a free HF Space** — blocked. HF now requires a **PRO subscription ($9/mo)** to run
   Docker/Gradio Spaces on `cpu-basic` (`402 Payment Required`). Only Static Spaces are free.
3. **CLIP via HF Inference API** — not available. The `hf-inference` provider currently serves **zero**
   `zero-shot-image-classification` and **zero** `image-feature-extraction` models. Verified against the
   live API.

**Consequence:** there are no free CLIP image embeddings, so ranking candidates by *pixel-level visual
similarity* is not currently possible. Instead the VLM converts the photo into a precise semantic search
phrase (e.g. a linen-shirt photo → `"oversized linen shirt dress"`), which is what actually drives the
match. `match_mode` in the API response reports `keyword-semantic` to be honest about this.

---

## 3. Done

**The base (2026-07-12) — app is now genuinely deployable and every AI path is verified live.**

- [x] Project scaffold: FastAPI backend, React/Vite frontend, Vercel config.
- [x] Upload flow: 4 categories (upper / lower / accessories / tattoo), multipart to `/api/analyze`.
- [x] **Image analysis via VLM** (`gemma-3-27b-it`) → aesthetic tags, colors, semantic search query.
- [x] **Inspiration**: VLM search phrase → Pinterest v5 API → Pexels fallback.
- [x] **Instagram captions** (normal + trendy) from the same model.
- [x] Torch/transformers removed entirely — backend fits Vercel's Python function.
- [x] Pinterest: official v5 `GET /v5/pins`, largest image, real pin URLs. Never scrapes.
- [x] Graceful fallbacks: no HF token → heuristic tags + caption templates; no keys → empty results.
- [x] Removed the fake `recommendation.results` stub (`score: 0.92`).
- [x] Internal `_search_query` hint stripped from API responses.
- [x] Marketing/info pages + Privacy Policy page & public route.
- [x] Repo hygiene: untracked `dist/`+`*.pyc`, removed stray files. Added `.env.example`.
- [x] Tests: 11 passing (0.6s — no model loading). Frontend builds.
- [x] **Verified end-to-end**: real photo → VLM tags → `"oversized linen shirt dress"` → matching Pexels
      results → real model captions. `tag_source: vision-model`, `caption_source: text-generation-model`.

---

## 4. Current Sprint

- [ ] Deploy to Vercel with `HF_TOKEN` + `PEXELS_API_KEY` env vars; verify live.
- [ ] Push to GitHub.
- [ ] Pinterest Developer app (needs the live privacy-policy URL) → add `PINTEREST_ACCESS_TOKEN`.

---

## 5. Backlog (from Project Overview vision)

**Phase 1 completeness**
- [ ] Analyze *all* uploaded images, not just the first per category (currently capped at 1 per category
      to stay inside the serverless time budget — needs batching or a background job).
- [ ] Restore true **visual similarity** ranking. Blocked on free CLIP embeddings; options: a paid HF
      Space/endpoint, a self-hosted embedder, or a provider that serves image feature-extraction.
- [ ] Multi-factor analysis: tattoo *placement*, lighting, background, body areas.
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
| 1 | Pexels API key | Image source | ✅ provided |
| 2 | Hugging Face token | Vision model + captions | ✅ provided |
| 3 | Vercel account linked | Deploy target | ✅ linked |
| 4 | **Rotate the HF + Pexels keys** — both were pasted into chat | Hygiene; they're exposed | ⚠️ recommended |
| 5 | **Pinterest Developer app** (developers.pinterest.com) — create once the site is live, then hand over the access token | Enables the official Pinterest inspiration source. Requires a live privacy-policy URL, which the Vercel deploy provides at `/privacy-policy` | ⏳ pending (needs live URL) |

---

## 7. Changelog

- **2026-07-12** — Created this status doc. Diagnosed the real Vercel deploy blocker: `torch`/`transformers`
  exceed the serverless size limit, so the app had never actually deployed.
- **2026-07-12** — First attempt at a fix: split architecture (Docker HF Space backend + Vercel static
  frontend). Added `Dockerfile`, env-based `VITE_API_BASE`, fixed Pinterest to official v5 `/pins`, repo
  hygiene, rewrote README.
- **2026-07-12** — **Abandoned the Space plan**: HF now charges for Docker Spaces (`402 Payment Required`,
  PRO only). Also confirmed the free `hf-inference` provider serves no CLIP / image-embedding models at all.
- **2026-07-12** — **Rebuilt on the free path and shipped the base.** Replaced local CLIP+flan-t5 with
  remote calls to `google/gemma-3-27b-it` (vision-language) via HF Inference Providers. Dropped
  `torch`/`transformers`; backend now fits a Vercel Python function. Restored `api/index.py` + serverless
  `vercel.json` (60s budget). Removed the `Dockerfile`/Space artifacts and the fake `score: 0.92` stub.
  Capped analysis to one image per category for the time budget. Tests 7 → 11, runtime 45s → 0.6s.
  Verified live end-to-end: photo → tags → semantic query → matching images → captions.
