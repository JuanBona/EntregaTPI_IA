"""Interfaz Streamlit para editar perfiles y generar la recomendación grupal.

Correr con: streamlit run ui/app.py
No se usa en Colab (ver notebook/ para el entregable de Colab).
"""

import os
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.mediador import recomendar_grupal
from agent.perfil import Perfil, cargar_perfil, listar_paths_perfiles
from rag.vectorstore import cargar_vectorstore, construir_vectorstore
from ui.perfil_forms import (
    combinar_generos,
    generos_disponibles,
    guardar_perfil,
    items_a_texto,
    parsear_items_texto,
)

st.set_page_config(page_title="Recomendador grupal", page_icon="🎬", layout="wide")


@st.cache_data
def _cargar_dataset() -> pd.DataFrame:
    csv_path = os.getenv("DATASET_CSV_PATH", "./data/dataset.csv")
    return pd.read_csv(csv_path)


@st.cache_resource(show_spinner="Preparando la base vectorial (puede tardar la primera vez)...")
def _asegurar_vectorstore() -> None:
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    if os.path.isdir(persist_dir) and os.listdir(persist_dir):
        cargar_vectorstore(persist_dir)
    else:
        construir_vectorstore(persist_directory=persist_dir)


def _cargar_perfiles_con_paths() -> list[tuple[Path, Perfil]]:
    return [(Path(p), cargar_perfil(p)) for p in listar_paths_perfiles()]


st.title("🎬 Recomendador grupal de películas y libros")
st.caption("TP2 - Sistemas Inteligentes, editá los perfiles y generá la recomendación del grupo.")

try:
    _asegurar_vectorstore()
    dataset = _cargar_dataset()
except Exception as e:
    st.error(f"No se pudo cargar el dataset o la base vectorial: {e}")
    st.stop()

opciones_pelicula = generos_disponibles(dataset, tipo="pelicula")
opciones_libro = generos_disponibles(dataset, tipo="libro")

try:
    perfiles_con_paths = _cargar_perfiles_con_paths()
except (RuntimeError, ValueError, KeyError) as e:
    st.error(f"No se pudieron cargar los perfiles: {e}")
    st.stop()

if not perfiles_con_paths:
    st.error("No hay perfiles en perfiles/. Cada integrante debe cargar el suyo.")
    st.stop()

tabs = st.tabs([perfil.nombre for _, perfil in perfiles_con_paths])

for tab, (path, perfil) in zip(tabs, perfiles_con_paths):
    with tab:
        st.subheader(f"Perfil de {perfil.nombre}")

        col1, col2 = st.columns(2)
        with col1:
            sel_peliculas = st.multiselect(
                "Géneros favoritos (películas)",
                options=sorted(set(opciones_pelicula) | set(perfil.generos_favoritos_peliculas)),
                default=perfil.generos_favoritos_peliculas,
                key=f"peliculas_generos_{path.stem}",
            )
            otros_peliculas = st.text_input(
                "Otros géneros de películas (separados por coma, opcional)",
                key=f"peliculas_otros_{path.stem}",
            )
        with col2:
            sel_libros = st.multiselect(
                "Géneros favoritos (libros)",
                options=sorted(set(opciones_libro) | set(perfil.generos_favoritos_libros)),
                default=perfil.generos_favoritos_libros,
                key=f"libros_generos_{path.stem}",
            )
            otros_libros = st.text_input(
                "Otros géneros de libros (separados por coma, opcional)",
                key=f"libros_otros_{path.stem}",
            )

        contenido_texto = st.text_area(
            "Contenido favorito (uno por línea; formato 'Título | tipo', tipo opcional)",
            value=items_a_texto(perfil.contenido_favorito),
            key=f"contenido_{path.stem}",
            help=(
                "Una película o libro que ya viste/leíste y te gustó, uno por línea. "
                "El tipo es 'pelicula' o 'libro', y es opcional: si lo dejás vacío "
                "(solo el título, sin '|'), el sistema lo tiene en cuenta para ambas "
                "listas. Ejemplo: 'El nombre del viento | libro'."
            ),
        )

        sel_no_banca_generos = st.multiselect(
            "Géneros que no banca (de películas y de libros, todo junto)",
            options=sorted(set(opciones_pelicula) | set(opciones_libro) | set(perfil.no_banca_generos)),
            default=perfil.no_banca_generos,
            key=f"no_banca_generos_{path.stem}",
            help=(
                "Esta lista es una sola para los dos tipos: un género acá se descarta "
                "tanto si aparece en una película candidata como en un libro."
            ),
        )

        no_banca_titulos_texto = st.text_area(
            "Títulos que no banca (uno por línea; formato 'Título | tipo')",
            value=items_a_texto(perfil.no_banca_titulos),
            key=f"no_banca_titulos_{path.stem}",
            help="Mismo formato que 'Contenido favorito': 'Título | tipo', tipo opcional.",
        )

        notas = st.text_area(
            "Notas libres",
            value=perfil.notas_libres,
            key=f"notas_{path.stem}",
        )

        if st.button("Guardar cambios", key=f"guardar_{path.stem}"):
            nuevo_perfil = Perfil(
                nombre=perfil.nombre,
                generos_favoritos_peliculas=combinar_generos(sel_peliculas, otros_peliculas),
                generos_favoritos_libros=combinar_generos(sel_libros, otros_libros),
                contenido_favorito=parsear_items_texto(contenido_texto),
                no_banca_generos=sel_no_banca_generos,
                no_banca_titulos=parsear_items_texto(no_banca_titulos_texto),
                notas_libres=notas,
            )
            guardar_perfil(nuevo_perfil, str(path))
            st.success(f"Perfil de {perfil.nombre} guardado en {path.name}.")

st.divider()
st.header("Recomendación grupal")

# Un id de conversación por pestaña/sesión del navegador, para que la memoria del
# agente (RunnableWithMessageHistory en agent/mediador.py) no se mezcle entre gente
# distinta usando la demo al mismo tiempo.
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if not os.getenv("GOOGLE_API_KEY"):
    st.error(
        "Falta GOOGLE_API_KEY. Completá tu .env (ver .env.example) con una key "
        "gratis de https://aistudio.google.com/apikey y reiniciá la app."
    )
    st.stop()


def _pedir_recomendacion(mensaje: str | None = None) -> None:
    kwargs = {"session_id": st.session_state.chat_session_id}
    if mensaje:
        kwargs["mensaje"] = mensaje
    try:
        with st.spinner("Buscando candidatos y armando la recomendación..."):
            perfiles_actuales = [cargar_perfil(p) for p in listar_paths_perfiles()]
            st.session_state.resultado = recomendar_grupal(perfiles_actuales, **kwargs)
    except Exception as e:
        st.error(f"Falló la llamada al LLM: {e}")


if st.button("Generar recomendación grupal", type="primary"):
    _pedir_recomendacion()

resultado = st.session_state.resultado
if resultado:
    col_peliculas, col_libros = st.columns(2)
    with col_peliculas:
        st.subheader("Películas")
        st.caption(resultado["criterio_busqueda_peliculas"] or "(sin géneros/títulos de película en los perfiles)")
        st.dataframe(pd.DataFrame(resultado["candidatos_rankeados_peliculas"]))
        st.markdown(resultado["recomendacion_peliculas"])
    with col_libros:
        st.subheader("Libros")
        st.caption(resultado["criterio_busqueda_libros"] or "(sin géneros/títulos de libro en los perfiles)")
        st.dataframe(pd.DataFrame(resultado["candidatos_rankeados_libros"]))
        st.markdown(resultado["recomendacion_libros"])

    st.divider()
    st.caption(
        "¿Querés otra opción o algo distinto? El agente tiene memoria de esta "
        "conversación, así que tiene en cuenta lo que ya te recomendó."
    )
    with st.form("repregunta", clear_on_submit=True):
        repregunta = st.text_input(
            "Pedile algo puntual al agente (ej. \"dame otra opción\", \"algo más liviano\")"
        )
        if st.form_submit_button("Pedir de nuevo") and repregunta.strip():
            _pedir_recomendacion(repregunta.strip())
            st.rerun()
