/**
 * Componente para corrigir os erros de renderização no gráfico de topologia
 * Este hook gerencia o ciclo de vida do componente D3 para evitar vazamentos de memória
 * e erros de referência nula quando o componente é desmontado.
 */

import { ref, onMounted, onBeforeUnmount, onActivated, onDeactivated } from 'vue';
import * as d3 from 'd3';

/**
 * Hook para gerenciar o ciclo de vida de um gráfico D3 de topologia
 * @param {Object} options - Opções de configuração
 * @returns {Object} - API para gerenciar o gráfico
 */
export function useTopologyGraph(options = {}) {
  const {
    container = null,
    data = null,
    width = 800,
    height = 600,
    nodeRadius = 12,
    linkDistance = 120,
    chargeStrength = -300,
    colorMapping = {
      "service": "#4299E1",
      "database": "#F6AD55",
      "api": "#68D391",
      "web": "#9F7AEA",
      "default": "#CBD5E0"
    }
  } = options;

  // Estado local
  const isInitialized = ref(false);
  const svg = ref(null);
  const simulation = ref(null);
  const tooltip = ref(null);
  
  // Objetos de referência para D3
  let nodes = [];
  let links = [];
  let nodeElements = null;
  let linkElements = null;
  let labelElements = null;
  
  // Limpar tudo quando o componente é desmontado
  const cleanup = () => {
    if (simulation.value) {
      simulation.value.stop();
      simulation.value = null;
    }
    
    if (svg.value) {
      // Remover todos os event listeners
      d3.select(svg.value)
        .selectAll('*')
        .on('mouseover', null)
        .on('mouseout', null)
        .on('click', null)
        .on('drag', null);
        
      // Limpar SVG
      d3.select(svg.value).selectAll('*').remove();
    }
    
    if (tooltip.value) {
      d3.select(tooltip.value).remove();
      tooltip.value = null;
    }
    
    window.removeEventListener('resize', handleResize);
    isInitialized.value = false;
    
    nodes = [];
    links = [];
    nodeElements = null;
    linkElements = null;
    labelElements = null;
  };
  
  // Gerenciar redimensionamento da janela
  const handleResize = () => {
    if (container && container.value && svg.value && simulation.value) {
      const containerRect = container.value.getBoundingClientRect();
      const newWidth = containerRect.width;
      const newHeight = containerRect.height || height;
      
      // Atualizar tamanho do SVG
      d3.select(svg.value)
        .attr('width', newWidth)
        .attr('height', newHeight);
        
      // Reiniciar simulação com novas dimensões
      simulation.value
        .force('center', d3.forceCenter(newWidth / 2, newHeight / 2))
        .restart();
    }
  };
  
  // Inicializar gráfico
  const initGraph = () => {
    if (!container || !container.value || isInitialized.value) return;
    
    const containerElement = container.value;
    const containerRect = containerElement.getBoundingClientRect();
    const graphWidth = containerRect.width || width;
    const graphHeight = containerRect.height || height;
    
    // Criar SVG
    const svgElement = d3.select(containerElement)
      .append('svg')
      .attr('width', graphWidth)
      .attr('height', graphHeight)
      .attr('class', 'topology-graph');
      
    svg.value = svgElement.node();
    
    // Criar tooltip
    tooltip.value = d3.select(containerElement)
      .append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '5px 10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000);
      
    // Adicionar listener de redimensionamento
    window.addEventListener('resize', handleResize);
    
    isInitialized.value = true;
  };
  
  // Renderizar ou atualizar o gráfico
  const renderGraph = (newData) => {
    if (!container || !container.value || !newData || !newData.nodes || !newData.links) return;
    
    // Inicializar gráfico se necessário
    if (!isInitialized.value) {
      initGraph();
      if (!isInitialized.value) return; // Falha na inicialização
    }
    
    const svgElement = d3.select(svg.value);
    svgElement.selectAll('*').remove();
    
    // Preparar dados
    nodes = JSON.parse(JSON.stringify(newData.nodes));
    links = JSON.parse(JSON.stringify(newData.links));
    
    // Criar simulação
    simulation.value = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(svgElement.attr('width') / 2, svgElement.attr('height') / 2));
      
    // Criar linhas de conexão
    linkElements = svgElement.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.value || 1));
      
    // Criar nós
    nodeElements = svgElement.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', nodeRadius)
      .attr('fill', d => colorMapping[d.type] || colorMapping.default)
      .call(drag(simulation.value));
      
    // Adicionar rótulos
    labelElements = svgElement.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text(d => d.name)
      .attr('font-size', 10)
      .attr('dx', 15)
      .attr('dy', 4)
      .attr('fill', '#fff');
      
    // Adicionar interatividade
    nodeElements
      .on('mouseover', (event, d) => {
        d3.select(tooltip.value)
          .style('visibility', 'visible')
          .html(`
            <div>
              <strong>${d.name}</strong><br>
              Tipo: ${d.type}<br>
              ${d.status ? `Status: ${d.status}` : ''}
              ${d.metrics ? `<br>Métricas: ${JSON.stringify(d.metrics)}` : ''}
            </div>
          `)
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 10}px`);
      })
      .on('mouseout', () => {
        d3.select(tooltip.value)
          .style('visibility', 'hidden');
      });
      
    // Atualizar posições a cada tick
    simulation.value.on('tick', () => {
      linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
        
      nodeElements
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
        
      labelElements
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });
  };
  
  // Função para arrastar nós
  const drag = (simulation) => {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    
    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  };
  
  // Lifecycle hooks
  onMounted(() => {
    if (data && data.value) {
      renderGraph(data.value);
    }
  });
  
  onBeforeUnmount(() => {
    cleanup();
  });
  
  onActivated(() => {
    if (data && data.value && !isInitialized.value) {
      renderGraph(data.value);
    }
  });
  
  onDeactivated(() => {
    cleanup();
  });
  
  // Retornar API pública
  return {
    isInitialized,
    renderGraph,
    cleanup
  };
}

export default useTopologyGraph;
