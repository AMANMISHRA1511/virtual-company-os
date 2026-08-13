
import os
from .rag import context_for
from .nlp import analyze

def status():
    return {
        "configured": bool(os.getenv("OPENAI_API_KEY")),
        "provider": "openai" if os.getenv("OPENAI_API_KEY") else "local-rag-fallback",
        "model": os.getenv("OPENAI_MODEL","gpt-5-mini"),
        "rag": True,
        "nlp": True,
    }

def respond(agent_name:str, role_title:str, message:str):
    nlp=analyze(message)
    context,hits=context_for(message,6)
    if not os.getenv("OPENAI_API_KEY"):
        if hits:
            short="\n".join(f"• {h['path']}: {h['text'][:260]}" for h in hits[:3])
            return {
                "text":f"{agent_name}: RAG se relevant project context mila:\n{short}\n\nLLM reasoning ke liye OPENAI_API_KEY configure karo.",
                "nlp":nlp,"sources":hits,"mode":"rag-only"
            }
        return {
            "text":f"{agent_name}: NLP ne intent '{nlp['intent']}' detect kiya. Project knowledge index me relevant context nahi mila. LLM ke liye OPENAI_API_KEY configure karo.",
            "nlp":nlp,"sources":[],"mode":"nlp-only"
        }
    try:
        from openai import OpenAI
        client=OpenAI()
        instructions=f"""You are {agent_name}, {role_title}, inside a virtual AI company.
Reply naturally in the user's language. Use retrieved project context when relevant.
Be role-specific and concise. Do not claim a file/computer action happened unless context or tool state proves it.
NLP metadata: {nlp}"""
        user=f"Retrieved project context:\n{context or '(none)'}\n\nUser request:\n{message}"
        r=client.responses.create(
            model=os.getenv("OPENAI_MODEL","gpt-5-mini"),
            instructions=instructions,
            input=user,
        )
        return {"text":r.output_text,"nlp":nlp,"sources":hits,"mode":"llm+rag"}
    except Exception as e:
        return {"text":f"{agent_name}: LLM error: {type(e).__name__}. Local RAG/NLP still available.","nlp":nlp,"sources":hits,"mode":"fallback-error"}
