import requests
import json
import time
from datetime import datetime
import os
import sys

# Cores para terminal
VERMELHO = '\033[91m'
VERDE = '\033[92m'
AMARELO = '\033[93m'
AZUL = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

# Configuração
BACKEND_URL = "http://localhost:8000"
CHAT_ENDPOINT = "/chat"
TIMEOUT = 30

def print_titulo(texto):
    """Imprime um título formatado"""
    print(f"\n{AZUL}{'=' * 80}{RESET}")
    print(f"{AZUL}{texto.center(80)}{RESET}")
    print(f"{AZUL}{'=' * 80}{RESET}\n")

def print_sucesso(texto):
    """Imprime mensagem de sucesso"""
    print(f"{VERDE}✓ {texto}{RESET}")

def print_erro(texto):
    """Imprime mensagem de erro"""
    print(f"{VERMELHO}✗ {texto}{RESET}")

def print_aviso(texto):
    """Imprime mensagem de aviso"""
    print(f"{AMARELO}⚠ {texto}{RESET}")

def print_info(texto):
    """Imprime mensagem informativa"""
    print(f"{AZUL}ℹ {texto}{RESET}")

def verificar_chat(pergunta):
    """Envia uma pergunta ao endpoint de chat e verifica a resposta"""
    print_info(f"Enviando pergunta: '{pergunta}'")
    
    url = f"{BACKEND_URL}{CHAT_ENDPOINT}"
    payload = {"pergunta": pergunta}
    
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_erro(f"Erro {response.status_code} ao acessar endpoint de chat")
            return False, None
        
        dados = response.json()
        return True, dados
    except Exception as e:
        print_erro(f"Erro ao chamar endpoint de chat: {str(e)}")
        return False, None

def analisar_resposta_chat(resposta):
    """Analisa a estrutura e conteúdo da resposta do chat"""
    erros = 0
    avisos = 0
    
    # Verificar estrutura básica
    if not isinstance(resposta, dict):
        print_erro("Resposta não é um objeto JSON")
        return 1, 0
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ["resposta", "status", "timestamp"]
    for campo in campos_obrigatorios:
        if campo not in resposta:
            print_erro(f"Campo obrigatório '{campo}' não encontrado na resposta")
            erros += 1
        elif resposta[campo] is None or resposta[campo] == "":
            print_aviso(f"Campo '{campo}' está vazio na resposta")
            avisos += 1
    
    # Verificar campo de contexto
    if "contexto" not in resposta:
        print_erro("Campo 'contexto' não encontrado na resposta")
        erros += 1
    elif not isinstance(resposta["contexto"], dict):
        print_erro("Campo 'contexto' não é um objeto")
        erros += 1
    else:
        contexto = resposta["contexto"]
        
        # Verificar processamento
        if "processado" not in contexto or contexto["processado"] is not True:
            print_aviso("Campo 'processado' ausente ou não é verdadeiro")
            avisos += 1
        
        # Verificar entidades no contexto
        if "entidades" not in contexto:
            print_aviso("Campo 'entidades' não encontrado no contexto")
            avisos += 1
        elif not isinstance(contexto["entidades"], list):
            print_erro("Campo 'entidades' não é uma lista")
            erros += 1
        elif len(contexto["entidades"]) == 0:
            print_aviso("Lista de entidades está vazia")
            avisos += 1
        else:
            print_sucesso(f"Encontradas {len(contexto['entidades'])} entidades no contexto")
            
            # Verificar primeira entidade
            primeira_entidade = contexto["entidades"][0]
            if not isinstance(primeira_entidade, dict):
                print_erro("Entidade não é um objeto")
                erros += 1
            elif "name" not in primeira_entidade:
                print_erro("Campo 'name' não encontrado na entidade")
                erros += 1
            elif "metricas" not in primeira_entidade:
                print_aviso("Campo 'metricas' não encontrado na entidade")
                avisos += 1
        
        # Verificar métricas no contexto
        if "metricas" not in contexto:
            print_aviso("Campo 'metricas' não encontrado no contexto")
            avisos += 1
        elif not isinstance(contexto["metricas"], dict):
            print_erro("Campo 'metricas' não é um objeto")
            erros += 1
    
    # Verificar conteúdo da resposta
    resposta_texto = resposta.get("resposta", "")
    if len(resposta_texto) < 10:
        print_aviso("Resposta muito curta")
        avisos += 1
    
    if resposta_texto.lower().startswith(("erro", "não foi possível")):
        print_aviso("Resposta indica erro ou falha no processamento")
        avisos += 1
    
    # Verificar se a resposta parece genérica
    frases_genericas = ["não sei", "não entendi", "não posso ajudar", "desculpe"]
    if any(frase in resposta_texto.lower() for frase in frases_genericas):
        print_aviso("Resposta parece genérica ou evasiva")
        avisos += 1
    
    return erros, avisos

def testar_chat_interativo():
    """Testa o chat em modo interativo"""
    print_titulo("TESTE INTERATIVO DO CHAT")
    
    perguntas_teste = [
        "Qual é o status atual do sistema?",
        "Quais são as métricas mais críticas agora?",
        "Mostre-me as entidades com mais erros",
        "Como está o desempenho do sistema?",
        "Existe algum alerta importante agora?"
    ]
    
    erros_totais = 0
    avisos_totais = 0
    resultados = []
    
    for i, pergunta in enumerate(perguntas_teste):
        print_titulo(f"TESTE {i+1}: {pergunta}")
        
        sucesso, resposta = verificar_chat(pergunta)
        if not sucesso:
            print_erro("Falha ao chamar endpoint de chat")
            erros_totais += 1
            continue
        
        print_info("Resposta recebida:")
        print(f"\n{resposta.get('resposta', 'Sem resposta')}\n")
        
        erros, avisos = analisar_resposta_chat(resposta)
        erros_totais += erros
        avisos_totais += avisos
        
        resultados.append({
            "pergunta": pergunta,
            "sucesso": sucesso,
            "erros": erros,
            "avisos": avisos,
            "timestamp": datetime.now().isoformat()
        })
        
        # Aguardar um pouco entre as chamadas
        if i < len(perguntas_teste) - 1:
            time.sleep(1)
    
    # Salvar resultados
    try:
        arquivo_resultado = "resultado_teste_chat.json"
        with open(arquivo_resultado, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "erros_totais": erros_totais,
                "avisos_totais": avisos_totais,
                "testes": resultados
            }, f, indent=2)
        print_sucesso(f"Resultados salvos em {arquivo_resultado}")
    except Exception as e:
        print_erro(f"Erro ao salvar resultados: {str(e)}")
    
    # Mostrar resumo
    print_titulo("RESUMO DO TESTE")
    if erros_totais == 0:
        print_sucesso(f"TESTE APROVADO. Todos os testes passaram com {avisos_totais} avisos.")
    else:
        print_erro(f"TESTE COM FALHAS. Foram encontrados {erros_totais} erros e {avisos_totais} avisos.")
    
    return erros_totais == 0

def main():
    """Função principal"""
    print_titulo("TESTE DE VERIFICAÇÃO DO CHAT")
    
    # Verificar se o backend está rodando
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print_erro(f"Backend retornou status code {response.status_code}")
            return False
        print_sucesso("Backend está rodando")
    except Exception as e:
        print_erro(f"Erro ao acessar backend: {str(e)}")
        return False
    
    # Executar teste interativo
    sucesso = testar_chat_interativo()
    
    return sucesso

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
