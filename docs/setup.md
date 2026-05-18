# Setup Guide

## Prerequisites

### Backend
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
  ```bash
  ollama serve
  ollama pull llama3
  ```

### Frontend
- Node.js 18+

---

## Installation

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

---

## Running (Development)

Open two terminals:

**Terminal 1 — Backend**
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Tests

```bash
cd backend
.venv\Scripts\activate
pytest tests/ -v
```

---

## Configuration

Backend settings can be overridden via environment variables or a `backend/.env` file:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `TTS_RATE` | `180` | Speech rate (words/min) |

---

## Production Build

```bash
cd frontend
npm run build
```

The compiled assets will be in `frontend/dist/`. To serve them from FastAPI, mount the dist folder:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```
