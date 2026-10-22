# Finance Guru

Beginner-friendly investment education chat with React and FastAPI. Accounts, conversations, and messages are persisted in a relational database. The original PDF/RAG pipeline remains available as a later knowledge-grounding feature.

## Run locally

1. Copy `fastapi/.env.example` to `fastapi/.env`. The default `LLM_PROVIDER=demo` works without a model and is useful for wiring the product end-to-end.
2. For MySQL, set `DATABASE_URL=mysql+pymysql://user:password@localhost/finance_guru` after creating the database. SQLite is the default for local experimentation.
3. Install backend dependencies in the existing environment:

   ```powershell
   cd fastapi
   pip install -r requirements.txt
   pip install -r requirements.in
   uvicorn app.main:app --reload
   ```

   If `llama-cpp-python` has no wheel for your Python version, install it in a
   supported local Python environment or build it with CUDA; the rest of the
   backend remains testable without it.

4. In another terminal:

   ```powershell
   npm start
   ```

The frontend is available at `http://localhost:3000` and talks to the local FastAPI server at `http://localhost:8000`.

## First administrator and knowledge uploads

When no administrator exists, the sign-in screen offers **Set up the first administrator**. This setup is available once; subsequent accounts use regular registration. You can also bootstrap an administrator with `SUPERADMIN_EMAIL` and `SUPERADMIN_PASSWORD`. Sign in as an administrator to add trusted text or upload PDFs in the knowledge panel. Documents are embedded for retrieval-augmented answers; this does not train or update the model weights.

## Response length

The old default limited generation to 512 tokens. The default `LLM_MAX_TOKENS` is now 4096; local Python llama-cpp generation uses the remaining context after the prompt, and the CLI runs until its context window is full. The context window (`LLM_CONTEXT_SIZE`, 4096 by default) is the practical local maximum, not an unlimited output size. Hosted providers may enforce their own output-token limits.

## LLM deployment modes

`LLM_PROVIDER=demo` returns a safe explanatory response without an inference model. `LLM_PROVIDER=hosted` calls any OpenAI-compatible endpoint using the server-only `LLM_API_KEY`, which is suitable for Render. `LLM_PROVIDER=local` keeps the existing llama.cpp flow for local development. Do not put an LLM key in a `REACT_APP_*` variable.

Render can host the React build as a Static Site and FastAPI as a Web Service. A local Windows model cannot be reached by Render unless the local machine exposes a secure, always-on public API; the simplest zero-cost deployment is demo mode or a free hosted inference quota. Render's free filesystem is ephemeral, so MySQL should be a managed/external database for durable production data.

## GPU fallback

Set `LLM_GPU_LAYERS=0` for CPU inference. Increase it gradually for CUDA-enabled `llama-cpp-python` builds on GPUs with limited VRAM; the entire model does not need to fit in VRAM.

## Tests

```powershell
cd fastapi
pytest
```

The LLM is lazy-loaded, so PDF, chunking, prompt, and RAG tests do not require loading the GGUF model. Embeddings and inference errors are returned explicitly by the API.
