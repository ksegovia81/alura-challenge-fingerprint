"""
RAG chain: recupera contexto de ChromaDB y responde con Claude Sonnet 4.6.
"""
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
# Use cached HuggingFace model without network calls (model already downloaded via ingest)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import httpx
import anthropic as _anthropic_module

# Patch Anthropic() to always use httpx with verify=False (Windows SSL workaround)
_orig_anthropic_init = _anthropic_module.Anthropic.__init__
def _no_verify_anthropic_init(self, *args, **kwargs):
    kwargs.setdefault("http_client", httpx.Client(verify=False))
    _orig_anthropic_init(self, *args, **kwargs)
_anthropic_module.Anthropic.__init__ = _no_verify_anthropic_init

from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
COLLECTION = "fingerprint"

PROMPT = ChatPromptTemplate.from_template(
    """Eres un asistente experto en serigrafía de la empresa Fingerprint.
Respondé usando únicamente la información del siguiente contexto.
Si no encontrás la respuesta, decilo claramente sin inventar.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
)


def _format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


def build_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=1024)
    # Override internal Anthropic client to bypass SSL verification on Windows
    llm._client = _anthropic_module.Anthropic(http_client=httpx.Client(verify=False))

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )
    return chain
