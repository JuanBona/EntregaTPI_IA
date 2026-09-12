# Interfaz Streamlit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir una interfaz Streamlit local (`ui/app.py`) que permita editar los 5 perfiles del grupo y generar la recomendación grupal con un click, sin tocar `notebook/` ni la lógica de `agent/`/`rag/`.

**Architecture:** Capa fina sobre los módulos existentes. Lógica pura y testeable (conversión perfil↔formulario, listado de paths de perfiles) vive en funciones separadas con tests unitarios; el archivo `ui/app.py` solo arma los widgets y llama a esas funciones + a `agent.mediador.recomendar_grupal()`.

**Tech Stack:** Streamlit, pandas (ya en el proyecto), pytest (nuevo, para los tests unitarios).

---

## Contexto para quien ejecute este plan

- El repo ya tiene un pipeline funcionando: `ingestion/` → `data/dataset.csv` → `rag/` (Chroma + embeddings HuggingFace) → `agent/` (perfiles + ranking + LLM Gemini) → `prompts/` (tono).
- `agent/perfil.py` define `Perfil` (dataclass) e `ItemContenido` (dataclass con `titulo: str` y `tipo: str | None`), y carga perfiles desde `perfiles/*.json` (excluyendo `perfiles/ejemplo_perfil.json`).
- `agent/mediador.py` expone `recomendar_grupal(perfiles=None) -> {"recomendacion": str, "candidatos_rankeados": list[dict], "criterio_busqueda": str}`.
- `rag/vectorstore.py` expone `construir_vectorstore()` (lee CSV, genera embeddings, persiste) y `cargar_vectorstore()` (solo carga lo ya persistido). `rag/retriever.py` usa internamente `cargar_vectorstore()` cacheado con `lru_cache`.
- El repo no tiene tests todavía. Este plan introduce `pytest` y una carpeta `tests/`.
- Correr todo desde la raíz del repo. Los comandos de test asumen `python -m pytest ...` (así la raíz del repo queda en `sys.path` automáticamente).

---

### Task 1: Exponer `listar_paths_perfiles()` en `agent/perfil.py`

La UI necesita saber **de qué archivo** vino cada perfil (para poder guardarlo de vuelta ahí). Hoy `cargar_todos_los_perfiles()` descarta esa información. Se extrae el glob a una función propia y se reusa.

**Files:**
- Modify: `agent/perfil.py`
- Test: `tests/agent/test_perfil.py` (nuevo)

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/agent/test_perfil.py`:

```python
import json

from agent.perfil import cargar_todos_los_perfiles, listar_paths_perfiles


def _escribir_perfil(path, nombre):
    datos = {
        "nombre": nombre,
        "generos_favoritos": {"peliculas": ["terror"], "libros": []},
        "contenido_favorito": [],
        "no_banca": {"generos": [], "titulos": []},
        "notas_libres": "",
    }
    path.write_text(json.dumps(datos), encoding="utf-8")


def test_listar_paths_perfiles_excluye_ejemplo(tmp_path):
    _escribir_perfil(tmp_path / "bruno.json", "Bruno")
    _escribir_perfil(tmp_path / "juan.json", "Juan")
    _escribir_perfil(tmp_path / "ejemplo_perfil.json", "Juana")

    paths = listar_paths_perfiles(str(tmp_path))

    nombres_archivo = sorted(p.split("\\")[-1].split("/")[-1] for p in paths)
    assert nombres_archivo == ["bruno.json", "juan.json"]


def test_cargar_todos_los_perfiles_usa_los_mismos_paths(tmp_path):
    _escribir_perfil(tmp_path / "bruno.json", "Bruno")
    _escribir_perfil(tmp_path / "juan.json", "Juan")
    _escribir_perfil(tmp_path / "ejemplo_perfil.json", "Juana")

    perfiles = cargar_todos_los_perfiles(str(tmp_path))

    assert sorted(p.nombre for p in perfiles) == ["Bruno", "Juan"]


def test_cargar_todos_los_perfiles_falla_si_no_hay_perfiles(tmp_path):
    _escribir_perfil(tmp_path / "ejemplo_perfil.json", "Juana")

    try:
        cargar_todos_los_perfiles(str(tmp_path))
        assert False, "debería haber levantado RuntimeError"
    except RuntimeError:
        pass
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `python -m pytest tests/agent/test_perfil.py -v`
Expected: FAIL con `ImportError: cannot import name 'listar_paths_perfiles'`.

- [ ] **Step 3: Implementar `listar_paths_perfiles` y refactorizar `cargar_todos_los_perfiles`**

En `agent/perfil.py`, reemplazar la función `cargar_todos_los_perfiles` completa por:

```python
def listar_paths_perfiles(carpeta: str = "perfiles") -> list[str]:
    """Paths de perfiles reales en `carpeta`, excluyendo ejemplo_perfil.json."""
    return [
        path
        for path in sorted(glob.glob(os.path.join(carpeta, "*.json")))
        if os.path.basename(path) != "ejemplo_perfil.json"
    ]


def cargar_todos_los_perfiles(carpeta: str = "perfiles") -> list[Perfil]:
    """Carga todos los .json de la carpeta, excepto ejemplo_perfil.json."""
    paths = listar_paths_perfiles(carpeta)

    if not paths:
        raise RuntimeError(
            f"No se encontró ningún perfil en '{carpeta}/'. "
            "Cada integrante debe copiar perfiles/ejemplo_perfil.json y completarlo."
        )
    return [cargar_perfil(path) for path in paths]
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `python -m pytest tests/agent/test_perfil.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Confirmar que el comportamiento real (perfiles/ del repo) sigue andando**

Run: `python -c "from agent.perfil import cargar_todos_los_perfiles; print([p.nombre for p in cargar_todos_los_perfiles()])"`
Expected: `['Bruno', 'Juan', 'Lucas', 'Marcos', 'Rafa']`

- [ ] **Step 6: Commit**

```bash
git add agent/perfil.py tests/agent/test_perfil.py
git commit -m "Exponer listar_paths_perfiles para que la UI sepa a qué archivo guardar"
```

---

### Task 2: `ui/perfil_forms.py` — lógica pura de conversión perfil ↔ formulario

**Files:**
- Create: `ui/__init__.py` (vacío)
- Create: `ui/perfil_forms.py`
- Test: `tests/ui/test_perfil_forms.py` (nuevo)

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/ui/test_perfil_forms.py`:

```python
import pandas as pd

from agent.perfil import ItemContenido, Perfil, cargar_perfil
from ui.perfil_forms import (
    combinar_generos,
    generos_disponibles,
    guardar_perfil,
    items_a_texto,
    parsear_items_texto,
)


def test_items_a_texto_y_parsear_items_texto_hacen_round_trip():
    items = [
        ItemContenido(titulo="Hereditary", tipo="pelicula"),
        ItemContenido(titulo="Arrival", tipo=None),
    ]
    texto = items_a_texto(items)
    assert texto == "Hereditary | pelicula\nArrival"
    assert parsear_items_texto(texto) == items


def test_parsear_items_texto_ignora_lineas_vacias():
    texto = "Hereditary | pelicula\n\n   \nIt | libro"
    assert parsear_items_texto(texto) == [
        ItemContenido(titulo="Hereditary", tipo="pelicula"),
        ItemContenido(titulo="It", tipo="libro"),
    ]


def test_combinar_generos_deduplica_preservando_orden():
    resultado = combinar_generos(["terror", "thriller"], "thriller, gore,  ")
    assert resultado == ["terror", "thriller", "gore"]


def test_guardar_perfil_hace_round_trip_con_cargar_perfil(tmp_path):
    perfil = Perfil(
        nombre="Test",
        generos_favoritos_peliculas=["terror", "thriller"],
        generos_favoritos_libros=["misterio"],
        contenido_favorito=[ItemContenido(titulo="It", tipo="libro")],
        no_banca_generos=["romance"],
        no_banca_titulos=[ItemContenido(titulo="Twilight", tipo="pelicula")],
        notas_libres="nada de romance",
    )
    path = tmp_path / "test.json"

    guardar_perfil(perfil, str(path))
    recargado = cargar_perfil(str(path))

    assert recargado == perfil


def test_generos_disponibles_devuelve_generos_unicos_ordenados():
    df = pd.DataFrame(
        {
            "tipo": ["pelicula", "pelicula", "libro"],
            "generos": ["Thriller|Terror", "Terror|Accion", "Misterio"],
        }
    )
    assert generos_disponibles(df, tipo="pelicula") == ["Accion", "Terror", "Thriller"]
    assert generos_disponibles(df, tipo="libro") == ["Misterio"]
    assert generos_disponibles(df) == ["Accion", "Misterio", "Terror", "Thriller"]
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `python -m pytest tests/ui/test_perfil_forms.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ui'`.

- [ ] **Step 3: Crear `ui/__init__.py`**

Archivo vacío.

- [ ] **Step 4: Implementar `ui/perfil_forms.py`**

```python
"""Conversión pura entre Perfil (agent/perfil.py) y los datos que maneja la UI.

Sin dependencias de Streamlit: todo acá es testeable con pytest normal.
"""

import json

import pandas as pd

from agent.perfil import ItemContenido, Perfil


def items_a_texto(items: list[ItemContenido]) -> str:
    """Un ItemContenido por línea: 'Titulo | tipo', o solo 'Titulo' si no hay tipo."""
    lineas = []
    for item in items:
        lineas.append(f"{item.titulo} | {item.tipo}" if item.tipo else item.titulo)
    return "\n".join(lineas)


def parsear_items_texto(texto: str) -> list[ItemContenido]:
    """Inverso de items_a_texto. Ignora líneas vacías."""
    items = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if "|" in linea:
            titulo, tipo = linea.split("|", 1)
            items.append(ItemContenido(titulo=titulo.strip(), tipo=tipo.strip() or None))
        else:
            items.append(ItemContenido(titulo=linea, tipo=None))
    return items


def combinar_generos(seleccionados: list[str], texto_libre: str) -> list[str]:
    """Combina lo elegido en el multiselect con géneros nuevos tipeados a mano
    (separados por coma), sin duplicar y preservando el orden de aparición."""
    extra = [g.strip() for g in texto_libre.split(",") if g.strip()]
    return list(dict.fromkeys([*seleccionados, *extra]))


def guardar_perfil(perfil: Perfil, path: str) -> None:
    """Escribe `perfil` en `path` con el mismo schema que espera agent.perfil.cargar_perfil."""
    datos = {
        "nombre": perfil.nombre,
        "generos_favoritos": {
            "peliculas": list(perfil.generos_favoritos_peliculas),
            "libros": list(perfil.generos_favoritos_libros),
        },
        "contenido_favorito": [_item_a_dict(i) for i in perfil.contenido_favorito],
        "no_banca": {
            "generos": list(perfil.no_banca_generos),
            "titulos": [_item_a_dict(i) for i in perfil.no_banca_titulos],
        },
        "notas_libres": perfil.notas_libres,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _item_a_dict(item: ItemContenido) -> dict:
    datos = {"titulo": item.titulo}
    if item.tipo:
        datos["tipo"] = item.tipo
    return datos


def generos_disponibles(df: pd.DataFrame, tipo: str | None = None) -> list[str]:
    """Géneros únicos presentes en `df` (columna 'generos', separados por '|'),
    opcionalmente filtrados por `tipo` ('pelicula' | 'libro')."""
    if tipo:
        df = df[df["tipo"] == tipo]
    generos = set()
    for valor in df["generos"].dropna():
        generos.update(g.strip() for g in str(valor).split("|") if g.strip())
    return sorted(generos, key=str.lower)
```

- [ ] **Step 5: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/ui/test_perfil_forms.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add ui/__init__.py ui/perfil_forms.py tests/ui/test_perfil_forms.py
git commit -m "Agregar ui/perfil_forms.py: conversion perfil <-> formulario, con tests"
```

---

### Task 3: `ui/app.py` — la app Streamlit

No lleva tests automatizados (es renderizado de widgets); se verifica con un smoke test manual de arranque (Step 3) y con prueba manual completa en Task 5.

**Files:**
- Create: `ui/app.py`

- [ ] **Step 1: Implementar `ui/app.py`**

```python
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
```

- [ ] **Step 2: Agregar `streamlit` a `requirements.txt`**

En `requirements.txt`, agregar al final:

```
# Interfaz de prueba/demo (no se usa en Colab)
streamlit>=1.38.0
```

- [ ] **Step 3: Instalar y hacer un smoke test de arranque**

```bash
pip install -q streamlit
streamlit run ui/app.py --server.headless true --server.port 8501 &
```

Guardar el PID (`$!` en bash) para poder matarlo después. Luego:

```bash
curl --silent --retry 15 --retry-delay 1 --retry-connrefused -o /dev/null -w "%{http_code}\n" http://localhost:8501
```

Expected: `200`

Matar el proceso:

```bash
kill %1
```

Esto solo confirma que la app arranca sin errores de import/sintaxis — **no** reemplaza la prueba manual completa del Task 5.

- [ ] **Step 4: Commit**

```bash
git add ui/app.py requirements.txt
git commit -m "Agregar ui/app.py: interfaz Streamlit para editar perfiles y generar la recomendacion"
```

---

### Task 4: Documentar cómo correr la interfaz

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Agregar sección al README**

En `README.md`, después de la sección "## Correr cada módulo por separado" y antes de "## Cargar tu perfil", agregar:

```markdown
## Interfaz de prueba/demo (Streamlit)

Para probar el sistema completo con una interfaz web local (editar perfiles + generar
recomendación con un click), sin usar Colab:

```bash
streamlit run ui/app.py
```

Abre automáticamente `http://localhost:8501` en el navegador. Necesita `GOOGLE_API_KEY`
en el `.env` (ver arriba) y que `data/dataset.csv` exista — el vectorstore se genera
solo la primera vez que se corre.

Es una herramienta separada de `notebook/` (pensada para desarrollo y para la defensa
oral), no un entregable del TP.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Documentar como correr la interfaz Streamlit"
```

---

### Task 5: Verificación manual end-to-end

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr la app de verdad**

```bash
streamlit run ui/app.py
```

- [ ] **Step 2: Checklist manual en el navegador**

- [ ] Los 5 tabs (Bruno, Juan, Lucas, Marcos, Rafa) muestran los datos actuales de cada `perfiles/<nombre>.json`.
- [ ] Editar un género favorito de un perfil, click en "Guardar cambios" → aparece el mensaje de éxito.
- [ ] Abrir `perfiles/<nombre>.json` y confirmar que el cambio se escribió en disco.
- [ ] Click en "Generar recomendación grupal" → aparecen: criterio de búsqueda, tabla de candidatos, recomendación final en texto.
- [ ] Comentar/renombrar temporalmente `GOOGLE_API_KEY` en `.env`, reiniciar la app, click en "Generar recomendación grupal" → se ve `st.error` claro, no un traceback. Restaurar la key después.

- [ ] **Step 3: Detener la app**

`Ctrl+C` en la terminal donde corre `streamlit run`.

No hay commit en esta task (es solo verificación).
