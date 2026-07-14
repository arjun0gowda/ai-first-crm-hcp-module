# AI-First CRM — HCP Interaction Module

A full-stack assignment solution matching the supplied task/video: a field representative can log HCP interactions through a structured form or conversational assistant. The assistant uses **Groq + LangGraph**, executes five CRM tools, persists records, and populates the form after a chat-based log.

## Stack
- React + Vite + Redux Toolkit
- FastAPI + SQLAlchemy
- LangGraph StateGraph
- Groq LLM (`llama-3.3-70b-versatile` by default)
- SQLite locally; PostgreSQL through Docker
- Google Inter

## Five tools
1. Log Interaction
2. Edit Interaction
3. Search Interaction History
4. Schedule Follow-up
5. Recommend Next Best Action

## Why parsing is reliable
Every chat request uses a hybrid pipeline:
1. Deterministic extraction guarantees IDs, ISO dates, intent and common edit fields.
2. Groq JSON mode enriches the remaining structured fields and generates summaries.
3. The deterministic values take priority, so an LLM omission cannot remove a date or interaction ID already present in the message.

## Quick start (Windows)

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add a fresh private Groq key to `backend/.env`:
```env
GROQ_API_KEY=gsk_your_new_private_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Then run:
```bash
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and API docs at http://localhost:8000/docs.

## Demo commands

```text
Log a meeting with Dr. Vikram Shah today. We discussed diabetes treatment adherence and product benefits. He was positive. I shared a brochure and need to follow up next week.
```

```text
Show recent interaction history for Dr. Vikram Shah.
```

```text
Edit interaction 1. Change sentiment to neutral and add outcome: requested more clinical evidence.
```

```text
Schedule a follow-up for interaction 1 on 2026-07-21 to send clinical evidence.
```

```text
Recommend the next best action for Dr. Vikram Shah.
```

## Tests
```bash
cd backend
pytest -q
```

The tests cover all five tools, parser date extraction, edit extraction, and form-ready chat responses.

## Docker
Create `backend/.env`, then:
```bash
docker compose up --build
```

## Security
Never commit `.env` or an API key. A key shared in chat or screenshots must be revoked and replaced.
