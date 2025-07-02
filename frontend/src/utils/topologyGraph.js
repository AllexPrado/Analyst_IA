/**
 * Correções para os erros no componente InfraAvancada.vue
 * Este script adiciona um unmounted hook para limpar os event listeners e corrigir erros de referência nula
 * que ocorrem durante a renderização do componente.
 */

import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as d3 from 'd3';

/**
 * Cria e gerencia um gráfico de topologia D3 com ciclo de vida correto do Vue
 * @param {Ref} container - Ref para o elemento DOM onde o gráfico será renderizado
 * @param {Ref} data - Ref para os dados de topologia
 * @param {Ref} isActive - Ref para indicar se a aba está ativa
 * @returns {Object} - Funções para gerenciar o gráfico
 */
export function useTopologyGraph(container, data, isActive) {
  // Estado local
  let simulation = null;
  let resizeListener = null;
  
  // Função para limpar recursos
  const cleanup = () => {
    if (simulation) {
      simulation.stop();
      simulation = null;
    }
    
    if (resizeListener) {
      window.removeEventListener('resize', resizeListener);
      resizeListener = null;
    }
    
    // Limpar SVG se existir
    if (container.value) {
      d3.select(container.value).selectAll('*').remove();
    }
  };
  
  // Função para renderizar o gráfico
  const renderGraph = () => {
    // Garantir que temos o container e dados
    if (!container.value || !data.value?.nodes || !data.value?.links) {
      return;
    }
    
    // Limpar renderização anterior
    cleanup();
    
    // Obter dimensões do container
    const width = container.value.clientWidth || 800;
    const height = container.value.clientHeight || 600;
    
    // Criar SVG
    const svg = d3.select(container.value)
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
    // Criar grupo para o conteúdo
    const g = svg.append('g')
      .attr('class', 'topology-graph');
    
    // Preparar dados
    const nodes = data.value.nodes || [];
    const links = data.value.links || [];
    
    // Criar simulação de força
    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60));
    
    // Adicionar linhas para relações
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', d => d.errors > 0 ? '#f87171' : '#6b7280')
      .attr('stroke-width', d => Math.max(1, Math.min(5, Math.log(d.calls_per_minute || 1) / 2)))
      .attr('stroke-opacity', 0.6);
    
    // Adicionar setas direcionais
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .enter().append('marker')
      .attr('id', d => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', '#6b7280')
      .attr('d', 'M0,-5L10,0L0,5');
    
    link.attr('marker-end', 'url(#end)');
    
    // Função para determinar cor do nó
    const getNodeColor = (status) => {
      status = (status || '').toLowerCase();
      if (status === 'healthy') return '#10b981';
      if (status === 'degraded') return '#f59e0b';
      return '#ef4444';
    };
    
    // Criar grupos para cada nó
    const nodeGroups = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g');
    
    // Adicionar círculos para nós
    nodeGroups.append('circle')
      .attr('r', 25)
      .attr('fill', d => getNodeColor(d.status))
      .attr('stroke', '#1e293b')
      .attr('stroke-width', 2);
    
    // Adicionar texto
    nodeGroups.append('text')
      .text(d => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', 35)
      .attr('fill', 'white')
      .attr('font-size', '12px');
    
    // Adicionar funcionalidade de arrasto
    nodeGroups.call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));
    
    // Adicionar tooltip
    nodeGroups.append('title')
      .text(d => {
        const metrics = d.metrics || {};
        const apdex = metrics.apdex || 0;
        const respTime = metrics.response_time || 0;
        const errRate = metrics.error_rate || 0;
        
        return `${d.name}\nStatus: ${d.status || 'N/A'}\nApdex: ${apdex.toFixed(2)}\nResp Time: ${respTime.toFixed(1)}ms\nErro: ${(errRate * 100).toFixed(2)}%`;
      });
    
    // Função de atualização
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x || 0)
        .attr('y1', d => d.source.y || 0)
        .attr('x2', d => d.target.x || 0)
        .attr('y2', d => d.target.y || 0);
      
      nodeGroups.attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
    });
    
    // Funções para arrasto
    function dragstarted(event, d) {
      if (!event.active && simulation) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active && simulation) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // Configurar listener de redimensionamento
    resizeListener = () => {
      if (isActive.value && container.value) {
        renderGraph();
      }
    };
    
    window.addEventListener('resize', resizeListener);
  };
  
  // Observar mudanças nos dados e estado ativo
  watch(
    [data, isActive],
    () => {
      if (isActive.value) {
        // Pequeno delay para garantir que o DOM foi atualizado
        setTimeout(renderGraph, 100);
      }
    },
    { deep: true }
  );
  
  // Limpar recursos quando o componente for desmontado
  onUnmounted(() => {
    cleanup();
  });
  
  // Retornar API pública
  return {
    render: renderGraph,
    cleanup
  };
}
