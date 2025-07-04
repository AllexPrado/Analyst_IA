/**
 * Utility functions to handle null/undefined data in frontend components
 * This prevents errors when trying to render charts or metrics with missing data
 */

/**
 * Safely gets a value from a nested object path
 * @param {Object} obj - The object to extract value from
 * @param {string} path - The path to the property, e.g., 'metrics.30min.apdex[0].score'
 * @param {*} defaultValue - Default value if path doesn't exist
 * @returns {*} The value at path or defaultValue if not found
 */
export function getNestedValue(obj, path, defaultValue = null) {
  if (!obj || !path) return defaultValue;
  
  const parts = path.replace(/\[(\w+)\]/g, '.$1').split('.');
  let current = obj;
  
  for (const part of parts) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return defaultValue;
    }
    current = current[part];
  }
  
  return current === undefined || current === null ? defaultValue : current;
}

/**
 * Safely formats a metric value for display
 * @param {*} value - The value to format
 * @param {string} format - Format type: 'percent', 'number', 'time', etc.
 * @param {string} units - Units to append (ms, %, etc)
 * @param {string} fallbackText - Text to display if value is null/undefined (defaults to 'Sem dados')
 * @returns {string} Formatted value or fallback if null
 */
export function formatMetricValue(value, format = 'number', units = '', fallbackText = 'Sem dados') {
  if (value === undefined || value === null || (typeof value === 'number' && isNaN(value))) {
    return fallbackText;
  }
  
  let formattedValue;
  
  switch (format) {
    case 'percent':
      formattedValue = typeof value === 'number' ? 
        `${(value * 100).toFixed(2)}%` : 
        `${value}${units || '%'}`;
      break;
      
    case 'time':
      // Format time in ms or seconds based on magnitude
      if (typeof value === 'number') {
        if (value < 1 && value > 0) {
          formattedValue = `${(value * 1000).toFixed(2)}${units || 'ms'}`;
        } else {
          formattedValue = `${value.toFixed(2)}${units || 's'}`;
        }
      } else {
        formattedValue = `${value}${units}`;
      }
      break;
      
    case 'number':
    default:
      if (typeof value === 'number') {
        // Handle different number scales
        if (value === 0) {
          formattedValue = '0';
        } else if (value < 0.01 && value > 0) {
          formattedValue = value.toExponential(2);
        } else if (value % 1 !== 0) {
          formattedValue = value.toFixed(2);
        } else if (value > 999) {
          formattedValue = value.toLocaleString();
        } else {
          formattedValue = value.toString();
        }
      } else {
        formattedValue = String(value);
      }
      
      if (units) formattedValue += units;
  }
  
  return formattedValue;
}

/**
 * Creates safe chart data by ensuring all required properties exist
 * @param {Array|null} dataArray - The data array that might be null
 * @param {Object} options - Configuration options
 * @returns {Array} Safe array for charts with fallback values
 */
export function createSafeChartData(dataArray, options = {}) {
  const { 
    defaultLength = 5,
    defaultValue = 0,
    labelKey = 'name',
    valueKey = 'value',
    defaultLabels = ['No Data']
  } = options;
  
  // If no data or empty array, return null (não retorna mais dummy data)
  if (!dataArray || (Array.isArray(dataArray) && dataArray.length === 0)) {
    return null;
  }
  
  // Data exists, ensure each item has required properties
  return dataArray.map(item => {
    if (item === null || typeof item !== 'object') {
      return { [labelKey]: 'Unknown', [valueKey]: defaultValue };
    }
    
    return {
      ...item,
      [labelKey]: item[labelKey] || 'Unnamed',
      [valueKey]: (item[valueKey] === null || item[valueKey] === undefined) 
        ? defaultValue : item[valueKey]
    };
  });
}

/**
 * Check if an entity has any real data (non-null metrics)
 * @param {Object} entity - The entity object
 * @returns {boolean} True if entity has real data
 */
export function entityHasRealData(entity) {
  if (!entity || !entity.metricas) return false;
  
  // Check for at least one period with data
  const periods = Object.keys(entity.metricas);
  if (periods.length === 0) return false;
  
  // Check each period for any real metrics
  for (const period of periods) {
    const metrics = entity.metricas[period];
    if (!metrics) continue;
    
    // Check if any metric has non-null value
    for (const metricName in metrics) {
      const metric = metrics[metricName];
      
      // Handle array metrics
      if (Array.isArray(metric) && metric.length > 0) {
        // Check if any item in array has non-null values
        for (const item of metric) {
          if (item && Object.values(item).some(val => val !== null && val !== undefined)) {
            return true;
          }
        }
      } 
      // Handle direct value metrics
      else if (metric !== null && metric !== undefined) {
        return true;
      }
    }
  }
  
  return false;
}

/**
 * Get the most recent period with data for an entity
 * @param {Object} entity - The entity object
 * @returns {Object|null} The metrics from the most recent period or null
 */
export function getMostRecentPeriod(entity) {
  if (!entity || !entity.metricas) return null;
  
  const priorityOrder = ['30min', '24h', '7d', '30d'];
  
  // First try the priority order
  for (const period of priorityOrder) {
    if (entity.metricas[period] && Object.keys(entity.metricas[period]).length > 0) {
      return entity.metricas[period];
    }
  }
  
  // If not found, return any available period
  const periods = Object.keys(entity.metricas);
  return periods.length > 0 ? entity.metricas[periods[0]] : null;
}

/**
 * Cria dados seguros para gráficos ApexCharts
 * evitando erros de propriedades undefined
 * 
 * @param {Array|null} series - Os dados de séries que podem ser nulos
 * @returns {Array} Dados seguros para ApexCharts
 */
export function createSafeApexSeries(series) {
  // Se as séries forem nulas ou vazias, retorna uma série vazia segura
  if (!series || !Array.isArray(series) || series.length === 0) {
    return [{
      name: 'Sem dados',
      data: [0]
    }];
  }

  // Valida cada série e garante que tenha estrutura correta
  return series.map(serie => {
    // Se a série for nula ou não tiver dados, cria uma série segura
    if (!serie || !serie.data) {
      return {
        name: serie?.name || 'Sem nome',
        data: [0]
      };
    }
    
    // Se data não for array, converte para array
    if (!Array.isArray(serie.data)) {
      return {
        ...serie,
        name: serie.name || 'Sem nome',
        data: [serie.data || 0]
      };
    }
    
    // Se o array estiver vazio, adiciona zero
    if (serie.data.length === 0) {
      return {
        ...serie,
        name: serie.name || 'Sem nome',
        data: [0]
      };
    }
    
    // Garante que todos os valores no array são números válidos
    const safeData = serie.data.map(value => {
      if (value === null || value === undefined || isNaN(value)) {
        return 0;
      }
      return value;
    });
    
    return {
      ...serie,
      name: serie.name || 'Sem nome',
      data: safeData
    };
  });
}

/**
 * Cria opções seguras para gráficos ApexCharts
 * evitando erros de propriedades undefined
 * 
 * @param {Object|null} options - As opções que podem ser nulas
 * @returns {Object} Opções seguras para ApexCharts
 */
export function createSafeApexOptions(options) {
  // Opções padrão seguras
  const defaultOptions = {
    chart: {
      type: 'line',
      toolbar: {
        show: false
      }
    },
    tooltip: {
      enabled: true
    },
    xaxis: {
      categories: ['Sem dados']
    }
  };
  
  // Se as opções forem nulas, retorna as opções padrão
  if (!options || typeof options !== 'object') {
    return defaultOptions;
  }
  
  // Mescla as opções fornecidas com as opções padrão
  return {
    ...defaultOptions,
    ...options,
    // Garante que chart e xaxis existam
    chart: {
      ...defaultOptions.chart,
      ...(options.chart || {})
    },
    xaxis: {
      ...defaultOptions.xaxis,
      ...(options.xaxis || {}),
      // Garante que categories existe
      categories: options.xaxis?.categories || defaultOptions.xaxis.categories
    }
  };
}

/**
 * Verifica se uma série de dados é válida para renderização em gráficos
 * @param {Array|Object} series - Série de dados para verificação
 * @returns {boolean} True se a série contém dados válidos
 */
export function isValidSeries(series) {
  // Caso não exista série ou seja falsy
  if (!series) return false;
  
  // Para array de séries (formato comum no ApexCharts)
  if (Array.isArray(series)) {
    // Verifica se o array não está vazio
    if (series.length === 0) return false;
    
    // Verifica se pelo menos uma série tem dados válidos
    return series.some(serie => {
      if (!serie || !serie.data) return false;
      if (Array.isArray(serie.data)) {
        return serie.data.length > 0 && serie.data.some(point => point !== null && point !== undefined);
      }
      return false;
    });
  }
  
  // Para objetos de série única
  if (typeof series === 'object') {
    if (!series.data) return false;
    if (Array.isArray(series.data)) {
      return series.data.length > 0 && series.data.some(point => point !== null && point !== undefined);
    }
  }
  
  return false;
}

/**
 * Sanitiza série de dados para evitar valores nulos/undefined que quebram gráficos
 * @param {Array|Object} series - Série de dados para sanitização
 * @param {number|null} fallbackValue - Valor para substituir valores nulos (null para remover pontos inválidos)
 * @returns {Array|Object} Série sanitizada
 */
export function sanitizeSeries(series, fallbackValue = 0) {
  if (!series) return [];
  
  if (Array.isArray(series)) {
    return series.map(serie => ({
      ...serie,
      name: serie.name || 'Serie',
      data: sanitizeDataPoints(serie.data, fallbackValue)
    }));
  }
  
  if (typeof series === 'object') {
    return {
      ...series,
      name: series.name || 'Serie',
      data: sanitizeDataPoints(series.data, fallbackValue)
    };
  }
  
  return [];
}

/**
 * Sanitiza pontos de dados para evitar valores nulos/undefined
 * @param {Array} dataPoints - Pontos de dados a serem sanitizados
 * @param {number|null} fallbackValue - Valor para substituir valores nulos (null para remover pontos inválidos)
 * @returns {Array} Pontos de dados sanitizados
 */
function sanitizeDataPoints(dataPoints, fallbackValue) {
  if (!Array.isArray(dataPoints)) return [];
  
  if (fallbackValue === null) {
    // Remover pontos nulos
    return dataPoints.filter(point => point !== null && point !== undefined);
  }
  
  // Substituir valores nulos pelo fallback
    return dataPoints.map(point => {
      if (point === null || point === undefined || (typeof point === 'number' && isNaN(point))) {
        return fallbackValue;
      }
      return point;
    });
  }