"""Carga y valida los perfiles de perfiles/*.json. Ver perfiles/README.md para el esquema."""

import csv
import glob
import json
import os
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ItemContenido:
    titulo: str
    tipo: str | None = None  # "pelicula" | "libro" | None si no se sabe


@dataclass
class Perfil:
    nombre: str
    generos_favoritos_peliculas: list[str] = field(default_factory=list)
    generos_favoritos_libros: list[str] = field(default_factory=list)
    contenido_favorito: list[ItemContenido] = field(default_factory=list)
    no_banca_generos: list[str] = field(default_factory=list)
    no_banca_titulos: list[ItemContenido] = field(default_factory=list)
    notas_libres: str = ""


def _parsear_items(items_crudos: list[dict]) -> list[ItemContenido]:
    return [ItemContenido(titulo=i["titulo"], tipo=i.get("tipo")) for i in items_crudos]


def cargar_perfil(path: str) -> Perfil:
    """Carga y valida un único perfil. Levanta KeyError/ValueError si falta algo clave."""
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)

    if "nombre" not in datos:
        raise ValueError(f"{path}: falta el campo obligatorio 'nombre'")

    generos = datos.get("generos_favoritos", {})
    no_banca = datos.get("no_banca", {})

    return Perfil(
        nombre=datos["nombre"],
        generos_favoritos_peliculas=generos.get("peliculas", []),
        generos_favoritos_libros=generos.get("libros", []),
        contenido_favorito=_parsear_items(datos.get("contenido_favorito", [])),
        no_banca_generos=no_banca.get("generos", []),
        no_banca_titulos=_parsear_items(no_banca.get("titulos", [])),
        notas_libres=datos.get("notas_libres", ""),
    )


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


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, igual que agent/ranking.py, para comparar como compara el ranking."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sin_tildes.lower()


def validar_generos_contra_dataset(perfiles: list[Perfil], dataset_csv_path: str = "data/dataset.csv") -> None:
    """Avisa por consola qué géneros de los perfiles no existen en el dataset (no matchean nunca).

    No levanta excepción: es un chequeo informativo para correr una vez al cargar los
    perfiles, no una validación bloqueante (ver P2/P14 en la revisión del repo).
    """
    with open(dataset_csv_path, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    generos_dataset = {
        _normalizar(g.strip())
        for fila in filas
        for g in (fila.get("generos") or "").split("|")
        if g.strip()
    }

    for perfil in perfiles:
        generos_perfil = (
            perfil.generos_favoritos_peliculas + perfil.generos_favoritos_libros + perfil.no_banca_generos
        )
        for genero in generos_perfil:
            if _normalizar(genero) not in generos_dataset:
                print(f"ojo: el género '{genero}' de {perfil.nombre} no existe en el dataset")
