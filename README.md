# Conversation Agent

[![CI](https://github.com/hugoarias/conversational-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/hugoarias/conversational-agent/actions/workflows/ci.yml)

A fully offline, real-time conversational voice agent.Speak into your microphone — the agent transcribes your speech, generates a response with a local LLM, and speaks it back.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python, FastAPI, WebSockets |
| STT | faster-whisper (local, `base` model) |
| LLM | Ollama (`llama3`) |
| TTS | pyttsx3 / Windows SAPI5 |

## Quick Start

```bash
# Terminal 1 — Backend
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Requires [Ollama](https://ollama.ai) running with `llama3` pulled.

## Documentation

See [docs/setup.md](docs/setup.md) for full setup, configuration, and production build instructions.
