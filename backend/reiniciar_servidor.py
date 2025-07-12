"""
Script para reiniciar o servidor principal (main.py) com as correções
"""
import os
import subprocess
import sys
import time
import signal
import psutil

def kill_process_on_port(port=8000):
    """Finaliza qualquer processo que esteja usando a porta especificada"""
    print(f"Verificando processos na porta {port}...")
    
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            # Verifica se o processo tem conexões de rede
            if proc.info['connections']:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        print(f"Encontrado processo {proc.info['name']} (PID: {proc.info['pid']}) usando a porta {port}")
                        print(f"Finalizando processo...")
                        try:
                            process = psutil.Process(proc.info['pid'])
                            process.terminate()
                            process.wait(timeout=3)
                            print(f"Processo finalizado com sucesso!")
                            return True
                        except Exception as e:
                            print(f"Erro ao finalizar processo: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"Nenhum processo encontrado na porta {port}")
    return True

def restart_server():
    """Reinicia o servidor principal"""
    # Primeiro finaliza qualquer servidor existente
    kill_process_on_port(8000)
    
    # Espera um momento para garantir que a porta foi liberada
    time.sleep(2)
    
    # Inicia o servidor em um novo processo
    print("Iniciando o servidor...")
    server_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--reload"],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Aguarda alguns segundos para o servidor iniciar
    print("Aguardando o servidor iniciar (10 segundos)...")
    time.sleep(10)
    
    # Verifica se o processo ainda está em execução
    if server_process.poll() is None:
        print("Servidor iniciado com sucesso!")
        return True
    else:
        stdout, stderr = server_process.communicate()
        print(f"Erro ao iniciar o servidor:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

def test_endpoints():
    """Executa o script de teste de endpoints"""
    print("\nTestando os endpoints...")
    try:
        result = subprocess.run(
            ["python", "teste_rapido_agno.py"],
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Falha ao testar endpoints: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("REINICIANDO SERVIDOR COM CORREÇÕES")
    print("=" * 60)
    
    try:
        # Instala a biblioteca psutil se não estiver disponível
        import psutil
    except ImportError:
        print("Instalando a biblioteca psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    if restart_server():
        # Se o servidor reiniciar com sucesso, testa os endpoints
        test_endpoints()
    else:
        print("Falha ao reiniciar o servidor. Verifique os logs para mais detalhes.")
        sys.exit(1)
