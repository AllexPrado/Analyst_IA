#!/usr/bin/env python3
"""
Teste para verificar se o backend está retornando dados reais para o frontend
e identificar entidades com métricas nulas
"""
import requests
import json
import sys
from pprint import pprint
from collections import Counter

def test_backend_endpoints():
    """Testa os endpoints principais do backend"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/api/health",
        "/api/status", 
        "/api/diagnostico",
        "/api/chat",
        "/api/entidades"  # Adicionado endpoint de entidades para análise detalhada
    ]
    
    print("🔍 Testando endpoints do backend...")
    
    all_stats = {"entidades_total": 0, "entidades_com_dados": 0, "metricas_total": 0, "metricas_nulas": 0}
    entidades_status = []
    
    for endpoint in endpoints:
        try:
            if endpoint == "/api/chat":
                # POST para chat
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"pergunta": "status geral"}, 
                                       timeout=30)
            else:
                # GET para outros endpoints
                response = requests.get(f"{base_url}{endpoint}", timeout=30)
            
            print(f"\n📍 {endpoint}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Dados recebidos")
                    
                    # Analisa estrutura dos dados
                    if endpoint == "/api/diagnostico":
                        print(f"   📊 Diagnóstico:")
                        if isinstance(data, dict):
                            if 'metricas' in data:
                                metricas_count = len(data['metricas']) if data['metricas'] else 0
                                print(f"      - Métricas: {metricas_count}")
                                
                                if metricas_count > 0:
                                    print(f"      - Primeira métrica: {data['metricas'][0] if data['metricas'] else 'N/A'}")
                                else:
                                    print(f"      - ⚠️ PROBLEMA: Nenhuma métrica encontrada!")
                            
                            if 'explicacao' in data:
                                print(f"      - Explicação: {data['explicacao'][:100]}..." if data['explicacao'] else "N/A")
                                
                    elif endpoint == "/api/status":
                        print(f"   📈 Status:")
                        if isinstance(data, dict):
                            if 'entidades' in data:
                                entidades_count = data['entidades']
                                print(f"      - Total entidades: {entidades_count}")
                                if entidades_count == 0:
                                    print(f"      - ⚠️ PROBLEMA: Nenhuma entidade encontrada!")

                            if 'problemas' in data:
                                problemas_count = len(data['problemas']) if data['problemas'] else 0
                                print(f"      - Problemas detectados: {problemas_count}")
                                    
                    elif endpoint == "/api/health":
                        print(f"   🏥 Health:")
                        if isinstance(data, dict):
                            print(f"      - Status: {data.get('status', 'N/A')}")
                            print(f"      - Fallback mode: {data.get('fallback_mode', 'N/A')}")
                            
                    elif endpoint == "/api/chat":
                        print(f"   💬 Chat:")
                        if isinstance(data, dict) and 'resposta' in data:
                            resposta = data['resposta'][:100] + "..." if len(data['resposta']) > 100 else data['resposta']
                            print(f"      - Resposta: {resposta}")
                            
                            # Verificar se a resposta contém mensagem genérica
                            generic_responses = ["Desculpe pela confusão", "não incluem informações suficientes", "não tenho dados detalhados", "não foi possível obter", "Não possuo detalhes suficientes"]
                            
                            if any(text in data['resposta'] for text in generic_responses):
                                print(f"      - ⚠️ PROBLEMA: Resposta genérica detectada!")
                        else:
                            print(f"      - ⚠️ PROBLEMA: Resposta inválida!")
                            
                    elif endpoint == "/api/entidades":
                        print(f"   🔍 Entidades:")
                        if isinstance(data, list):
                            entidades_count = len(data)
                            print(f"      - Total entidades: {entidades_count}")
                            all_stats["entidades_total"] = entidades_count
                            
                            dominios = Counter([e.get('domain', 'Unknown') for e in data])
                            print(f"      - Distribuição por domínio: {dict(dominios)}")
                            
                            # Análise detalhada de métricas nulas
                            entidades_com_metricas = 0
                            entidades_sem_metricas = 0
                            metricas_nulas = 0
                            metricas_total = 0
                            problemas = Counter()
                            
                            print(f"      - Analisando detalhes de métricas...")
                            
                            for entidade in data:
                                possui_metricas_validas = False
                                detalhe_str = entidade.get('detalhe')
                                
                                # Processar quando o detalhe é string (formato JSON serializado)
                                if detalhe_str and isinstance(detalhe_str, str):
                                    try:
                                        detalhe = json.loads(detalhe_str.replace("'", "\""))
                                        # Verificar métricas comuns
                                        metricas_keys = [
                                            'cpu_percent', 'mem_percent', 'disk_percent',
                                            'uptime', 'network_in', 'network_out',
                                            'host_count'
                                        ]
                                        
                                        metricas_entity = 0
                                        nulas_entity = 0
                                        
                                        for key in metricas_keys:
                                            if key in detalhe and detalhe[key]:
                                                for metric_item in detalhe[key]:
                                                    metricas_entity += 1
                                                    metricas_total += 1
                                                    for k, v in metric_item.items():
                                                        if v is None:
                                                            nulas_entity += 1
                                                            metricas_nulas += 1
                                                        else:
                                                            possui_metricas_validas = True
                                        
                                        # Verificar tipo de problema
                                        problema = entidade.get('problema', '')
                                        problemas[problema] += 1
                                        
                                        # Status desta entidade
                                        entity_status = {
                                            "nome": entidade.get('name', 'Unknown'),
                                            "dominio": entidade.get('domain', 'Unknown'),
                                            "problema": problema,
                                            "metricas_total": metricas_entity,
                                            "metricas_nulas": nulas_entity,
                                            "porcentagem_nula": round(nulas_entity/metricas_entity*100 if metricas_entity > 0 else 0, 2)
                                        }
                                        entidades_status.append(entity_status)
                                        
                                    except json.JSONDecodeError:
                                        print(f"      - ⚠️ PROBLEMA: JSON inválido em detalhe de {entidade.get('name', 'Unknown')}")
                                        
                                if possui_metricas_validas:
                                    entidades_com_metricas += 1
                                else:
                                    entidades_sem_metricas += 1
                            
                            all_stats["entidades_com_dados"] = entidades_com_metricas
                            all_stats["metricas_total"] = metricas_total
                            all_stats["metricas_nulas"] = metricas_nulas
                            
                            print(f"      - Entidades com métricas válidas: {entidades_com_metricas}/{entidades_count} ({round(entidades_com_metricas/entidades_count*100 if entidades_count > 0 else 0, 2)}%)")
                            print(f"      - Entidades sem métricas válidas: {entidades_sem_metricas}/{entidades_count} ({round(entidades_sem_metricas/entidades_count*100 if entidades_count > 0 else 0, 2)}%)")
                            print(f"      - Métricas nulas: {metricas_nulas}/{metricas_total} ({round(metricas_nulas/metricas_total*100 if metricas_total > 0 else 0, 2)}%)")
                            print(f"      - Problemas detectados: {dict(problemas)}")
                            
                            # Listar top 5 entidades com mais métricas nulas
                            entidades_status.sort(key=lambda x: x['porcentagem_nula'], reverse=True)
                            print("\n      - Top 5 entidades com mais métricas nulas:")
                            for i, entity in enumerate(entidades_status[:5]):
                                print(f"        {i+1}. {entity['nome']} ({entity['dominio']}): {entity['metricas_nulas']}/{entity['metricas_total']} ({entity['porcentagem_nula']}%) - {entity['problema']}")
                                
                except json.JSONDecodeError:
                    print(f"   ❌ Erro ao decodificar JSON")
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                print(f"   Mensagem: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erro de conexão: {e}")
    
    # Sumário geral
    print("\n📊 SUMÁRIO GERAL DE DADOS:")
    print(f"- Entidades totais: {all_stats['entidades_total']}")
    print(f"- Entidades com dados reais: {all_stats['entidades_com_dados']} ({round(all_stats['entidades_com_dados']/all_stats['entidades_total']*100 if all_stats['entidades_total'] > 0 else 0, 2)}%)")
    print(f"- Total de métricas: {all_stats['metricas_total']}")
    print(f"- Métricas nulas: {all_stats['metricas_nulas']} ({round(all_stats['metricas_nulas']/all_stats['metricas_total']*100 if all_stats['metricas_total'] > 0 else 0, 2)}%)")
    
    return True

def verificar_frontend():
    """Verifica se o frontend está protegendo contra dados nulos"""
    try:
        # Verificar se o frontend está rodando
        response = requests.get("http://localhost:5173", timeout=2)
        print("\n🌐 Frontend disponível em http://localhost:5173")
        print("  Execute este script com o frontend aberto para ver os erros no console do navegador.")
    except:
        print("\n⚠️ Frontend não parece estar disponível em http://localhost:5173")
        print("  Inicie o frontend para verificar os erros de console.")

if __name__ == "__main__":
    print("🚀 Testando dados do backend para frontend...\n")
    test_backend_endpoints()
    verificar_frontend()
    print("\n✅ Teste concluído!")
