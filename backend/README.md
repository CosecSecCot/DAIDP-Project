# MediQare backend

FastAPI, PostgreSQL, and LangGraph for testing patient-facing conversations and appointment workflows.

## Run with Docker Compose

1. Copy .env.example to .env and set OPENAI_API_KEY and a random ADMIN_API_KEY.
2. From this directory, run docker compose up --build.
3. Open http://localhost:8000/docs.

Compose starts the API and PostgreSQL. The API creates missing tables from its SQLAlchemy models at startup. In development it idempotently seeds demo doctors and future appointment slots; it does not seed booked appointments. PostgreSQL data and uploaded files use named volumes. Uploaded documents are extracted in FastAPI background tasks. The web app runs separately and can call the API. This setup creates tables for a fresh database; it does not update or clean up an existing schema.

## Prototype identity

The prototype does not create user accounts or associate saved records with a person. Appointments and uploaded documents are shared records.

## Conversation gateway

All chat goes through /api/v1/conversations. A security node rejects repeated, unrelated, or unclear requests. For a health concern, the agent gathers key details, gives conservative preliminary guidance, and suggests doctors when professional assessment may be useful. Users can then view appointment slots and book an offered slot. Doctor search and scheduling also work on direct request. Document questions are an optional side path and use uploaded records; uploaded documents are shared across the prototype.

Example request:

    POST /api/v1/conversations
    Content-Type: application/json

    {"message":"I have had a headache since this morning."}

Continue with POST /api/v1/conversations/{conversation_id}/messages; retrieve history with GET /api/v1/conversations/{conversation_id}. LangGraph keeps conversation state in process memory only. Conversations disappear when the API restarts and are not written to PostgreSQL.

For appointment booking, the agent presents current slots and requires a direct request such as “book slot 12”. It verifies that the slot was offered in the current in-memory conversation, locks the slot in PostgreSQL, and books it transactionally. GET /api/v1/appointments lists all bookings.

## Supporting APIs

- POST /api/v1/documents uploads a PDF or text file; GET /api/v1/documents lists all uploads. Questions about files go through conversation chat.
- GET /api/v1/doctors and GET /api/v1/slots search the directory and availability.
- POST /api/v1/admin/doctors and /api/v1/admin/slots create prototype directory and schedule entries; provide X-Admin-Key.

## Prototype limits

Urgency and care suggestions are model-generated preliminary information, not clinician-approved advice. Local Docker volume storage is for development only. Conversation state is transient in API process memory; appointments and uploaded documents are shared and have no user association. Review model-provider data flow, access controls, retention, and hosting before using patient records.
