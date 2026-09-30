# Changelog

## Unreleased

### Added

- Added `SOFTWARE_ARCHITECTURE.md` with a concise explanation of languages, stack, request flow, RAG, and deployment.
- Added superadmin role support with environment-based bootstrap credentials.
- Added admin-only text and PDF knowledge ingestion endpoints.
- Added ChromaDB `knowledge_chunks` collection for shared Finance Guru context.
- Added retrieval of relevant knowledge context during authenticated chat.
- Added a superadmin knowledge-base panel to the React application.
- Added this changelog.

### Changed

- Chat answers can now use centrally managed educational context instead of relying only on the base model.
- Auth responses now identify whether the signed-in user is a superadmin.

### Notes

- Knowledge ingestion is RAG, not model-weight training. This keeps updates fast and avoids retraining the model for every document.
- Existing document-QA endpoints and storage remain in place for future per-document features.
