# rag/

Toma `data/dataset.csv` (generado por `/ingestion`), genera embeddings locales y los
persiste en ChromaDB. Expone `retriever(query, k)` para que `/agent` la use.

## Setup

No necesita API keys — los embeddings corren local (`sentence-transformers`, ver
`docs/DISENO.md`). La primera vez descarga el modelo (~1 GB), puede tardar un rato.

## Correr

1. Construir el vector store (una vez, o cada vez que cambie `data/dataset.csv`):

   ```bash
   python -m rag.vectorstore
   ```

   Esto persiste en `data/chroma/` (gitignoreado — cada uno lo genera local).

2. Probar el retriever:

   ```bash
   python -c "from rag.retriever import retriever; print(retriever('thriller psicológico con giros', k=3))"
   ```

## Archivos

- `vectorstore.py` — `construir_vectorstore()` (primera carga) y `cargar_vectorstore()`
  (cargas siguientes, no re-embeddea).
- `retriever.py` — `retriever(query, k, tipo=None)`, la función que consume `/agent`.

## Contrato con /agent

`retriever(query: str, k: int, tipo: str | None) -> list[dict]` donde cada dict tiene:
`titulo, tipo, generos, rating, anio, autor_director, sinopsis, score`. No cambiar esta
forma sin avisar al que está en `/agent`.
