"""Interfaz Streamlit para editar perfiles y generar la recomendación grupal.

Correr con: streamlit run ui/app.py
No se usa en Colab (ver notebook/ para el entregable de Colab).
"""

import os
import sys
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
st.caption("TP2 - Sistemas Inteligentes — editá los perfiles y generá la recomendación del grupo.")

_asegurar_vectorstore()
dataset = _cargar_dataset()
opciones_pelicula = generos_disponibles(dataset, tipo="pelicula")
opciones_libro = generos_disponibles(dataset, tipo="libro")

perfiles_con_paths = _cargar_perfiles_con_paths()
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
                key=f"peliculas_generos_{perfil.nombre}",
            )
            otros_peliculas = st.text_input(
                "Otros géneros de películas (coma-separados, opcional)",
                key=f"peliculas_otros_{perfil.nombre}",
            )
        with col2:
            sel_libros = st.multiselect(
                "Géneros favoritos (libros)",
                options=sorted(set(opciones_libro) | set(perfil.generos_favoritos_libros)),
                default=perfil.generos_favoritos_libros,
                key=f"libros_generos_{perfil.nombre}",
            )
            otros_libros = st.text_input(
                "Otros géneros de libros (coma-separados, opcional)",
                key=f"libros_otros_{perfil.nombre}",
            )

        contenido_texto = st.text_area(
            "Contenido favorito (uno por línea; formato 'Título | tipo', tipo opcional)",
            value=items_a_texto(perfil.contenido_favorito),
            key=f"contenido_{perfil.nombre}",
        )

        sel_no_banca_generos = st.multiselect(
            "Géneros que no banca",
            options=sorted(set(opciones_pelicula) | set(opciones_libro) | set(perfil.no_banca_generos)),
            default=perfil.no_banca_generos,
            key=f"no_banca_generos_{perfil.nombre}",
        )

        no_banca_titulos_texto = st.text_area(
            "Títulos que no banca (uno por línea; formato 'Título | tipo')",
            value=items_a_texto(perfil.no_banca_titulos),
            key=f"no_banca_titulos_{perfil.nombre}",
        )

        notas = st.text_area(
            "Notas libres",
            value=perfil.notas_libres,
            key=f"notas_{perfil.nombre}",
        )

        if st.button("Guardar cambios", key=f"guardar_{perfil.nombre}"):
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

if st.button("Generar recomendación grupal", type="primary"):
    if not os.getenv("GOOGLE_API_KEY"):
        st.error(
            "Falta GOOGLE_API_KEY. Completá tu .env (ver .env.example) con una key "
            "gratis de https://aistudio.google.com/apikey y reiniciá la app."
        )
        st.stop()

    with st.spinner("Buscando candidatos y armando la recomendación..."):
        perfiles_actuales = [cargar_perfil(p) for p in listar_paths_perfiles()]
        resultado = recomendar_grupal(perfiles_actuales)

    st.subheader("Criterio de búsqueda usado")
    st.caption(resultado["criterio_busqueda"])

    st.subheader("Candidatos rankeados")
    st.dataframe(pd.DataFrame(resultado["candidatos_rankeados"]))

    st.subheader("Recomendación final")
    st.markdown(resultado["recomendacion"])
