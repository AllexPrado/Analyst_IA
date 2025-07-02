# Cache Structure and Entity Analysis Report

## Overview

This report presents an analysis of the `cache.json` file in the Analyst_IA project, which stores various entities and metrics collected from New Relic.

## Cache Summary

- **Total Entities**: 16
- **Last Update Timestamp**: 2025-06-23T12:56:47.563735

## Entity Distribution by Domain

| Domain     | Entity Count |
|------------|-------------|
| apm        | 9           |
| browser    | 5           |
| infra      | 2           |
| db         | 0           |
| mobile     | 0           |
| iot        | 0           |
| serverless | 0           |
| synth      | 0           |
| ext        | 0           |
| alertas    | 0           |

## Entity Details

### APM (9 entities)
The APM domain contains 9 entities representing various applications monitored in New Relic. These applications include:

1. Api Sites (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTY5MTQ4NDYx)
2. Fastview Legado (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NDkzNjIzNjQy)
3. Jobs Fastview (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTczMzg1MTg0)
4. Laravel Fastview (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTcxNTMyNTMz)
5. Laravel Madnezz (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTMzNDU3NTA5)
6. Laravel Malltech (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTc3OTE5NjE2)
7. Madnezz V3 (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTkwNzU1NjAy)
8. Malltech Legado (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTIzMDc1MTU4)
9. Uploads Madnezz PHP (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTY5MjY5NTMwMw)

### BROWSER (5 entities)
The BROWSER domain contains 5 entities representing various browser applications monitored in New Relic:

1. Api Sites (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1Njk0MA)
2. Fastview Legado (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1OTQ0Mw)
3. Madnezz V3 (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTM4MTU5Nw)
4. Malltech Legado (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1OTQwMw)
5. React (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1NjU3MA)

### INFRA (2 entities)
The INFRA domain contains 2 entities representing infrastructure components monitored in New Relic:

1. madnezz-mssql-database (GUID: Mzg4MjgyMHxJTkZSQXxOQXw1MDE3MjQzMzE0NDIxNTcwMzEz)
2. Websites (GUID: Mzg4MjgyMHxJTkZSQXxOQXwtMzQyOTI2MzY1MTE4NjYyMDc3NA)

## Cache Structure

The cache file is structured as a JSON object with the following top-level keys:
- `apm`: Array of APM application entities
- `browser`: Array of Browser application entities
- `infra`: Array of Infrastructure entities
- `db`: Array of Database entities (currently empty)
- `mobile`: Array of Mobile application entities (currently empty)
- `iot`: Array of IoT entities (currently empty)
- `serverless`: Array of Serverless entities (currently empty)
- `synth`: Array of Synthetic monitoring entities (currently empty)
- `ext`: Array of Extension entities (currently empty)
- `alertas`: Array of Alert entities (currently empty)
- `timestamp`: ISO timestamp indicating when the cache was last updated

## Entity Structure

Each entity in the cache typically contains the following fields:
- `name`: The name of the entity
- `guid`: A unique identifier for the entity in New Relic
- `metricas`: An object containing various metrics collected for the entity

For APM entities, metrics may include:
- apdex
- response_time
- error_rate
- throughput
- recent_errors
- database_time
- top_endpoints

For BROWSER entities, metrics may include:
- page_load_time
- ajax_response_time
- ajax_error_rate
- js_errors
- top_pages

For INFRA entities, metrics may include:
- cpu_usage
- memory_usage
- disk_usage
- disk_io
- network_io

## Cache Management

The Analyst_IA project includes several modules for cache management:

1. `cache_maintenance.py`: Main script for testing, maintaining, and fixing the cache system
2. `utils/cache.py`: Core cache operations (get, update, load, save)
3. `utils/cache_advanced.py`: Advanced cache operations
4. `utils/cache_collector.py`: Collects entity data from New Relic
5. `utils/cache_initializer.py`: Initializes and validates the cache
6. `utils/cache_integration.py`: Integrates cache with other system components

## Conclusion

The cache system in Analyst_IA currently contains 16 entities across three domains (APM, BROWSER, and INFRA). The cache is well-structured with a consistent format for each entity type and includes comprehensive metrics for each entity. The system includes robust tools for cache management, including initialization, validation, and maintenance.
