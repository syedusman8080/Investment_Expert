# Finance Guru software architecture

This file is a quick guide for a developer joining the project.

## 1. Language

- **Python** powers the backend. It exposes the API, authenticates users, stores data, processes PDFs, creates embeddings, searches the knowledge base, and calls the language model.
- **JavaScript with React** powers the frontend. It renders the login page, chat experience, conversation history, and the superadmin knowledge-base panel.
- **SQL** is used through SQLAlchemy. SQLite is the default local database; MySQL can be selected with `DATABASE_URL`.

## 2. Stack

| Layer | Technology | Purpose |
|---|---|---|
| Browser UI | React, Create React App | Login, chat, history, admin tools |
| API | FastAPI, Uvicorn | JSON endpoints and authentication |
| Relational data | SQLAlchemy with SQLite/MySQL | Users, roles, conversations, messages, knowledge-source records |
| Vector search | ChromaDB | Stores and searches knowledge embeddings |
| Embeddings | Sentence Transformers | Converts text into vectors for similarity search |
| Language model | Demo, hosted OpenAI-compatible API, or local llama.cpp | Produces the final explanation |
| Deployment | Render Static Site + Web Service | Hosts frontend and backend separately |

## 3. How a normal chat works

1. A user creates an account or signs in.
2. The frontend stores the returned access token in browser local storage and sends it as a Bearer token.
3. The user creates or selects a conversation.
4. The message is saved in the relational database.
5. If embeddings are configured, the backend searches the Finance Guru knowledge base for relevant chunks.
6. The backend places the retrieved context and question into a grounded prompt.
7. The selected LLM provider generates an answer.
8. The assistant answer is saved and returned to the frontend.
9. The frontend displays the answer and the conversation remains available in history.

## 4. How superadmin knowledge ingestion works

The superadmin does not retrain the model weights. The feature uses **RAG (Retrieval-Augmented Generation)**, which is cheaper, faster, and safer for changing financial education material.

1. A superadmin is bootstrapped from `SUPERADMIN_EMAIL` and `SUPERADMIN_PASSWORD`.
2. The admin uploads a PDF or pastes trusted text.
3. The backend extracts the text and splits it into overlapping chunks.
4. Sentence Transformers creates an embedding for each chunk.
5. ChromaDB stores the chunks and vectors in the `knowledge_chunks` collection.
6. When a user asks a question, the closest chunks are retrieved and included in the LLM prompt.

Adding new material therefore updates the searchable knowledge base immediately; it does not require an expensive model-training job.

## 5. Important backend locations

- `fastapi/app/main.py`: application creation, CORS, and database initialization.
- `fastapi/app/api/routes.py`: HTTP endpoints.
- `fastapi/app/auth.py`: password hashing, signed tokens, and role checks.
- `fastapi/app/db.py`: SQLAlchemy models and database session setup.
- `fastapi/app/services/knowledge_service.py`: admin text/PDF ingestion.
- `fastapi/app/vectorstore/chroma.py`: document and knowledge vector storage.
- `fastapi/app/llm/service.py`: local, hosted, and demo LLM providers.
- `fastapi/app/rag/prompt.py`: grounded prompt construction.

## 6. Important frontend locations

- `src/App.js`: authentication, chat, history, and admin panel composition.
- `src/services/api.js`: API requests and token attachment.
- `src/App.css`: application styling.

## 7. Configuration and deployment

Copy `fastapi/.env.example` to `fastapi/.env` locally. Keep `AUTH_SECRET`, database credentials, and LLM keys on the backend only. Never put them in `REACT_APP_*` variables.

For Render, deploy the backend as a Python Web Service and the frontend as a Static Site. Use an external MySQL-compatible database for durable data because Render free-service filesystems are ephemeral. Use `LLM_PROVIDER=demo` for a zero-cost product demonstration or configure a server-side hosted inference provider.
