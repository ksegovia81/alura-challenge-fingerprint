"""
Indexa FINGERPRINT.pdf en ChromaDB.
Correr una sola vez (o cuando el PDF cambie): python -m app.ingest
"""
import os
import ssl

# Fix SSL on Windows (affects Python ssl module and requests)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

# Fix SSL for httpx used internally by huggingface_hub
import httpx
_orig_client_init = httpx.Client.__init__
def _no_verify_client_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _orig_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _no_verify_client_init

from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "FINGERPRINT.pdf"
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
COLLECTION = "fingerprint"


def ingest():
    print(f"Cargando PDF: {PDF_PATH}")
    loader = PyMuPDFLoader(str(PDF_PATH))
    docs = loader.load()
    print(f"  {len(docs)} páginas cargadas")

    if docs:
        sample = docs[0].page_content[:300].strip()
        print(f"  Muestra pág 1: {repr(sample)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    print(f"  {len(chunks)} chunks generados")

    if not chunks:
        print("ERROR: El PDF no tiene texto extraíble.")
        return

    print("Generando embeddings (primera vez puede tardar ~1 min)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Guardando en ChromaDB: {CHROMA_DIR}")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION,
    )
    print("Indexación completa.")


if __name__ == "__main__":
    ingest()
