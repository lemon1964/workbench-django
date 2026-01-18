# Workbench Notes — backend (Django + DRF)

Backend API for Workbench Notes: projects tree, entries drafts, snapshots/releases, images upload.

## 🔗 Links

- Backend (prod): https://workbench-django.onrender.com/
- Frontend (prod): https://workbench-next.onrender.com/

## ⚙️ Stack

- Django + Django REST Framework
- SQLite (demo)
- gunicorn (Render)

## ✨ What it provides

- Projects / Topics / Sections / Entries CRUD
- Project tree endpoint (for left sidebar navigation)
- Entry draft API (Delta / HTML / Text)
- Section snapshots/releases (version-like checkpoints)
- Image upload endpoint (used by editor)
- Search endpoint (project notes search)

## 🔌 Key endpoints (high level)

- `GET /api/projects/`
- `GET /api/projects/<id>/tree/`
- `POST /api/topics/` / `POST /api/sections/` / `POST /api/entries/`
- `GET /api/sections/<id>/entries/`
- `PATCH /api/entries/<id>/draft/`
- `POST /api/sections/<id>/snapshot/`
- `POST /api/sections/<id>/release/`
- `POST /api/images/upload/`
- `GET /api/search/`
