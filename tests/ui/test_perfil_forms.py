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
