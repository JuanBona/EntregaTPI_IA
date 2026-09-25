from agent.mediador import _separar_recomendacion, construir_criterio_busqueda
from agent.perfil import ItemContenido, Perfil


def _perfil(nombre, peliculas_fav=None, libros_fav=None, contenido_favorito=None):
    return Perfil(
        nombre=nombre,
        generos_favoritos_peliculas=peliculas_fav or [],
        generos_favoritos_libros=libros_fav or [],
        contenido_favorito=contenido_favorito or [],
    )


def test_criterio_pelicula_no_incluye_generos_de_libros():
    """Regresión: antes se armaba una sola query mezclando géneros de película y de
    libro, lo que hacía que el vocabulario de películas (casi el doble en el dataset)
    ahogara al de libros y el retriever casi no trajera libros como candidatos."""
    perfil = _perfil("Test", peliculas_fav=["terror"], libros_fav=["policial"])

    criterio = construir_criterio_busqueda([perfil], tipo="pelicula")

    assert "terror" in criterio
    assert "policial" not in criterio


def test_criterio_libro_no_incluye_generos_de_peliculas():
    perfil = _perfil("Test", peliculas_fav=["terror"], libros_fav=["policial"])

    criterio = construir_criterio_busqueda([perfil], tipo="libro")

    assert "policial" in criterio
    assert "terror" not in criterio


def test_criterio_incluye_titulos_del_tipo_correspondiente():
    perfil = _perfil(
        "Test",
        contenido_favorito=[
            ItemContenido(titulo="El resplandor", tipo="pelicula"),
            ItemContenido(titulo="Mientras dormían", tipo="libro"),
            ItemContenido(titulo="Sin tipo aclarado"),
        ],
    )

    criterio_pelicula = construir_criterio_busqueda([perfil], tipo="pelicula")
    criterio_libro = construir_criterio_busqueda([perfil], tipo="libro")

    assert "El resplandor" in criterio_pelicula
    assert "Mientras dormían" not in criterio_pelicula
    assert "Sin tipo aclarado" in criterio_pelicula

    assert "Mientras dormían" in criterio_libro
    assert "El resplandor" not in criterio_libro
    assert "Sin tipo aclarado" in criterio_libro


def test_separar_recomendacion_corta_en_el_encabezado_de_libro():
    texto = "## Pelicula\nVa por acá.\n\n## Libro\nVa por allá."

    peliculas, libro = _separar_recomendacion(texto)

    assert peliculas == "## Pelicula\nVa por acá."
    assert libro == "## Libro\nVa por allá."


def test_separar_recomendacion_sin_encabezado_devuelve_todo_en_ambos():
    texto = "El LLM no respetó el formato pedido."

    peliculas, libro = _separar_recomendacion(texto)

    assert peliculas == texto
    assert libro == texto
