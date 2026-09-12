"""Construye/carga el vector store de ChromaDB a partir de data/dataset.csv.

Embeddings: HuggingFace local multilingüe (ver docs/DISENO.md para el porqué).
"""

import os

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

_EMBEDDINGS_MODEL_DEFAULT = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def _get_embeddings() -> HuggingFaceEmbeddings:
    modelo = os.getenv("EMBEDDINGS_MODEL", _EMBEDDINGS_MODEL_DEFAULT)
    return HuggingFaceEmbeddings(model_name=modelo)


def _dataframe_a_documentos(df: pd.DataFrame) -> list[Document]:
    documentos = []
    for _, fila in df.iterrows():
        contenido = (
            f"Título: {fila['titulo']}\n"
            f"Tipo: {fila['tipo']}\n"
            f"Géneros: {fila['generos']}\n"
            f"Sinopsis: {fila['sinopsis']}"
        )
        metadata = {
            "id": fila["id"],
            "tipo": fila["tipo"],
            "titulo": fila["titulo"],
            "generos": fila["generos"],
            "rating": float(fila["rating"]) if pd.notna(fila["rating"]) else None,
            "anio": int(fila["anio"]) if pd.notna(fila["anio"]) else None,
            "autor_director": fila["autor_director"],
            "sinopsis": fila["sinopsis"]  # NUEVA LÍNEA 
        }
        documentos.append(Document(page_content=contenido, metadata=metadata, id=fila["id"]))
    return documentos


def construir_vectorstore(
    csv_path: str | None = None,
    persist_directory: str | None = None,
) -> Chroma:
    """Lee el CSV, genera embeddings y los persiste en ChromaDB. Idempotente por `id`."""
    csv_path = csv_path or os.getenv("DATASET_CSV_PATH", "./data/dataset.csv")
    persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")

    df = pd.read_csv(csv_path)
    documentos = _dataframe_a_documentos(df)

    vectorstore = Chroma(
        collection_name="recomendador",
        embedding_function=_get_embeddings(),
        persist_directory=persist_directory,
    )
    vectorstore.add_documents(documentos, ids=[d.id for d in documentos])
    return vectorstore


def cargar_vectorstore(persist_directory: str | None = None) -> Chroma:
    """Carga un vector store ya persistido, sin volver a generar embeddings."""
    persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    return Chroma(
        collection_name="recomendador",
        embedding_function=_get_embeddings(),
        persist_directory=persist_directory,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    vs = construir_vectorstore()
    print(f"Vectorstore construido con {vs._collection.count()} documentos.")
