# RAG Agent Platform

## Context (load as needed)
| Need | File |
|------|------|
| Frontend | `frontend/CLAUDE.md` |
| Backend | `backend/CLAUDE.md` |
| API Routes | `.claude/api-routes.md` |
| Services | `.claude/services.md` |
| Testing | `.claude/testing.md` |
| Todos | `.docs/04-todos.md` |

## Stack
- **Frontend:** SvelteKit 2 + Svelte 5 (Runes) + Tailwind v4 + shadcn-svelte
- **Backend:** FastAPI + Python 3.12 + SQLAlchemy async + PostgreSQL
- **AI:** LiteLLM (Google Gemini) + pgvector

## Critical Patterns
- **Svelte 5:** `$state()`, `$derived()`, `$props()`, `{@render}`
- **Python:** Always type hints (`X | None` syntax)
- **API:** Wrap with `BaseResponse(trace_id=ctx.trace_id, data=...)`

## Task Tracking
Update `.docs/04-todos.md`: `[ ]` → `[x]`
