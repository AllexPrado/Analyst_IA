"""
Monitor de economia de tokens para o Analyst IA.
Este script monitora o impacto da filtragem rigorosa de entidades
na economia de tokens da API OpenAI.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Tratamento para matplotlib (opcional)
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("AVISO: matplotlib não está instalado. Gráficos não serão gerados.")
    print("Para instalar: pip install matplotlib numpy")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para armazenamento de relatórios
REPORT_DIR = Path("relatorios/economia_tokens")
HISTORY_FILE = REPORT_DIR / "historico_economia.json"

def calcular_tamanho_token(entidade):
    """Calcula aproximadamente o número de tokens que uma entidade consumiria."""
    if not entidade:
        return 0
    
    # Converte para JSON para estimativa realista
    texto = json.dumps(entidade)
    # Estimativa: 1 token ~= 4 caracteres
    return len(texto) // 4

def analisar_cache(cache_file_path):
    """Analisa um arquivo de cache para calcular economia de tokens."""
    try:
        if not Path(cache_file_path).exists():
            logger.error(f"Arquivo de cache não encontrado: {cache_file_path}")
            return None
            
        logger.info(f"Analisando cache: {cache_file_path}")
        
        with open(cache_file_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
        # Recupera estatísticas se disponíveis
        if "metricas_processamento" in cache:
            stats = cache["metricas_processamento"]
            logger.info(f"Estatísticas encontradas: {stats}")
            
        # Recupera entidades
        entidades = cache.get("entidades", [])
        if not entidades:
            logger.warning(f"Nenhuma entidade encontrada no cache: {cache_file_path}")
            return None
            
        # Calcula tamanho aproximado em tokens
        total_tokens = sum(calcular_tamanho_token(e) for e in entidades)
        
        resultado = {
            "arquivo": str(Path(cache_file_path).name),
            "timestamp": datetime.now().isoformat(),
            "entidades": len(entidades),
            "tokens_estimados": total_tokens,
            "tokens_por_entidade": round(total_tokens / len(entidades), 2) if entidades else 0
        }
        
        # Adiciona estatísticas do cache se disponíveis
        if "metricas_processamento" in cache:
            resultado["metricas_original"] = cache["metricas_processamento"]
            
            # Calcula economia
            if "entidades_originais" in cache["metricas_processamento"]:
                entidades_originais = cache["metricas_processamento"]["entidades_originais"]
                entidades_filtradas = len(entidades)
                
                economia_percentual = 100 - (entidades_filtradas / max(1, entidades_originais) * 100)
                resultado["economia_percentual"] = round(economia_percentual, 1)
            
        return resultado
    except Exception as e:
        logger.error(f"Erro ao analisar cache: {e}")
        import traceback
        traceback.print_exc()
        return None

def salvar_historico(dados):
    """Salva dados de economia no histórico."""
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        historico = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except:
                historico = []
        
        # Adiciona novo relatório
        historico.append(dados)
        
        # Salva histórico atualizado
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Histórico de economia atualizado: {HISTORY_FILE}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar histórico: {e}")
        return False

def gerar_grafico_economia():
    """Gera um gráfico da economia de tokens ao longo do tempo."""
    try:
        # Verifica se matplotlib está disponível
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib não disponível. Gráficos não serão gerados.")
            return False
            
        if not HISTORY_FILE.exists():
            logger.error(f"Arquivo de histórico não encontrado: {HISTORY_FILE}")
            return False
            
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            historico = json.load(f)
            
        if not historico:
            logger.warning("Histórico vazio, não é possível gerar gráfico")
            return False
            
        # Extrai dados para o gráfico
        datas = []
        economias = []
        tokens_por_entidade = []
        
        for relatorio in historico:
            data = datetime.fromisoformat(relatorio["timestamp"]).strftime("%d/%m %H:%M")
            datas.append(data)
            
            economia = relatorio.get("economia_percentual", 0)
            economias.append(economia)
            
            tpe = relatorio.get("tokens_por_entidade", 0)
            tokens_por_entidade.append(tpe)
        
        # Cria o gráfico
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Gráfico de economia percentual
        ax1.plot(datas, economias, 'o-', color='green')
        ax1.set_title('Economia de Tokens (%)')
        ax1.set_ylabel('Economia (%)')
        ax1.grid(True)
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico de tokens por entidade
        ax2.plot(datas, tokens_por_entidade, 'o-', color='blue')
        ax2.set_title('Tokens por Entidade')
        ax2.set_ylabel('Tokens')
        ax2.grid(True)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Salva o gráfico
        grafico_path = REPORT_DIR / "economia_tokens.png"
        plt.savefig(grafico_path)
        
        logger.info(f"Gráfico salvo em: {grafico_path}")
        plt.close()
        
        # Salva também em formato CSV para análises alternativas
        csv_path = REPORT_DIR / "economia_tokens.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("Data,Economia_Percentual,Tokens_Por_Entidade\n")
            for i in range(len(datas)):
                f.write(f"{datas[i]},{economias[i]},{tokens_por_entidade[i]}\n")
        
        logger.info(f"Dados CSV salvos em: {csv_path}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal."""
    try:
        logger.info("Iniciando monitor de economia de tokens")
        
        # Verifica se foi passado um arquivo específico
        if len(sys.argv) > 1:
            cache_file = sys.argv[1]
        else:
            # Procura pelo cache mais recente
            cache_files = list(Path("historico").glob("cache*.json"))
            if not cache_files:
                logger.error("Nenhum arquivo de cache encontrado!")
                return 1
                
            # Pega o cache mais recente
            cache_file = str(max(cache_files, key=lambda f: f.stat().st_mtime))
            
        # Analisa o cache
        resultado = analisar_cache(cache_file)
        
        if resultado:
            # Imprime relatório
            logger.info("\n" + "="*50)
            logger.info("RELATÓRIO DE ECONOMIA DE TOKENS")
            logger.info("="*50)
            logger.info(f"Arquivo analisado: {resultado['arquivo']}")
            logger.info(f"Entidades no cache: {resultado['entidades']}")
            logger.info(f"Tokens estimados: {resultado['tokens_estimados']}")
            logger.info(f"Tokens por entidade: {resultado['tokens_por_entidade']}")
            
            if "economia_percentual" in resultado:
                logger.info(f"Economia estimada: {resultado['economia_percentual']}%")
            
            logger.info("="*50)
            
            # Salva resultado no histórico
            salvar_historico(resultado)
            
            # Gera gráfico atualizado se matplotlib estiver disponível
            if MATPLOTLIB_AVAILABLE:
                gerar_grafico_economia()
            else:
                logger.warning("Matplotlib não disponível - gráficos não serão gerados")
                
                # Cria arquivo de texto com estatísticas
                texto_path = REPORT_DIR / "economia_tokens_stats.txt"
                with open(texto_path, "w", encoding="utf-8") as f:
                    f.write("="*50 + "\n")
                    f.write("ESTATÍSTICAS DE ECONOMIA DE TOKENS\n")
                    f.write("="*50 + "\n\n")
                    f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write(f"Arquivo analisado: {resultado['arquivo']}\n")
                    f.write(f"Entidades no cache: {resultado['entidades']}\n")
                    f.write(f"Tokens estimados: {resultado['tokens_estimados']}\n")
                    f.write(f"Tokens por entidade: {resultado['tokens_por_entidade']}\n")
                    if "economia_percentual" in resultado:
                        f.write(f"Economia estimada: {resultado['economia_percentual']}%\n")
                        
                logger.info(f"Estatísticas salvas em: {texto_path}")
            
            return 0
        else:
            logger.error("Não foi possível analisar o cache")
            return 1
    except Exception as e:
        logger.error(f"Erro no monitor de economia: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
