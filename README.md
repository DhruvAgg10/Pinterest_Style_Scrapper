# Pinterest_Style_Scrapper

## Overview
This project implements a lightweight MVP for uploading outfit and tattoo images, analyzing them into style tags, and returning simple visual inspiration recommendations.

## Run locally
### Backend
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server.app.main:app --reload --port 8000
```

### Frontend
```bash
npm install
npm run dev
```

## Deployment
The project includes a Vercel configuration for deploying the FastAPI API and the static frontend.
