from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.agent import build_chain

STATIC_DIR = Path(__file__).resolve().parent / "static"

chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    chain = build_chain()
    yield


app = FastAPI(title="Fingerprint RAG Agent", lifespan=lifespan)


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
def ask(body: Question):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")
    result = chain.invoke(body.question)
    return Answer(answer=result)
