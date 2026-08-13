# Virtual Company OS

AI/ML multi-agent company environment with 24 named virtual employees.

## Included
- 24 named assistants/departments
- ML task routing (TF-IDF + Logistic Regression)
- Hindi/Hinglish-friendly commands
- Direct assistant addressing by name
- Task board and live activity feed
- Workspace File Library with file tree
- File version snapshots and change records
- Agent-to-agent file handoff
- Download individual file or full project ZIP
- Approval gate for external communication
- Render-ready deployment

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000


## AI / RAG / NLP
Set these Render environment variables:
- OPENAI_API_KEY = your API key
- OPENAI_MODEL = gpt-5-mini (or another supported Responses API model)

RAG works locally using TF-IDF even without an API key. `/api/rag/reindex` indexes readable files in the project workspace.
