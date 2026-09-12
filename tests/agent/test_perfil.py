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
