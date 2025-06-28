# Analyst IA - Cache System Documentation

## Overview

The cache system in Analyst IA is responsible for storing and managing entity data retrieved from New Relic across various domains. The system includes mechanisms for initial loading, periodic updates (once per day), forced refreshes, and entity consolidation. All cache operations are logged for traceability.

## Entity Consolidation

Entities in the system are collected from multiple domains (apm, browser, infra, etc.) and then consolidated into a unified list to allow cross-domain analysis. The consolidation process:

1. Collects entities from all supported domains (apm, browser, infra, db, mobile, iot, serverless, synth, ext)
2. Identifies unique entities by their GUID
3. Creates a consolidated list without duplicates
4. Stores this list in the cache under the "entidades" key
5. Persists the updated cache to disk in `historico/cache_completo.json`
6. Ensures that only entities with valid metrics are included in the consolidated list

## Cache Structure

The cache consists of:

- Domain-specific entity lists (apm, browser, infra, etc.)
- A consolidated entities list ("entidades")
- Timestamps and metadata for tracking freshness
- Historical query results (in `historico/consultas/`)
- Diagnostic logs (in `logs/analyst_ia.log`)

## Diagnostic and Maintenance

For cache diagnostics and maintenance, the following tools are available:

- `/api/cache/diagnostico` endpoint - Returns detailed cache status, including entity counts and freshness
- `/api/cache/atualizar` endpoint - Forces a cache update from New Relic
- `test_cache.py` - Runs tests to validate cache functionality and data integrity
- `corrigir_cache_consolidacao.py` - Script to fix and consolidate entities in the cache if corruption or missing data is detected
- `test_cache_status.py` - Verifies the presence and integrity of consolidated entities

## Troubleshooting

If consolidated entities are missing from the cache or the frontend is not receiving data:

1. Run the cache diagnostic endpoint (`/api/cache/diagnostico`) to check the current status and entity counts
2. Use `test_cache_status.py` to verify the presence of consolidated entities and metrics
3. If needed, execute `corrigir_cache_consolidacao.py` to rebuild the consolidated entities list and persist to disk
4. Check the logs in `logs/analyst_ia.log` for errors or warnings related to cache, entity collection, or New Relic API
5. Ensure the backend is running and the frontend is configured to use the correct backend URL (typically `http://localhost:8000`)
6. If using multiple backends, ensure only the main backend (`main.py`) is used for dashboards and entity data

All corrective actions and errors are logged in the `historico` and `logs` directories for future reference.

## Important Note

- Always verify the cache contains consolidated entities with valid metrics when implementing changes that affect data structure or entity processing.
- Never point the frontend to a backend that does not serve consolidated entities (e.g., `api_incidentes`).
- After any cache or backend update, validate the `/api/entidades` and `/api/kpis` endpoints for real data.
- If the frontend still shows no data, check the backend logs and cache diagnostics before troubleshooting the frontend code.
