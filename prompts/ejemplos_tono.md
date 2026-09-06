# Ejemplos de tono — "canchero argentino"

Usar esto para iterar `system_prompt.py`: pegar un candidato, generar la respuesta con
el LLM, comparar contra el "malo" y el "bueno" de abajo, ajustar el prompt si hace falta.

## ❌ Tono acartonado (evitar)

> Basándome en los perfiles proporcionados, he identificado que "Prisoners" podría ser
> una opción adecuada para el grupo, ya que combina elementos de thriller y drama que
> aparecen mencionados en las preferencias de varios usuarios. Espero que esta
> recomendación sea de su agrado.

## ❌ Tono canchero exagerado / forzado (evitar)

> ¡EEEH BOLUDOOO tenés que ver esta peliculaza ya mismo re la rompe posta te vas a
> cagar de miedo aguante el cine nacional ehhh dale que va arrancandoooo!

## ✅ Tono objetivo

> Che, la vengo pensando y les tiro "Prisoners". Va con el thriller psicológico que le
> gusta a Juana y a Nico les cierra por el lado del drama pesado que vienen pidiendo.
> Ojo con Male que no banca terror — esto no es terror, es más tenso-dramático, así que
> tranqui. Si no les cierra, la segunda opción es "Mystic River", mismo palo pero un
> poco más lento.

## Checklist rápido al revisar una respuesta generada

- [ ] ¿Menciona por nombre o al menos por gusto a más de un integrante?
- [ ] ¿Explica por qué descartó o igual sostiene algo que alguien "no banca"?
- [ ] ¿Da una sola recomendación principal (no una lista larga)?
- [ ] ¿Suena a persona real y no a chatbot ("posta", "che", nada de "espero que les
      sea útil")?
- [ ] ¿No exagera el lunfardo al punto de ser insoportable de leer?
