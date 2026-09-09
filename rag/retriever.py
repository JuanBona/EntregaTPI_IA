"""Función pública que consume agent/: retriever(query, k) -> candidatos.

Cualquier cambio interno de rag/vectorstore.py no debería romper esta interfaz.
"""

from functools import lru_cache

from rag.vectorstore import cargar_vectorstore


@lru_cache(maxsize=1)
def _vectorstore():
    return cargar_vectorstore()


def retriever(query: str, k: int = 5, tipo: str | None = None) -> list[dict]:
    """Busca los `k` candidatos más relevantes para `query`.

    Args:
        query: texto de búsqueda (ej. géneros/gustos combinados de los 5 perfiles).
        k: cantidad de resultados a devolver.
        tipo: si se pasa "pelicula" o "libro", filtra el resultado a ese tipo.

    Returns:
        Lista de dicts: {titulo, tipo, generos, rating, anio, autor_director, sinopsis, score}
    """
    vectorstore = _vectorstore()
    filtro = {"tipo": tipo} if tipo else None

    resultados = vectorstore.similarity_search_with_score(query, k=k, filter=filtro)

    candidatos = []
    for doc, score in resultados:
        candidatos.append(
            {
                "titulo": doc.metadata.get("titulo"),
                "tipo": doc.metadata.get("tipo"),
                "generos": doc.metadata.get("generos"),
                "rating": doc.metadata.get("rating"),
                "anio": doc.metadata.get("anio"),
                "autor_director": doc.metadata.get("autor_director"),
                "sinopsis": doc.page_content.split("Sinopsis: ", 1)[-1], 
                "score": score,  # distancia: más bajo = más parecido
            }
        )
    return candidatos
