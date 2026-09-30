# prompts/

Define la personalidad y el formato de respuesta del recomendador de peliculas.

Este modulo esta separado de `agent/` para que el tono pueda iterarse sin tocar la
logica de perfiles, ranking o RAG.

## Que aporta

- Un tono argentino, distendido y natural, como si fuera un amigo.
- Una recomendacion principal clara, no una lista larga.
- Justificaciones conectadas con los gustos reales del grupo.
- Honestidad sobre posibles conflictos, por ejemplo cuando una pelicula roza algo que
  alguien "no banca".
- Una regla explicita para no inventar datos fuera de perfiles y candidatos.

## Archivos

- `system_prompt.py`: contiene `SYSTEM_PROMPT`, `get_system_prompt()` y
  `build_user_prompt(...)`, usados por `agent/mediador.py`.

## Contrato con agent/

El agente espera poder importar:

```python
from prompts.system_prompt import build_user_prompt, get_system_prompt
```

Por eso se puede cambiar el texto del prompt, pero no conviene cambiar los nombres ni
los parametros de esas funciones sin coordinar con quien trabaje en `agent/`.

## Como probar esta parte sin el resto

No hace falta tener dataset, embeddings ni API keys para revisar el texto que arma este
modulo:

```python
from prompts.system_prompt import build_user_prompt, get_system_prompt

perfiles = """
- Marcos: le gustan thriller, misterio y ciencia ficcion. No banca romance.
- Juan: le gustan drama y policial. No banca terror.
"""

candidatos_peliculas = """
- "Prisoners" (pelicula, 2013, rating 8.1): thriller dramatico sobre una investigacion
  desesperada despues de una desaparicion.
- "Arrival" (pelicula, 2016, rating 7.6): ciencia ficcion introspectiva sobre lenguaje,
  memoria y contacto extraterrestre.
"""

candidatos_libros = """
- "El nombre del viento" (libro, 2007, rating 8.9): fantasia narrada por su propio
  protagonista, sobre su ascenso a leyenda.
"""

print(get_system_prompt())
print(build_user_prompt(perfiles, candidatos_peliculas, candidatos_libros))
```

Para probar la respuesta completa hace falta que `agent/` pueda llamar al LLM.
