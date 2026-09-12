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
