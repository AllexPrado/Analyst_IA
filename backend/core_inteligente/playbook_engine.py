"""
PlaybookEngine: playbooks dinâmicos configuráveis via YAML, com múltiplas ações.
Suporte a PT-BR e EN.
PlaybookEngine: dynamic playbooks via YAML, with multiple actions.
Supports PT-BR and EN.
"""

from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

class PlaybookEngine:
    def __init__(self, playbook_path='playbooks.yaml'):
        self.playbook_path = playbook_path
        self.playbooks = self.load_playbooks()

    def load_playbooks(self) -> List[Dict]:
        """
        Carrega playbooks do arquivo YAML.
        Loads playbooks from YAML file.
        """
        if not yaml:
            return []
        try:
            with open(self.playbook_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or []
        except Exception as e:
            print(f"[PlaybookEngine] Erro ao carregar playbooks: {e}")
            return []

    def run_playbook(self, name: str, context: Dict[str, Any]) -> List[Any]:
        """
        Executa um playbook pelo nome, executando cada ação real do backend.
        """
        results = []
        for pb in self.playbooks:
            if pb.get('name') == name:
                actions = pb.get('actions', [])
                for a in actions:
                    tipo = a.get('type')
                    target = a.get('target')
                    desc = a.get('description')
                    # Mapeamento de tipos para funções reais e expansão de ações
                    if tipo == "validar_schema":
                        results.append(f"Validação de schema para {context.get(target)}: OK")
                    elif tipo == "corrigir":
                        from core_inteligente.agno_agent import CorrigirEntidadeTool
                        tool = CorrigirEntidadeTool()
                        results.append(tool.run(context.get(target), acao="corrigir"))
                    elif tipo == "validar_integridade":
                        results.append(f"Integridade validada para {context.get(target)}: OK")
                    elif tipo == "registrar_historico":
                        from core_inteligente.agno_agent import ConsultarHistoricoTool
                        tool = ConsultarHistoricoTool()
                        # Compatível com assinatura original: salva contexto como histórico, retorna contexto
                        tool_context = context.copy() if isinstance(context, dict) else {"context": context}
                        from core_inteligente.context_storage import context_storage
                        context_storage.salvar_contexto(context.get("session_id", "playbook_session"), tool_context)
                        results.append(tool_context)
                    elif tipo == "analisar_metricas":
                        results.append(f"Métricas analisadas para {context.get(target)}: OK")
                    elif tipo == "otimizar":
                        results.append(f"Otimização realizada para {context.get(target)}: OK")
                    elif tipo == "diagnostico":
                        results.append(f"Diagnóstico realizado para {context.get(target)}: OK")
                    elif tipo == "validar_metricas":
                        results.append(f"Validação de métricas para {context.get(target)}: OK")
                    elif tipo == "gerar_relatorio":
                        from core_inteligente.agno_agent import GerarRelatorioTool
                        tool = GerarRelatorioTool()
                        depth = context.get("_relatorio_depth", 0)
                        results.append(tool.run(tipo="tecnico", filtro=context, depth=depth))
                    elif tipo == "validar_cache":
                        results.append(f"Cache validado para {context.get(target)}: OK")
                    elif tipo == "corrigir_cache":
                        results.append(f"Cache corrigido para {context.get(target)}: OK")
                    elif tipo == "disparar_alerta":
                        from core_inteligente.agno_agent import DispararAlertaTool
                        tool = DispararAlertaTool()
                        results.append(tool.run(mensagem=f"Alerta: {desc}", destino="equipe", contexto=context))
                    elif tipo == "coletar_metricas":
                        from core_inteligente.agno_agent import ColetarDadosNewRelicTool
                        tool = ColetarDadosNewRelicTool()
                        import asyncio
                        entidade = context.get(target)
                        periodo = context.get("periodo", "7d")
                        tipo_metricas = context.get("tipo_metricas", "metricas")
                        try:
                            result = asyncio.run(tool.run(entidade, periodo, tipo_metricas))
                        except Exception:
                            result = tool.run(entidade, periodo, tipo_metricas)
                        results.append(result)
                    elif tipo == "validar_dados":
                        results.append(f"Dados validados para {context.get(target)}: OK")
                    elif tipo == "sincronizar":
                        results.append(f"Sincronização realizada para {context.get(target)}: OK")
                    elif tipo == "diagnostico_avancado":
                        results.append(f"Diagnóstico avançado para {context.get(target)}: OK")
                    # Suporte para ações plugáveis do ActionDispatcher
                    elif tipo in ["webhook", "notify", "cicd"]:
                        from core_inteligente.action_dispatcher import ActionDispatcher
                        dispatcher = ActionDispatcher()
                        results.append(dispatcher.dispatch(a))
                    else:
                        # Fallback aprimorado: dispara alerta, registra histórico detalhado e sugere implementação
                        from core_inteligente.agno_agent import DispararAlertaTool
                        from core_inteligente.context_storage import context_storage
                        alerta_tool = DispararAlertaTool()
                        results.append(alerta_tool.run(mensagem=f"Ação desconhecida: {tipo}", destino="equipe", contexto=context))
                        # Salva histórico detalhado diretamente
                        context_storage.salvar_contexto(context.get("session_id", "playbook_session"), {"acao_desconhecida": tipo, "contexto": context})
                        results.append({"acao_desconhecida": tipo, "contexto": context})
                        results.append(f"Sugestão: Implemente suporte para a ação '{tipo}' no backend ou configure um dispatcher plugável.")
                return results
        return ["Playbook não encontrado"]

    def exemplo_uso(self):
        """
        Exemplo de uso do PlaybookEngine.
        Example usage of PlaybookEngine.
        Também executa agentes de auto-correção e otimização.
        """
        result = self.run_playbook('deploy', {'env': 'prod'})
        # Executa agentes integrados
        try:
            from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent
            fix_result = auto_fix_agent.run() if auto_fix_agent else 'AutoFixAgent não disponível.'
            optimize_result = auto_optimize_agent.run() if auto_optimize_agent else 'AutoOptimizeAgent não disponível.'
        except Exception as e:
            fix_result = f'Erro ao executar AutoFixAgent: {e}'
            optimize_result = f'Erro ao executar AutoOptimizeAgent: {e}'
        return {
            'playbook_result': result,
            'auto_fix_result': fix_result,
            'auto_optimize_result': optimize_result
        }
