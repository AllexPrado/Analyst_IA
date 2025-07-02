# Cache Entity Analysis - Final Report

## Executive Summary

This report provides a comprehensive analysis of the cache structure in the Analyst_IA project, with a focus on determining the exact count of entities in the cache.

**Key Findings:**
- Total entities in cache: **16**
- Entity distribution: 9 APM entities, 5 Browser entities, 2 Infrastructure entities
- The cache structure is well-organized with separate sections for different entity types
- The cache was last updated on: 2025-06-23T12:56:47.563735

## Cache Structure

The `cache.json` file is structured as a JSON object with the following organization:

```
cache.json
├── apm: Array[9]
│   └── Each entity contains: name, guid, metricas
├── browser: Array[5]
│   └── Each entity contains: name, guid, metricas
├── infra: Array[2]
│   └── Each entity contains: name, guid, metricas
├── db: Array[0]
├── mobile: Array[0]
├── iot: Array[0]
├── serverless: Array[0]
├── synth: Array[0]
├── ext: Array[0]
├── alertas: Array[0]
└── timestamp: String (ISO datetime)
```

## Entity Distribution

The cache contains a total of **16 entities** distributed across 3 domains:

| Domain   | Count | Percentage |
|----------|-------|------------|
| APM      | 9     | 56.3%      |
| Browser  | 5     | 31.2%      |
| Infra    | 2     | 12.5%      |
| Others   | 0     | 0%         |
| **Total**| **16**| **100%**   |

## Detailed Entity List

### APM Entities (9)
1. Api Sites (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTY5MTQ4NDYx)
2. Fastview Legado (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NDkzNjIzNjQy)
3. Jobs Fastview (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTczMzg1MTg0)
4. Laravel Fastview (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTcxNTMyNTMz)
5. Laravel Madnezz (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTMzNDU3NTA5)
6. Laravel Malltech (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTc3OTE5NjE2)
7. Madnezz V3 (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTkwNzU1NjAy)
8. Malltech Legado (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTIzMDc1MTU4)
9. Uploads Madnezz PHP (GUID: Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTY5MjY5NTMwMw)

### BROWSER Entities (5)
1. Api Sites (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1Njk0MA)
2. Fastview Legado (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1OTQ0Mw)
3. Madnezz V3 (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTM4MTU5Nw)
4. Malltech Legado (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1OTQwMw)
5. React (GUID: Mzg4MjgyMHxCUk9XU0VSfEFQUExJQ0FUSU9OfDYwMTU1NjU3MA)

### INFRA Entities (2)
1. madnezz-mssql-database (GUID: Mzg4MjgyMHxJTkZSQXxOQXw1MDE3MjQzMzE0NDIxNTcwMzEz)
2. Websites (GUID: Mzg4MjgyMHxJTkZSQXxOQXwtMzQyOTI2MzY1MTE4NjYyMDc3NA)

## Entity Structure

Each entity in the cache follows a consistent structure:

```json
{
  "name": "Entity Name",
  "guid": "Unique New Relic Entity GUID",
  "metricas": {
    "metric1": value1,
    "metric2": value2,
    ...
  }
}
```

The specific metrics collected depend on the entity type:

- **APM Entities**: apdex, response_time, error_rate, throughput, recent_errors, database_time, top_endpoints
- **BROWSER Entities**: page_load_time, ajax_response_time, ajax_error_rate, js_errors, top_pages
- **INFRA Entities**: cpu_usage, memory_usage, disk_usage, disk_io, network_io

## Cache Management System

The project includes a comprehensive cache management system with several components:

1. **Cache Maintenance (`cache_maintenance.py`)**: Main script for testing, maintaining, and fixing the cache system
2. **Core Cache Operations (`utils/cache.py`)**: Basic cache operations like get, update, load, save
3. **Advanced Cache Operations (`utils/cache_advanced.py`)**: More complex cache operations
4. **Cache Collection (`utils/cache_collector.py`)**: Collects entity data from New Relic
5. **Cache Initialization (`utils/cache_initializer.py`)**: Initializes and validates the cache
6. **Cache Integration (`utils/cache_integration.py`)**: Integrates cache with other system components

## Conclusion

The cache system in the Analyst_IA project is well-structured and currently contains 16 entities distributed across three domains (APM, BROWSER, and INFRA). The entities represent various applications, websites, and infrastructure components being monitored in New Relic. The cache system includes comprehensive tools for management, initialization, validation, and maintenance.

---

*This analysis was generated on: ${new Date().toISOString().split('T')[0]}*
