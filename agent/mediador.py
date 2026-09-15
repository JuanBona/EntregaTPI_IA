"""Agente mediador: cruza los 5 perfiles, busca candidatos vía RAG, rankea y le pide
al LLM la recomendación final con el tono de prompts/system_prompt.py.
"""

import os

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.perfil import Perfil, cargar_todos_los_perfiles
from agent.ranking import rankear_candidatos
from prompts.system_prompt import MENSAJE_DEFAULT, prompt
from rag.retriever import retriever

K_CANDIDATOS_RAG = 8
K_CANDIDATOS_FINALES = 3


def construir_criterio_busqueda(perfiles: list[Perfil]) -> str:
    """Combina los gustos de los 5 perfiles en una sola query de texto para el retriever.

    Estrategia simple (fácil de explicar en la defensa): concatenar géneros favoritos
    y títulos de todos, dejando que el embedding semántico encuentre el punto medio
    del grupo. Los "no banca" y las `notas_libres` NO entran acá, se filtran/usan
    después (ranking.py y el prompt del LLM), para no confundir al embedding con
    negaciones (los modelos de embeddings no manejan bien la negación semántica,
    ej. "no me gusta terror" puede quedar cerca de "terror" en el espacio vectorial,
    y las notas libres suelen tener negaciones mezcladas con gustos positivos).
    """
    partes = []
    for perfil in perfiles:
        partes.extend(perfil.generos_favoritos_peliculas)
        partes.extend(perfil.generos_favoritos_libros)
        partes.extend(item.titulo for item in perfil.contenido_favorito)

    return ", ".join(partes)


def _resumen_perfiles_para_prompt(perfiles: list[Perfil]) -> str:
    lineas = []
    for p in perfiles:
        lineas.append(
            f"- {p.nombre}: le gustan {p.generos_favoritos_peliculas + p.generos_favoritos_libros}, "
            f"vio/leyó y le gustó {[i.titulo for i in p.contenido_favorito]}, "
            f"no banca {p.no_banca_generos + [i.titulo for i in p.no_banca_titulos]}. "
            f"Notas: {p.notas_libres or '-'}"
        )
    return "\n".join(lineas)


def _resumen_candidatos_para_prompt(candidatos: list[dict]) -> str:
    lineas = []
    for c in candidatos:
        lineas.append(
            f"- \"{c['titulo']}\" ({c['tipo']}, {c.get('anio', '?')}, rating {c.get('rating', '?')}): "
            f"{c['sinopsis'][:300]}"
        )
    return "\n".join(lineas)


def _get_llm() -> ChatGoogleGenerativeAI:
    modelo = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    return ChatGoogleGenerativeAI(model=modelo, temperature=0.7)


# Memoria en RAM por session_id (alcanza para el TP; no hace falta persistirla).
_historiales: dict[str, InMemoryChatMessageHistory] = {}


def _historial(session_id: str) -> InMemoryChatMessageHistory:
    return _historiales.setdefault(session_id, InMemoryChatMessageHistory())


def recomendar_grupal(
    perfiles: list[Perfil] | None = None,
    mensaje: str = MENSAJE_DEFAULT,
    session_id: str = "default",
) -> dict:
    """Función principal del módulo. Devuelve {recomendacion, candidatos_rankeados}.

    Args:
        perfiles: si no se pasa, carga automáticamente todos los perfiles/*.json.
        mensaje: pedido puntual ("dame otra opción", etc). Por default pide la
            recomendación inicial.
        session_id: separa el historial de memoria entre conversaciones distintas.
    """
    perfiles = perfiles or cargar_todos_los_perfiles()

    criterio = construir_criterio_busqueda(perfiles)
    candidatos = retriever(criterio, k=K_CANDIDATOS_RAG)
    candidatos_rankeados = rankear_candidatos(candidatos, perfiles)[:K_CANDIDATOS_FINALES]

    chain = prompt | _get_llm() | StrOutputParser()
    chain_con_memoria = RunnableWithMessageHistory(
        chain, _historial, input_messages_key="mensaje", history_messages_key="historial"
    )
    texto = chain_con_memoria.invoke(
        {
            "perfiles_resumen": _resumen_perfiles_para_prompt(perfiles),
            "candidatos_resumen": _resumen_candidatos_para_prompt(candidatos_rankeados),
            "mensaje": mensaje,
        },
        config={"configurable": {"session_id": session_id}},
    )

    return {
        "recomendacion": texto,
        "candidatos_rankeados": candidatos_rankeados,
        "criterio_busqueda": criterio,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    resultado = recomendar_grupal()
    print(resultado["recomendacion"])
