# perfiles/

Cada integrante copia `ejemplo_perfil.json` a `perfiles/<tu_nombre>.json` y completa sus
gustos. `agent/mediador.py` carga automáticamente **todos** los `.json` de esta carpeta
(menos `ejemplo_perfil.json`), así que no hace falta tocar código para agregar tu perfil.

## Campos

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `nombre` | string | sí | |
| `generos_favoritos.peliculas` | lista de strings | no | géneros en minúscula |
| `generos_favoritos.libros` | lista de strings | no | |
| `contenido_favorito` | lista de `{titulo, tipo?}` | no | `tipo` es `"pelicula"`, `"libro"` o se omite si no lo sabés |
| `no_banca.generos` | lista de strings | no | géneros que evitar |
| `no_banca.titulos` | lista de `{titulo, tipo?}` | no | títulos puntuales que no le gustaron |
| `notas_libres` | string | no | cualquier cosa en texto libre que quieras que el agente tenga en cuenta |

Los títulos van **en el idioma en que los conocés** (ej. "Prisoners", no hace falta
traducir a "Prisioneros") — el matching contra las fuentes de datos no asume un idioma.

Validá tu JSON antes de commitear con:

```bash
python -c "from agent.perfil import cargar_perfil; print(cargar_perfil('perfiles/tu_nombre.json'))"
```
