
import re
from .classifier import router

HINDI_HINTS=("karo","banao","bhejo","dikhao","check","test","file","mujhe","isko","kaise","kya","hai","karna")

def analyze(text:str):
    low=text.lower()
    lang="hinglish" if any(w in low.split() for w in HINDI_HINTS) else "english"
    intent=router.classify(text)
    urgency="high" if any(x in low for x in ["urgent","jaldi","asap","immediately","abhi"]) else "normal"
    entities={
        "files": re.findall(r'[\w.-]+\.(?:zip|pdf|docx?|xlsx?|csv|json|py|js|tsx?|jsx|sql|png|jpe?g|apk)',text,re.I),
        "people": [n for n in ["aarav","arjun","neha","meera","dev","vihaan","priya","riya","kabir"] if n in low],
    }
    return {"language":lang,"intent":intent,"urgency":urgency,"entities":entities}
