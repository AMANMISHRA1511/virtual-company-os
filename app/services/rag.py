
from pathlib import Path
import json, re, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path("workspace/projects/demo-company/current")
INDEX_FILE = Path("workspace/rag_index.json")

TEXT_EXTS={".txt",".md",".py",".js",".ts",".tsx",".jsx",".html",".css",".scss",".json",".csv",".sql",".yaml",".yml",".xml",".log"}

def _read(path:Path)->str:
    ext=path.suffix.lower()
    try:
        if ext in TEXT_EXTS:
            return path.read_text(encoding="utf-8",errors="ignore")
        if ext==".pdf":
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
        if ext==".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(str(path)).paragraphs)
    except Exception:
        return ""
    return ""

def _chunks(text:str, size:int=1800, overlap:int=250):
    text=re.sub(r"\s+"," ",text).strip()
    if not text:return []
    out=[];start=0
    while start<len(text):
        out.append(text[start:start+size])
        if start+size>=len(text):break
        start += max(1,size-overlap)
    return out

def build_index():
    docs=[]
    if ROOT.exists():
        for p in ROOT.rglob("*"):
            if p.is_file() and p.stat().st_size <= 8*1024*1024:
                txt=_read(p)
                for i,ch in enumerate(_chunks(txt)):
                    docs.append({"path":str(p.relative_to(ROOT)),"chunk":i,"text":ch})
    INDEX_FILE.parent.mkdir(parents=True,exist_ok=True)
    INDEX_FILE.write_text(json.dumps(docs,ensure_ascii=False),encoding="utf-8")
    return {"chunks":len(docs),"files":len(set(d["path"] for d in docs))}

def load_index():
    if not INDEX_FILE.exists(): build_index()
    try:return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:return []

def retrieve(query:str, top_k:int=6):
    docs=load_index()
    if not docs:return []
    texts=[d["text"] for d in docs]
    vec=TfidfVectorizer(ngram_range=(1,2),max_features=25000)
    mat=vec.fit_transform(texts+[query])
    scores=cosine_similarity(mat[-1],mat[:-1]).flatten()
    idx=scores.argsort()[::-1][:top_k]
    return [{**docs[i],"score":float(scores[i])} for i in idx if scores[i]>0]

def context_for(query:str, top_k:int=6):
    hits=retrieve(query,top_k)
    return "\n\n".join(f"[{h['path']}#{h['chunk']} score={h['score']:.3f}]\n{h['text']}" for h in hits),hits
