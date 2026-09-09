# Estructuración de proyecto

Quién hace qué, en qué orden, y cómo arranca cada uno. El código base de los 5 módulos
ya está en `main` (funcional, no son cáscaras vacías) — el trabajo de cada uno es
completar/ajustar/testear su parte, no arrancar de cero. Ver el `README.md` de cada
carpeta para el detalle técnico; este documento es el mapa de quién hace qué y en qué
orden.

## Orden de arranque (por dependencias)

```
ingestion  ─┐
            ├─→  rag  ─→  agent  ─┐
prompts    ─┘                     ├─→  notebook
                                   │
perfiles (los 5, en paralelo) ────┘
```

- **Arrancan YA, en paralelo, sin esperar a nadie:** `ingestion` y `prompts` (no
  dependen de ningún otro módulo). También cada uno puede completar su
  `perfiles/<nombre>.json` desde el día 1.
- **`rag` arranca apenas exista `data/dataset.csv`.** Si `ingestion` todavía no
  terminó, puede arrancar igual: el CSV de ejemplo alcanza para probar que el
  pipeline de embeddings + ChromaDB funciona, y después solo hay que re-correr
  `python -m rag.vectorstore` cuando el dataset real esté listo.
- **`agent` arranca apenas `rag.retriever` responda algo** (real o con el dataset
  chico de prueba). No necesita esperar a que `ingestion` esté 100% terminado.
- **`notebook` arranca al final**, cuando `ingestion`, `rag`, `agent` y `prompts` ya
  estén mergeados a `main`. Es el único módulo real mente secuencial.

Conclusión práctica: todos pueden arrancar en paralelo desde el día 1. El único que
tiene que esperar de verdad es `notebook`.

## División de tareas

| Módulo | Rama | Qué hace | Depende de | Quién |
|---|---|---|---|---|
| `ingestion/` | `feature/ingestion` | Traer datos de TMDB + Google Books, limpiar, generar `data/dataset.csv` | nada | LucasViguera |
| `rag/` | `feature/rag` | Embeddings + ChromaDB, función `retriever(query, k)` | `data/dataset.csv` (real o de prueba) | rafatrucco |
| `agent/` | `feature/agent` | Cruzar los 5 perfiles, armar criterio de búsqueda, rankear candidatos | `rag.retriever` | JuanBona |
| `prompts/` | `feature/prompts` | Personalidad "canchero argentino", iterar tono | nada | marcosberruhet |
| `notebook/` | `feature/notebook` | Integrar todo en el notebook final de Colab | los 4 anteriores en `main` | BrunoNeirotti |

Asignación provisoria (se puede reacomodar si a alguien le cierra más otro módulo,
avisen en el grupo). Los 5 completan además su propio `perfiles/<nombre>.json`.

## Checklist por módulo

### `ingestion/` (`docs/DISENO.md` tiene el detalle del esquema)
- [ ] Conseguir API key de TMDB y cargarla en `.env`
- [ ] Correr `python -m ingestion.build_dataset` y revisar que el CSV tenga datos
      razonables (sinopsis no vacías, géneros bien mapeados)
- [ ] Ajustar `--paginas-tmdb` / `--resultados-libros` según cuántos ítems quieran en
      el dataset final
- [ ] Revisar `ingestion/clean.py` si aparecen filas raras (sinopsis cortadas, años
      mal parseados, etc.)
- [ ] Commitear `data/dataset.csv` final a `main` (vía PR) para que el resto no
      necesite las API keys

### `rag/`
- [ ] Correr `python -m rag.vectorstore` contra el dataset real
- [ ] Probar `retriever()` con 4-5 queries de ejemplo (géneros, mezclas
      película/libro) y confirmar que los resultados tienen sentido
- [ ] Si la calidad no convence, evaluar cambiar `EMBEDDINGS_MODEL` en `.env` (ver
      trade-off de embeddings en `docs/DISENO.md`)

### `agent/`
- [ ] Probar `cargar_todos_los_perfiles()` con los 5 perfiles reales ya cargados
- [ ] Correr `recomendar_grupal()` end-to-end y revisar que la recomendación tenga
      en cuenta a los 5
- [ ] Ajustar los pesos de `agent/ranking.py` (`PESO_GENERO_FAVORITO`, etc.) si el
      ranking no refleja bien los gustos del grupo
- [ ] Revisar `construir_criterio_busqueda()` en `agent/mediador.py` si el retriever
      trae candidatos poco relacionados

### `prompts/`
- [ ] Generar 5-10 respuestas con distintos perfiles/candidatos
- [ ] Comparar contra el checklist de `prompts/ejemplos_tono.md`
- [ ] Iterar `SYSTEM_PROMPT` hasta que el tono sea consistente (ni acartonado ni
      forzado)

### `notebook/`
- [ ] Confirmar que `ingestion`, `rag`, `agent`, `prompts` ya están en `main`
- [ ] Completar la sección 6 (casos de prueba) con 2-3 corridas reales para mostrar
      en la defensa oral
- [ ] Correr la notebook completa en Colab de punta a punta antes de la entrega

## Cómo arrancar (todos)

```bash
git clone https://github.com/JuanBona/EntregaTPI_IA.git
cd EntregaTPI_IA
git checkout feature/<tu-modulo>
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # completar con las keys que necesite tu módulo
```

## Flujo de git (recordatorio)

`main` está protegida: PR + 1 review antes de mergear, sin push directo. Trabajás en
tu rama `feature/<modulo>`, cuando esté lista abrís PR contra `main`, alguien del
equipo la revisa y aprueba, se mergea. Como cada rama toca una carpeta distinta, no
debería haber conflictos.

## Contacto entre módulos

Si necesitás cambiar la forma de los datos que le pasás a otro módulo (por ejemplo,
agregar una columna al CSV, o cambiar qué devuelve `retriever()`), avisá antes en el
grupo — los "contratos" entre módulos están documentados en el README de cada carpeta,
bajo la sección "Contrato con...".
