# New Relic Integration Guide for Agents

## New Relic Concepts

### 1. Entities

Entities in New Relic represent components of your architecture, such as:
- Applications (APM)
- Browser applications
- Mobile applications
- Infrastructure hosts
- Kubernetes clusters
- Databases

Each entity has:
- GUID: Globally unique identifier
- Name: Human-readable name
- Type: The kind of entity
- Domain: The product domain the entity belongs to

### 2. NRQL (New Relic Query Language)

NRQL is a SQL-like query language used to retrieve data from New Relic. Key points:

#### Basic Structure
```sql
SELECT function(attribute)
FROM dataType
WHERE condition
SINCE timeframe
UNTIL timeframe
TIMESERIES timeframe
FACET attribute
LIMIT number
```

#### Common Functions
- `count()`
- `average()`
- `sum()`
- `min()`
- `max()`
- `percentile()`
- `filter()`
- `latest()`

#### Data Types
- `Transaction`
- `TransactionError`
- `PageView`
- `SystemSample`
- `ProcessSample`
- `Metric`
- `Event`
- `Log`

#### Time Frames
- `SINCE 1 hour ago`
- `SINCE 30 minutes ago`
- `SINCE '2023-07-01 00:00:00'`
- `UNTIL now`
- `UNTIL '2023-07-02 23:59:59'`

#### Common Errors
1. **Syntax Errors**: Unexpected characters or malformed queries
2. **Type Mismatches**: Using incorrect data types
3. **Non-existent Attributes**: Referencing attributes that don't exist
4. **Time Range Issues**: Invalid time ranges or formats
5. **Quota/Limit Issues**: Exceeding query limits

## API Endpoints

### Entity API
```
GET /api/v1/entities/{guid}
```

### Metrics API
```
GET /api/v1/metrics
```

### NRQL Query API
```
POST /api/v1/nrql
```

## Query Optimization

### Best Practices
1. Use specific time ranges
2. Limit the number of results
3. Use appropriate aggregations
4. Filter data at query time
5. Avoid using `*` in SELECT statements
6. Include only necessary facets

### Common Optimizations
1. **Add Proper LIMIT**: Always include LIMIT unless you need all results
2. **Use FACET carefully**: Limit the cardinality of FACET attributes
3. **Time Window**: Use smallest necessary time window
4. **Pre-aggregation**: Pre-aggregate data when possible

## Error Handling

### Error Response Format
```json
{
  "errors": [
    {
      "message": "Error message details",
      "path": ["path", "to", "error"],
      "extensions": {
        "errorClass": "ERROR_TYPE",
        "errorCode": "CODE:1234567"
      },
      "locations": [
        {
          "line": 1,
          "column": 50
        }
      ]
    }
  ]
}
```

### Common Error Codes
- `NRDB:1102004`: NRQL Syntax Error
- `NRDB:1102002`: Unknown attribute
- `NRDB:1102003`: Invalid function usage
- `NRQL:0001`: Rate limit exceeded
- `AUTH:0001`: Authentication error

## Automated Query Correction Strategies

### Syntax Error Correction
1. Identify position of error from error message
2. Check for unbalanced quotes, parentheses
3. Validate all identifiers and keywords
4. Check for illegal characters

### Specific Error Handling
1. **Unexpected character**: Check for special characters or typos
2. **Unknown attribute**: Verify attribute names against schema
3. **Invalid function usage**: Check function signature and arguments
4. **Timestamp format**: Ensure proper format 'YYYY-MM-DD HH:MM:SS'

### Example: Fixing position-based errors
If error message states "Error at position 50, unexpected '7'":
1. Extract the query string
2. Identify character at position 50
3. Check context around that position
4. Look for number format issues, misplaced quotes, etc.
5. Apply appropriate correction based on context

## Connection Issues and Troubleshooting

### SSL Connection Errors

When working with New Relic API, you might encounter SSL connection errors, particularly when making many concurrent requests:

#### Common SSL Errors

- `SSL shutdown timed out`: Occurs when connections are closed too quickly or there are too many concurrent SSL handshakes
- `Connection lost`: Typically related to network stability or connection limit issues
- `ClientConnectionError`: Generic connection error that could be related to limits, timeouts, or network issues

#### Troubleshooting Strategies

1. **Connection Pooling**: Use connection pooling to reuse SSL connections
   ```python
   # Example with aiohttp
   connector = aiohttp.TCPConnector(ssl=False, limit=20, ttl_dns_cache=300)
   async with aiohttp.ClientSession(connector=connector) as session:
       # Make requests
   ```

2. **Rate Limiting**: Implement rate limiting to prevent too many concurrent requests
   ```python
   semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
   async with semaphore:
       # Make request
   ```

3. **Exponential Backoff**: Implement retry mechanism with exponential backoff
   ```python
   retry_count = 0
   max_retries = 3
   while retry_count < max_retries:
       try:
           # Make request
           break
       except ClientConnectionError:
           retry_count += 1
           await asyncio.sleep(2 ** retry_count)  # Exponential backoff
   ```

4. **Connection Timeout Handling**: Set appropriate timeouts
   ```python
   timeout = aiohttp.ClientTimeout(total=30, connect=10)
   async with aiohttp.ClientSession(timeout=timeout) as session:
       # Make requests
   ```

5. **SSL Context Configuration**: Use custom SSL context
   ```python
   import ssl
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ssl_context.verify_mode = ssl.CERT_NONE
   connector = aiohttp.TCPConnector(ssl=ssl_context)
   ```

6. **Connection Error Handling**: Handle connection errors gracefully
   ```python
   try:
       # Make request
   except aiohttp.ClientConnectorError as e:
       logger.warning(f"Connection error: {str(e)}")
       # Implement fallback strategy
   ```

### Request Optimization

To reduce connection issues when working with many entities:

1. **Batch Requests**: Group multiple entity queries into a single request when possible
2. **Prioritize Entities**: Process critical entities first
3. **Implement Caching**: Cache results to reduce API calls
4. **Use GraphQL**: Prefer GraphQL over REST for more efficient data retrieval
5. **Parallelize Wisely**: Balance between parallelism and not overwhelming the connection
