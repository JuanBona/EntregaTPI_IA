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


def construir_criterio_busqueda(perfiles: list[Perfil], tipo: str) -> str:
    """Combina los gustos de los 5 perfiles en una query de texto para el retriever,
    separada por tipo ("pelicula" o "libro").

    Antes se armaba una sola query mezclando géneros y títulos de películas y libros
    de los 5 perfiles, y se buscaba una sola vez. Como el dataset tiene casi el doble
    de películas que de libros, esa query mezclada quedaba dominada por vocabulario
    de películas y el retriever casi no traía libros entre los candidatos, aunque el
    grupo tuviera géneros de libros favoritos. Separar la query por tipo, junto con el
    filtro `tipo=` que ya soporta `rag.retriever`, garantiza que se busquen y rankeen
    candidatos de cada tipo por separado.

    Los "no banca" y las `notas_libres` NO entran acá, se filtran/usan después
    (ranking.py y el prompt del LLM), para no confundir al embedding con negaciones
    (los modelos de embeddings no manejan bien la negación semántica, ej. "no me gusta
    terror" puede quedar cerca de "terror" en el espacio vectorial, y las notas libres
    suelen tener negaciones mezcladas con gustos positivos).
    """
    generos_favoritos = (
        [g for perfil in perfiles for g in perfil.generos_favoritos_peliculas]
        if tipo == "pelicula"
        else [g for perfil in perfiles for g in perfil.generos_favoritos_libros]
    )
    titulos = [
        item.titulo
        for perfil in perfiles
        for item in perfil.contenido_favorito
        if item.tipo in (None, tipo)
    ]
    return ", ".join(generos_favoritos + titulos)


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
    if not candidatos:
        return "(no se encontró ningún candidato de este tipo)"
    lineas = []
    for c in candidatos:
        lineas.append(
            f"- \"{c['titulo']}\" ({c['tipo']}, {c.get('anio', '?')}, rating {c.get('rating', '?')}): "
            f"{c['sinopsis'][:300]}"
        )
    return "\n".join(lineas)


# Marca el corte entre la sección de película y la de libro en el texto que devuelve
# el LLM (ver prompts/system_prompt.py, el prompt le pide que respete este encabezado).
_MARCA_SEPARACION_LIBRO = "## Libro"


def _separar_recomendacion(texto: str) -> tuple[str, str]:
    """Separa el texto del LLM en (sección película, sección libro) usando el
    encabezado que le pedimos en el prompt. Si el LLM no lo respetó, devuelve el texto
    completo en ambas partes en vez de perder contenido."""
    if _MARCA_SEPARACION_LIBRO not in texto:
        return texto, texto
    peliculas, libro = texto.split(_MARCA_SEPARACION_LIBRO, 1)
    return peliculas.strip(), (_MARCA_SEPARACION_LIBRO + libro).strip()


def _get_llm() -> ChatGoogleGenerativeAI:
    modelo = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    return ChatGoogleGenerativeAI(model=modelo, temperature=0.7)


# Memoria en RAM por session_id (alcanza para el TP; no hace falta persistirla).
_historiales: dict[str, InMemoryChatMessageHistory] = {}


def _historial(session_id: str) -> InMemoryChatMessageHistory:
    return _historiales.setdefault(session_id, InMemoryChatMessageHistory())


def _buscar_y_rankear(perfiles: list[Perfil], tipo: str) -> tuple[str, list[dict]]:
    criterio = construir_criterio_busqueda(perfiles, tipo)
    candidatos = retriever(criterio, k=K_CANDIDATOS_RAG, tipo=tipo)
    candidatos_rankeados = rankear_candidatos(candidatos, perfiles)[:K_CANDIDATOS_FINALES]
    return criterio, candidatos_rankeados


def recomendar_grupal(
    perfiles: list[Perfil] | None = None,
    mensaje: str = MENSAJE_DEFAULT,
    session_id: str = "default",
) -> dict:
    """Función principal del módulo. Busca y rankea películas y libros por separado
    (ver `construir_criterio_busqueda`) y le pide al LLM una recomendación de cada tipo
    en una sola llamada.

    Devuelve un dict con, para cada tipo ("_peliculas"/"_libros"): el criterio de
    búsqueda usado y los candidatos rankeados; más "recomendacion" (el texto completo
    del LLM, con ambas secciones) y "recomendacion_peliculas"/"recomendacion_libros"
    (el mismo texto separado por sección, para mostrar cada una por su lado en la UI).

    Args:
        perfiles: si no se pasa, carga automáticamente todos los perfiles/*.json.
        mensaje: pedido puntual ("dame otra opción", etc). Por default pide la
            recomendación inicial.
        session_id: separa el historial de memoria entre conversaciones distintas.
    """
    perfiles = perfiles or cargar_todos_los_perfiles()

    criterio_peliculas, candidatos_peliculas = _buscar_y_rankear(perfiles, "pelicula")
    criterio_libros, candidatos_libros = _buscar_y_rankear(perfiles, "libro")

    chain = prompt | _get_llm() | StrOutputParser()
    chain_con_memoria = RunnableWithMessageHistory(
        chain, _historial, input_messages_key="mensaje", history_messages_key="historial"
    )
    texto = chain_con_memoria.invoke(
        {
            "perfiles_resumen": _resumen_perfiles_para_prompt(perfiles),
            "candidatos_resumen_peliculas": _resumen_candidatos_para_prompt(candidatos_peliculas),
            "candidatos_resumen_libros": _resumen_candidatos_para_prompt(candidatos_libros),
            "mensaje": mensaje,
        },
        config={"configurable": {"session_id": session_id}},
    )
    recomendacion_peliculas, recomendacion_libros = _separar_recomendacion(texto)

    return {
        "recomendacion": texto,
        "recomendacion_peliculas": recomendacion_peliculas,
        "recomendacion_libros": recomendacion_libros,
        "candidatos_rankeados_peliculas": candidatos_peliculas,
        "candidatos_rankeados_libros": candidatos_libros,
        "criterio_busqueda_peliculas": criterio_peliculas,
        "criterio_busqueda_libros": criterio_libros,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    resultado = recomendar_grupal()
    print(resultado["recomendacion"])
