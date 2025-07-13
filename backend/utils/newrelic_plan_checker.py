"""
Módulo para verificar o status do plano New Relic e adaptar o comportamento do sistema.
Este módulo permite que o sistema continue funcionando com o plano gratuito do New Relic,
respeitando suas limitações e usando cache mais agressivamente para reduzir custos.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import aiohttp

# Configurar logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")
NEW_RELIC_ACCOUNT_ID = os.getenv("NEW_RELIC_ACCOUNT_ID")

# Caminho para o arquivo de cache de status do plano
PLAN_STATUS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "cache", "newrelic_plan_status.json")

# Configurações para plano gratuito
FREE_PLAN_SETTINGS = {
    "max_data_ingest_gb": 100,  # 100 GB de ingestão de dados por mês
    "max_synthetic_checks": 500,  # 500 verificações sintéticas por mês
    "max_full_users": 1,  # 1 usuário completo
    "cache_ttl_hours": 48,  # Usar cache por mais tempo para economizar chamadas de API
    "optimize_queries": True,  # Otimizar consultas para reduzir dados
    "reduce_logging": True  # Reduzir volume de logs enviados ao New Relic
}

# Configurações para planos pagos (padrão antes de detectar)
PAID_PLAN_SETTINGS = {
    "cache_ttl_hours": 24,
    "optimize_queries": False,
    "reduce_logging": False
}

class NewRelicPlanChecker:
    """Classe para verificar o status do plano New Relic e fornecer configurações apropriadas"""
    
    def __init__(self):
        self.settings = PAID_PLAN_SETTINGS.copy()  # Começa com configurações padrão
        self.is_free_plan = False
        self.last_checked = None
        self.load_cached_status()
    
    def load_cached_status(self):
        """Carrega o status do plano do cache se disponível e ainda válido"""
        try:
            if os.path.exists(PLAN_STATUS_CACHE_FILE):
                with open(PLAN_STATUS_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    
                last_checked = datetime.fromisoformat(data.get('last_checked'))
                # Considera o cache válido por 24 horas
                if datetime.now() - last_checked < timedelta(hours=24):
                    self.is_free_plan = data.get('is_free_plan', False)
                    self.settings = data.get('settings', self.settings)
                    self.last_checked = last_checked
                    logger.info(f"Carregado status do plano do cache: {'Gratuito' if self.is_free_plan else 'Pago'}")
                    return True
        except Exception as e:
            logger.warning(f"Erro ao carregar cache de status do plano: {e}")
        
        return False
    
    def save_status_to_cache(self):
        """Salva o status atual do plano no cache"""
        try:
            # Garantir que o diretório de cache existe
            os.makedirs(os.path.dirname(PLAN_STATUS_CACHE_FILE), exist_ok=True)
            
            with open(PLAN_STATUS_CACHE_FILE, 'w') as f:
                json.dump({
                    'is_free_plan': self.is_free_plan,
                    'settings': self.settings,
                    'last_checked': datetime.now().isoformat()
                }, f)
            logger.info("Status do plano New Relic salvo no cache")
        except Exception as e:
            logger.warning(f"Erro ao salvar cache de status do plano: {e}")
    
    async def check_plan_status(self):
        """Verifica o status do plano New Relic através da API"""
        if not NEW_RELIC_API_KEY or not NEW_RELIC_ACCOUNT_ID:
            logger.warning("Credenciais New Relic não configuradas. Assumindo plano gratuito.")
            self._set_free_plan()
            return
        
        # Se já verificou nas últimas 24 horas, usa o valor em cache
        if self.last_checked and (datetime.now() - self.last_checked < timedelta(hours=24)):
            return
        
        try:
            # Endpoint para verificar o plano (pode variar dependendo da API do New Relic)
            url = f"https://api.newrelic.com/v2/accounts/{NEW_RELIC_ACCOUNT_ID}"
            headers = {
                "Api-Key": NEW_RELIC_API_KEY,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    # Status 402 Payment Required indica que o plano foi rebaixado/cancelado
                    if response.status == 402:
                        logger.warning("Detectado erro 402 Payment Required. Configurando para plano gratuito.")
                        self._set_free_plan()
                    # Status 403 Forbidden pode indicar mudanças de permissão que sugerem plano gratuito
                    elif response.status == 403:
                        logger.warning("Detectado erro 403 Forbidden. Configurando para plano gratuito.")
                        self._set_free_plan()
                    elif response.status == 200:
                        # Verifica no conteúdo da resposta se há indicação de plano gratuito
                        data = await response.json()
                        plan_name = data.get('account', {}).get('subscription', {}).get('name', '').lower()
                        
                        if 'free' in plan_name:
                            logger.info(f"Plano gratuito identificado: {plan_name}")
                            self._set_free_plan()
                        else:
                            logger.info(f"Plano pago identificado: {plan_name}")
                            self.is_free_plan = False
                            self.settings = PAID_PLAN_SETTINGS.copy()
                    else:
                        # Em caso de erro não esperado, assume plano gratuito para evitar custos
                        logger.warning(f"Erro ao verificar plano: {response.status}. Assumindo plano gratuito.")
                        self._set_free_plan()
        except Exception as e:
            # Em caso de erro, presume plano gratuito para evitar custos inesperados
            logger.warning(f"Erro ao verificar plano New Relic: {e}. Assumindo plano gratuito.")
            self._set_free_plan()
        
        # Atualiza timestamp e salva no cache
        self.last_checked = datetime.now()
        self.save_status_to_cache()
    
    def _set_free_plan(self):
        """Configura as definições para plano gratuito"""
        self.is_free_plan = True
        self.settings = FREE_PLAN_SETTINGS.copy()
    
    def get_settings(self):
        """Retorna as configurações atuais baseadas no plano"""
        return self.settings
    
    def is_free(self):
        """Retorna True se estiver usando plano gratuito"""
        return self.is_free_plan


# Singleton para ser usado pelo resto da aplicação
plan_checker = NewRelicPlanChecker()

async def get_plan_settings():
    """Obtém as configurações atuais do plano, verificando o status se necessário"""
    await plan_checker.check_plan_status()
    return plan_checker.get_settings()

def is_free_plan():
    """Verifica se está usando plano gratuito (usa cache se disponível)"""
    return plan_checker.is_free()

# Função para adaptar consultas NRQL para economizar dados em plano gratuito
def optimize_nrql_query(query, is_free=None):
    """
    Otimiza uma consulta NRQL para consumir menos dados se estiver no plano gratuito
    
    Args:
        query (str): Consulta NRQL original
        is_free (bool): Força o modo gratuito se True, verifica automaticamente se None
        
    Returns:
        str: Consulta otimizada
    """
    if is_free is None:
        is_free = is_free_plan()
    
    if not is_free:
        return query
    
    # Aplicar otimizações para plano gratuito
    optimized = query
    
    # Adicionar LIMIT se não existir
    if 'LIMIT' not in optimized.upper():
        optimized = optimized + " LIMIT 100"  # Limita resultados para economizar dados
    else:
        # Reduzir LIMIT existente se for muito grande
        import re
        limit_match = re.search(r'LIMIT\s+(\d+)', optimized, re.IGNORECASE)
        if limit_match:
            limit = int(limit_match.group(1))
            if limit > 100:
                optimized = re.sub(r'LIMIT\s+\d+', f'LIMIT 100', optimized, flags=re.IGNORECASE)
    
    # Reduzir janela de tempo se for muito grande
    time_windows = {
        r'SINCE \d+ DAYS AGO': 'SINCE 1 DAY AGO',
        r'SINCE \d+ WEEKS AGO': 'SINCE 1 DAY AGO',
        r'SINCE \d+ HOURS AGO': lambda m: f"SINCE {min(24, int(m.group(1)))} HOURS AGO"
    }
    
    for pattern, replacement in time_windows.items():
        if callable(replacement):
            import re
            matches = re.search(pattern.replace(r'\d+', r'(\d+)'), optimized, re.IGNORECASE)
            if matches:
                optimized = re.sub(pattern, replacement(matches), optimized, flags=re.IGNORECASE)
        else:
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
    
    return optimized
