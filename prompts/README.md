# prompts/

Personalidad del agente ("canchero argentino") separada del resto de la lógica para
poder iterar el tono sin tocar `/agent`.

## Archivos

- `system_prompt.py` — `SYSTEM_PROMPT` (constante) + `build_user_prompt(...)`, usados
  por `agent/mediador.py` al llamar al LLM.
- `ejemplos_tono.md` — ejemplos de tono "malo" vs "bueno" y un checklist para revisar
  respuestas generadas. Usalo para iterar el prompt a mano antes de tocar el código.

## Iterar el tono

1. Ajustar `SYSTEM_PROMPT` en `system_prompt.py`.
2. Correr el agente con un caso de prueba (ver `/agent/README.md`).
3. Comparar la salida contra el checklist de `ejemplos_tono.md`.
4. Repetir.
