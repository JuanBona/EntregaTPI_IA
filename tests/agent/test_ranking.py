from agent.perfil import ItemContenido, Perfil
from agent.ranking import _score_candidato, rankear_candidatos


def _perfil(
    nombre,
    peliculas_fav=None,
    libros_fav=None,
    no_banca_generos=None,
    no_banca_titulos=None,
):
    return Perfil(
        nombre=nombre,
        generos_favoritos_peliculas=peliculas_fav or [],
        generos_favoritos_libros=libros_fav or [],
        no_banca_generos=no_banca_generos or [],
        no_banca_titulos=no_banca_titulos or [],
    )


def test_genero_favorito_sin_tilde_matchea_candidato_con_tilde():
    perfil = _perfil("Test", peliculas_fav=["ciencia ficcion", "accion"])
    candidato = {"tipo": "pelicula", "generos": "Ciencia ficción|Acción", "titulo": "X", "rating": 0}

    score = _score_candidato(candidato, [perfil])

    assert score == 2.0


def test_genero_no_banca_sin_tilde_penaliza_candidato_con_tilde():
    perfil = _perfil("Test", no_banca_generos=["accion"])
    candidato = {"tipo": "pelicula", "generos": "Acción|Drama", "titulo": "X", "rating": 0}

    score = _score_candidato(candidato, [perfil])

    assert score == -2.0


def test_titulo_no_banca_con_tilde_matchea_perfil_sin_tilde():
    perfil = _perfil("Test", no_banca_titulos=[ItemContenido(titulo="Amelie", tipo="pelicula")])
    candidato = {"tipo": "pelicula", "generos": "", "titulo": "Amélie", "rating": 0}

    score = _score_candidato(candidato, [perfil])

    assert score == -3.0


def test_genero_favorito_thriller_matchea_candidato_suspense():
    """Regresión: los perfiles tipean 'thriller' (cine) o 'policial' (libros), pero
    el dataset etiqueta esos mismos géneros como 'Suspense' y 'Crimen'."""
    perfil = _perfil("Test", peliculas_fav=["thriller"])
    candidato = {"tipo": "pelicula", "generos": "Suspense|Drama", "titulo": "X", "rating": 0}

    score = _score_candidato(candidato, [perfil])

    assert score == 1.0


def test_score_semantico_del_retriever_desempata_entre_candidatos_parejos():
    """Regresión: el ranking ignoraba el 'score' (distancia) que trae rag.retriever(),
    así que dos candidatos con el mismo match de género quedaban empatados aunque uno
    fuera semánticamente mucho más relevante que el otro."""
    perfil = _perfil("Test", peliculas_fav=["terror"])
    candidato_cercano = {
        "tipo": "pelicula",
        "titulo": "Cercano",
        "generos": "Terror",
        "rating": 0,
        "score": 3.0,
    }
    candidato_lejano = {
        "tipo": "pelicula",
        "titulo": "Lejano",
        "generos": "Terror",
        "rating": 0,
        "score": 9.0,
    }

    rankeados = rankear_candidatos([candidato_lejano, candidato_cercano], [perfil])

    assert rankeados[0]["titulo"] == "Cercano"


def test_rankear_candidatos_prefiere_match_real_de_genero_por_sobre_generico():
    """Regresión: 'ciencia ficcion' (perfil, sin tilde) no matcheaba 'Ciencia ficción'
    (dataset, con tilde), lo que hacia que un candidato generico ganara siempre aunque
    no tuviera nada que ver con lo que el grupo pidio."""
    fan_de_ciencia_ficcion = _perfil("Fan", peliculas_fav=["ciencia ficcion"])

    candidato_sci_fi = {
        "tipo": "pelicula",
        "titulo": "Sci-Fi Movie",
        "generos": "Ciencia ficción|Drama",
        "rating": 7.0,
    }
    candidato_generico = {
        "tipo": "pelicula",
        "titulo": "Generic Movie",
        "generos": "Comedia|Familia",
        "rating": 7.0,
    }

    rankeados = rankear_candidatos([candidato_generico, candidato_sci_fi], [fan_de_ciencia_ficcion])

    assert rankeados[0]["titulo"] == "Sci-Fi Movie"
