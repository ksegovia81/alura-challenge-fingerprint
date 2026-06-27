"""
Extrae el texto de fingerprint_dossier.pdf usando Claude (funciona con PDFs escaneados).
Guarda el resultado en fingerprint_dossier.txt para que ingest.py lo indexe.
Correr una sola vez: python -m app.extract_pdf
"""
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx
import anthropic

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "fingerprint_dossier.pdf"
TXT_PATH = BASE_DIR / "fingerprint_dossier.txt"


def extract():
    print(f"Leyendo PDF: {PDF_PATH}")
    with open(PDF_PATH, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    print("Enviando a Claude para extracción de texto...")
    client = anthropic.Anthropic(http_client=httpx.Client(verify=False))
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Extraé todo el texto de este documento PDF conservando "
                        "la estructura (títulos, secciones, listas). "
                        "Devolvé solo el texto plano, sin comentarios adicionales."
                    ),
                },
            ],
        }],
    )

    text = response.content[0].text
    TXT_PATH.write_text(text, encoding="utf-8")
    print(f"Texto extraído guardado en: {TXT_PATH}")
    print(f"  {len(text)} caracteres, ~{len(text.split())} palabras")


if __name__ == "__main__":
    extract()
