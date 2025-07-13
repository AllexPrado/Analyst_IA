# NRQL Error Correction Guide

## Common NRQL Errors and Solutions

### 1. Syntax Errors

#### Error: Unexpected character at position X
This error occurs when the parser encounters a character it doesn't expect in the current context.

**Example Error:**
```
"NRQL Syntax Error: Error at line 1 position 50, unexpected '7'"
```

**Common Causes and Solutions:**

1. **Unescaped quote in string**
   - Error: `SELECT * FROM Transaction WHERE name = 'User's Page'`
   - Fix: `SELECT * FROM Transaction WHERE name = 'User\'s Page'`

2. **Invalid numeric format**
   - Error: `SELECT * FROM Transaction WHERE duration > 1,000`
   - Fix: `SELECT * FROM Transaction WHERE duration > 1000`

3. **Special characters in unquoted identifiers**
   - Error: `SELECT count(*) FROM Transaction WHERE user-name = 'test'`
   - Fix: `SELECT count(*) FROM Transaction WHERE "user-name" = 'test'`

4. **Improper facet syntax**
   - Error: `SELECT count(*) FROM Transaction FACET name, FACET duration`
   - Fix: `SELECT count(*) FROM Transaction FACET name, duration`

5. **Invalid time formats**
   - Error: `SELECT * FROM Transaction SINCE '2023-07-11 24:00:00'`
   - Fix: `SELECT * FROM Transaction SINCE '2023-07-12 00:00:00'`

### 2. Semantic Errors

#### Error: Unknown attribute
This error occurs when referencing an attribute that doesn't exist in the data.

**Example Error:**
```
"NRQL Syntax Error: Unknown attribute 'responseime'"
```

**Common Causes and Solutions:**

1. **Typos in attribute names**
   - Error: `SELECT average(responseime) FROM Transaction`
   - Fix: `SELECT average(responseTime) FROM Transaction`

2. **Case sensitivity issues**
   - Error: `SELECT average(ResponseTime) FROM Transaction`
   - Fix: `SELECT average(responseTime) FROM Transaction`

3. **Using attributes from wrong data type**
   - Error: `SELECT average(duration) FROM SystemSample`
   - Fix: `SELECT average(cpuPercent) FROM SystemSample`

### 3. Function-Related Errors

#### Error: Invalid function usage
This occurs when a function is used incorrectly.

**Example Error:**
```
"NRQL Syntax Error: Function 'percentile' requires at least 2 arguments"
```

**Common Causes and Solutions:**

1. **Wrong number of arguments**
   - Error: `SELECT percentile(duration) FROM Transaction`
   - Fix: `SELECT percentile(duration, 95) FROM Transaction`

2. **Invalid argument type**
   - Error: `SELECT average('duration') FROM Transaction`
   - Fix: `SELECT average(duration) FROM Transaction`

3. **Unsupported function combination**
   - Error: `SELECT count(average(duration)) FROM Transaction`
   - Fix: `SELECT count(*) FROM Transaction`

## Automatic Error Correction Strategies

### 1. Position-Based Correction

When an error message specifies a position (like "Error at position 50"), follow these steps:

1. Extract the full NRQL query string
2. Identify the character at the specified position
3. Examine the context (5-10 characters before and after)
4. Apply appropriate fix based on common patterns:

**Example Implementation:**
```python
def correct_position_error(query, error_position):
    # Extract 10 chars before and after error position for context
    start = max(0, error_position - 10)
    end = min(len(query), error_position + 10)
    context = query[start:end]
    
    # Check for common issues
    if "," in context and any(char.isdigit() for char in context):
        # Likely a numeric formatting issue
        corrected = query[:start] + context.replace(",", "") + query[end:]
        return corrected
    
    # More pattern checks here...
    
    return None  # No automatic correction found
```

### 2. Pattern-Based Correction

For well-known error patterns, create a lookup of regex patterns and their corrections:

**Example Implementation:**
```python
correction_patterns = [
    {
        "pattern": r"SELECT\s+\w+\(\s*'(\w+)'\s*\)",
        "replacement": r"SELECT \1(\2)",
        "description": "Remove quotes from attribute names in functions"
    },
    {
        "pattern": r"FACET\s+(\w+)\s*,\s*FACET\s+(\w+)",
        "replacement": r"FACET \1, \2",
        "description": "Fix multiple FACET keywords"
    }
]

def apply_pattern_corrections(query):
    for pattern in correction_patterns:
        if re.search(pattern["pattern"], query):
            corrected = re.sub(pattern["pattern"], pattern["replacement"], query)
            return corrected, pattern["description"]
    
    return None, None
```

### 3. Entity-Specific Attribute Validation

Maintain a registry of valid attributes for each entity type:

```python
entity_attributes = {
    "Transaction": ["duration", "name", "appName", "httpResponseCode", "apdexPerfZone"],
    "SystemSample": ["cpuPercent", "memoryUsedBytes", "diskUsedPercent"],
    # More entity types...
}

def validate_attributes(query, entity_type):
    # Extract all referenced attributes
    attribute_pattern = r"(\w+)\s*\("
    attributes = re.findall(attribute_pattern, query)
    
    # Check if attributes are valid for this entity type
    invalid_attrs = [attr for attr in attributes if attr not in entity_attributes[entity_type]]
    
    # Suggest corrections
    corrections = []
    for attr in invalid_attrs:
        # Find closest match
        closest = difflib.get_close_matches(attr, entity_attributes[entity_type], n=1)
        if closest:
            corrections.append((attr, closest[0]))
    
    return corrections
```

## Implementation in Agno AI System

### Integration with Playbook Engine

Create a dedicated playbook for NRQL correction:

```python
{
    "metadata": {
        "name": "corrigir_consulta_nrql",
        "description": "Corrige erros em consultas NRQL",
        "version": "1.0.0",
        "tags": ["nrql", "correção", "new relic"]
    },
    "inputs": {
        "required": ["consulta", "mensagem_erro"]
    },
    "steps": [
        {
            "name": "parse_error",
            "action": "analisar_erro_nrql",
            "inputs": {
                "mensagem": "{{inputs.mensagem_erro}}"
            },
            "output_var": "erro_detalhado"
        },
        {
            "name": "position_correction",
            "action": "corrigir_por_posicao",
            "inputs": {
                "consulta": "{{inputs.consulta}}",
                "posicao": "{{steps.parse_error.output.position}}",
                "caracter": "{{steps.parse_error.output.unexpected_char}}"
            },
            "output_var": "correcao_posicao",
            "conditional": "{{steps.parse_error.output.has_position}}"
        },
        {
            "name": "pattern_correction",
            "action": "corrigir_por_padrao",
            "inputs": {
                "consulta": "{{inputs.consulta}}",
                "tipo_erro": "{{steps.parse_error.output.error_type}}"
            },
            "output_var": "correcao_padrao",
            "conditional": "{{!steps.position_correction.success}}"
        },
        {
            "name": "validate_correction",
            "action": "validar_consulta_nrql",
            "inputs": {
                "consulta": "{{steps.position_correction.success ? steps.position_correction.output : steps.pattern_correction.output}}"
            },
            "output_var": "validacao"
        }
    ],
    "outputs": {
        "success": "{{steps.validate_correction.success}}",
        "consulta_original": "{{inputs.consulta}}",
        "consulta_corrigida": "{{steps.validate_correction.output.consulta}}",
        "confianca": "{{steps.validate_correction.output.confidence}}",
        "explicacao": "{{steps.validate_correction.output.explanation}}"
    }
}
```

### Learning Loop

Implement a feedback mechanism to improve correction accuracy:

1. **Record corrections**: Store each correction attempt and its outcome
2. **User validation**: Allow users to confirm if automatic corrections are correct
3. **Pattern extraction**: Analyze successful corrections to identify new patterns
4. **Model refinement**: Periodically update the correction model with new patterns

This creates a virtuous cycle where the NRQL correction system becomes more accurate over time.
