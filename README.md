# MediQare

MediQare is a prototype health assistant for discussing health concerns, understanding uploaded documents, finding doctors, and booking appointments.

## Architecture

- **Frontend:** Next.js app in `mediqare-frontend/`. It provides chat, document selection and upload, and appointment views.
- **API:** FastAPI app in `backend/app/`. It serves chat, document, and scheduling endpoints.
- **Agent:** A LangGraph flow routes each message through security, then to intake, document help, doctor search, scheduling, or general help.
- **Data:** PostgreSQL stores doctors, appointment slots, bookings, and document records. Uploaded files use a separate storage volume. LangGraph uses an in-memory checkpointer for conversation state; that state is cleared when the API restarts.

The frontend sends each message to the API. The API restores the conversation state, loads relevant database context, runs the agent, then returns the reply and any doctor or appointment options.

## Run locally

Start PostgreSQL and the API with Docker Compose from `backend/`:

```bash
cp .env.example .env
docker compose up --build
```

Set `OPENAI_API_KEY` in `backend/.env`. Start the frontend separately from `mediqare-frontend/` with `npm run dev`. The API docs are available at `http://localhost:8000/docs`.
