"""
Painel de Status dos Agentes MPC

Este script cria uma interface gráfica simples para visualizar o status dos agentes MPC,
suas últimas atividades e métricas principais.

Requisitos:
- PyQt5: pip install PyQt5
"""

import sys
import os
import asyncio
import json
import logging
import time
from datetime import datetime
import traceback
from typing import Dict, List, Optional, Any

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mpc_status_panel")

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
        QProgressBar, QTabWidget, QTextEdit, QComboBox, QLineEdit,
        QFormLayout, QMessageBox, QHeaderView
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QThread
    from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
except ImportError:
    logger.error("PyQt5 não encontrado. Instale com: pip install PyQt5")
    logger.error("Tentando instalar automaticamente...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
        logger.info("PyQt5 instalado com sucesso. Reinicie o script.")
    except Exception as e:
        logger.error(f"Falha ao instalar PyQt5: {e}")
    sys.exit(1)

# Importar módulos MPC
try:
    from core_inteligente.mpc_agent_communication import (
        send_agent_command,
        broadcast_to_agents,
        get_agent_status,
        get_agent_history,
        mpc_communication
    )
except ImportError as e:
    logger.error(f"Erro ao importar módulo de comunicação MPC: {e}")
    sys.exit(1)

class BackgroundWorker(QThread):
    """Classe para executar tarefas em segundo plano"""
    statusUpdated = pyqtSignal(dict)
    historyUpdated = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
    
    def stop(self):
        self._running = False
    
    def run(self):
        """Executa o loop de atualização em segundo plano"""
        while self._running:
            try:
                # Obter status dos agentes
                status = asyncio.run(get_agent_status())
                self.statusUpdated.emit(status)
                
                # Obter histórico de comunicações
                history = get_agent_history(limit=20)
                self.historyUpdated.emit(history)
                
                # Aguardar antes da próxima atualização
                for _ in range(50):  # 5 segundos (100ms * 50)
                    if not self._running:
                        break
                    time.sleep(0.1)
                
            except Exception as e:
                self.error.emit(f"Erro na atualização de dados: {str(e)}")
                time.sleep(5)  # Aguardar antes de tentar novamente

class CommandWorker(QThread):
    """Classe para executar comandos em segundo plano"""
    commandCompleted = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, agent_id, action, parameters=None, context=None, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.action = action
        self.parameters = parameters or {}
        self.context = context or {}
    
    def run(self):
        """Executa o comando e emite o resultado"""
        try:
            response = asyncio.run(send_agent_command(
                agent_id=self.agent_id,
                action=self.action,
                parameters=self.parameters,
                context=self.context
            ))
            
            # Converter para dict para facilitar o envio via sinal
            result = {
                "status": response.status,
                "data": response.data,
                "error_message": response.error_message,
                "execution_time": response.execution_time,
                "agent_id": response.agent_id
            }
            self.commandCompleted.emit(result)
        except Exception as e:
            self.error.emit(f"Erro ao executar comando: {str(e)}")

class MPCStatusPanel(QMainWindow):
    """Painel principal para visualização do status dos agentes MPC"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Painel de Status dos Agentes MPC")
        self.setMinimumSize(800, 600)
        
        # Inicializar a interface
        self.init_ui()
        
        # Iniciar o worker em segundo plano
        self.background_worker = BackgroundWorker()
        self.background_worker.statusUpdated.connect(self.update_agent_status)
        self.background_worker.historyUpdated.connect(self.update_history)
        self.background_worker.error.connect(self.show_error)
        self.background_worker.start()
    
    def init_ui(self):
        """Inicializa a interface do usuário"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Tabs principais
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab de status
        self.status_tab = QWidget()
        self.tabs.addTab(self.status_tab, "Status dos Agentes")
        
        # Tab de histórico
        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, "Histórico de Comunicação")
        
        # Tab de comandos
        self.command_tab = QWidget()
        self.tabs.addTab(self.command_tab, "Enviar Comandos")
        
        # Inicializar cada tab
        self.init_status_tab()
        self.init_history_tab()
        self.init_command_tab()
    
    def init_status_tab(self):
        """Inicializa a tab de status dos agentes"""
        layout = QVBoxLayout(self.status_tab)
        
        # Cabeçalho com informações gerais
        header_box = QGroupBox("Informações do Sistema MPC")
        header_layout = QHBoxLayout(header_box)
        
        self.total_agents_label = QLabel("Agentes Total: --")
        self.active_agents_label = QLabel("Agentes Ativos: --")
        self.last_update_label = QLabel("Última Atualização: --")
        
        header_layout.addWidget(self.total_agents_label)
        header_layout.addWidget(self.active_agents_label)
        header_layout.addWidget(self.last_update_label)
        
        layout.addWidget(header_box)
        
        # Tabela de status dos agentes
        self.agent_table = QTableWidget()
        self.agent_table.setColumnCount(6)
        self.agent_table.setHorizontalHeaderLabels([
            "ID", "Nome", "Status", "Última Atividade", "Saúde", "Ações"
        ])
        self.agent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.agent_table)
        
        # Botão para atualizar status
        refresh_button = QPushButton("Atualizar Status")
        refresh_button.clicked.connect(self.refresh_status)
        layout.addWidget(refresh_button)
    
    def init_history_tab(self):
        """Inicializa a tab de histórico de comunicações"""
        layout = QVBoxLayout(self.history_tab)
        
        # Filtro de agente
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Agente:"))
        self.agent_filter = QComboBox()
        self.agent_filter.addItem("Todos", "")
        filter_layout.addWidget(self.agent_filter)
        
        # Botão de limpar histórico
        clear_button = QPushButton("Limpar Filtro")
        clear_button.clicked.connect(lambda: self.agent_filter.setCurrentIndex(0))
        filter_layout.addWidget(clear_button)
        
        layout.addLayout(filter_layout)
        
        # Tabela de histórico
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Agente", "Ação", "Status", "Duração", "Detalhes"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.history_table)
        
        # Conectar sinal de alteração do filtro
        self.agent_filter.currentIndexChanged.connect(self.apply_history_filter)
    
    def init_command_tab(self):
        """Inicializa a tab de envio de comandos"""
        layout = QVBoxLayout(self.command_tab)
        
        # Formulário para envio de comandos
        form_layout = QFormLayout()
        
        # Seleção de agente
        self.command_agent = QComboBox()
        self.command_agent.addItem("-- Selecione um Agente --", "")
        form_layout.addRow("Agente:", self.command_agent)
        
        # Ação a executar
        self.command_action = QLineEdit()
        form_layout.addRow("Ação:", self.command_action)
        
        # Parâmetros (em formato JSON)
        self.command_params = QTextEdit()
        self.command_params.setPlaceholderText('{\n    "param1": "valor1",\n    "param2": "valor2"\n}')
        form_layout.addRow("Parâmetros (JSON):", self.command_params)
        
        # Contexto (em formato JSON)
        self.command_context = QTextEdit()
        self.command_context.setPlaceholderText('{\n    "contexto1": "valor1"\n}')
        form_layout.addRow("Contexto (JSON):", self.command_context)
        
        # Adicionar o formulário
        form_group = QGroupBox("Enviar Comando")
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Botão de envio
        send_button = QPushButton("Enviar Comando")
        send_button.clicked.connect(self.send_command)
        layout.addWidget(send_button)
        
        # Área de resultado
        result_group = QGroupBox("Resultado")
        result_layout = QVBoxLayout(result_group)
        
        self.command_result = QTextEdit()
        self.command_result.setReadOnly(True)
        result_layout.addWidget(self.command_result)
        
        layout.addWidget(result_group)
    
    @pyqtSlot(dict)
    def update_agent_status(self, status_data):
        """Atualiza a visualização de status com os dados mais recentes"""
        agents = []
        active_count = 0
        
        # Processar dados para extrair informações dos agentes
        for agent_id, status in status_data.items():
            if isinstance(status, dict):
                agent_info = mpc_communication.get_agent_by_id(agent_id) or {}
                
                agent_data = {
                    "id": agent_id,
                    "name": agent_info.get("name", agent_id),
                    "status": status.get("status", "unknown"),
                    "last_activity": status.get("last_activity", "Never"),
                    "health": status.get("health", 0),
                    "enabled": agent_info.get("enabled", True)
                }
                
                agents.append(agent_data)
                
                if agent_data["status"] == "active" and agent_data["enabled"]:
                    active_count += 1
        
        # Atualizar labels de informações gerais
        self.total_agents_label.setText(f"Agentes Total: {len(agents)}")
        self.active_agents_label.setText(f"Agentes Ativos: {active_count}")
        self.last_update_label.setText(f"Última Atualização: {datetime.now().strftime('%H:%M:%S')}")
        
        # Atualizar tabela de agentes
        self.agent_table.setRowCount(len(agents))
        
        for row, agent in enumerate(agents):
            # ID
            self.agent_table.setItem(row, 0, QTableWidgetItem(agent["id"]))
            
            # Nome
            self.agent_table.setItem(row, 1, QTableWidgetItem(agent["name"]))
            
            # Status
            status_item = QTableWidgetItem(agent["status"])
            if agent["status"] == "active":
                status_item.setForeground(QColor("green"))
            elif agent["status"] == "inactive":
                status_item.setForeground(QColor("orange"))
            else:
                status_item.setForeground(QColor("red"))
            self.agent_table.setItem(row, 2, status_item)
            
            # Última atividade
            self.agent_table.setItem(row, 3, QTableWidgetItem(agent["last_activity"]))
            
            # Saúde
            health_bar = QProgressBar()
            health_bar.setRange(0, 100)
            health_bar.setValue(agent["health"])
            if agent["health"] > 70:
                health_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            elif agent["health"] > 30:
                health_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
            else:
                health_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            
            self.agent_table.setCellWidget(row, 4, health_bar)
            
            # Ações
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Botão de diagnóstico
            diagnose_button = QPushButton("Diagnosticar")
            diagnose_button.setProperty("agent_id", agent["id"])
            diagnose_button.clicked.connect(lambda checked, aid=agent["id"]: self.run_diagnostics(aid))
            actions_layout.addWidget(diagnose_button)
            
            # Botão de ativar/desativar
            toggle_button = QPushButton("Desativar" if agent["enabled"] else "Ativar")
            toggle_button.setProperty("agent_id", agent["id"])
            toggle_button.setProperty("enabled", agent["enabled"])
            toggle_button.clicked.connect(lambda checked, aid=agent["id"], en=agent["enabled"]: self.toggle_agent(aid, en))
            actions_layout.addWidget(toggle_button)
            
            self.agent_table.setCellWidget(row, 5, actions_widget)
        
        # Atualizar combobox de seleção de agente na tab de comandos
        current_agent = self.command_agent.currentData()
        self.command_agent.clear()
        self.command_agent.addItem("-- Selecione um Agente --", "")
        
        for agent in agents:
            self.command_agent.addItem(f"{agent['name']} ({agent['id']})", agent["id"])
        
        # Restaurar seleção anterior se possível
        if current_agent:
            index = self.command_agent.findData(current_agent)
            if index >= 0:
                self.command_agent.setCurrentIndex(index)
        
        # Atualizar combobox de filtro de agente na tab de histórico
        current_filter = self.agent_filter.currentData()
        self.agent_filter.clear()
        self.agent_filter.addItem("Todos", "")
        
        for agent in agents:
            self.agent_filter.addItem(f"{agent['name']} ({agent['id']})", agent["id"])
        
        # Restaurar seleção anterior se possível
        if current_filter:
            index = self.agent_filter.findData(current_filter)
            if index >= 0:
                self.agent_filter.setCurrentIndex(index)
    
    @pyqtSlot(list)
    def update_history(self, history_data):
        """Atualiza a visualização de histórico com os dados mais recentes"""
        # Guardar dados completos para filtro posterior
        self._full_history = history_data
        
        # Aplicar filtro atual
        self.apply_history_filter()
    
    def apply_history_filter(self):
        """Aplica filtro no histórico baseado no agente selecionado"""
        if not hasattr(self, '_full_history'):
            return
        
        agent_id = self.agent_filter.currentData()
        
        if agent_id:
            filtered_history = [
                entry for entry in self._full_history
                if entry.get("request", {}).get("agent_id") == agent_id
            ]
        else:
            filtered_history = self._full_history
        
        # Atualizar tabela
        self.history_table.setRowCount(len(filtered_history))
        
        for row, entry in enumerate(filtered_history):
            timestamp = entry.get("timestamp", "")
            agent_id = entry.get("request", {}).get("agent_id", "")
            action = entry.get("request", {}).get("action", "")
            status = entry.get("response", {}).get("status", "")
            duration = entry.get("duration", 0)
            
            # Timestamp
            self.history_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Agente
            agent_item = QTableWidgetItem(agent_id)
            self.history_table.setItem(row, 1, agent_item)
            
            # Ação
            action_item = QTableWidgetItem(action)
            self.history_table.setItem(row, 2, action_item)
            
            # Status
            status_item = QTableWidgetItem(status)
            if status == "success":
                status_item.setForeground(QColor("green"))
            else:
                status_item.setForeground(QColor("red"))
            self.history_table.setItem(row, 3, status_item)
            
            # Duração
            duration_item = QTableWidgetItem(f"{duration:.2f}s")
            self.history_table.setItem(row, 4, duration_item)
            
            # Detalhes
            details_button = QPushButton("Ver Detalhes")
            details_button.clicked.connect(lambda checked, e=entry: self.show_history_details(e))
            
            details_widget = QWidget()
            details_layout = QHBoxLayout(details_widget)
            details_layout.setContentsMargins(2, 2, 2, 2)
            details_layout.addWidget(details_button)
            
            self.history_table.setCellWidget(row, 5, details_widget)
    
    def show_history_details(self, entry):
        """Mostra detalhes completos de uma entrada do histórico"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Detalhes da Comunicação")
        
        # Formatar os detalhes
        timestamp = entry.get("timestamp", "")
        request = entry.get("request", {})
        response = entry.get("response", {})
        duration = entry.get("duration", 0)
        
        details = f"Timestamp: {timestamp}\n"
        details += f"Duração: {duration:.2f}s\n\n"
        
        details += "REQUEST:\n"
        details += f"  Agente: {request.get('agent_id', '')}\n"
        details += f"  Ação: {request.get('action', '')}\n"
        details += f"  Parâmetros: {json.dumps(request.get('parameters', {}), indent=2)}\n"
        details += f"  Contexto: {json.dumps(request.get('context', {}), indent=2)}\n\n"
        
        details += "RESPONSE:\n"
        details += f"  Status: {response.get('status', '')}\n"
        if response.get("error_message"):
            details += f"  Erro: {response.get('error_message', '')}\n"
        if response.get("data"):
            details += f"  Dados: {json.dumps(response.get('data', {}), indent=2)}\n"
        
        dialog.setText(details)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec_()
    
    def refresh_status(self):
        """Força uma atualização do status dos agentes"""
        try:
            status = asyncio.run(get_agent_status())
            self.update_agent_status(status)
        except Exception as e:
            self.show_error(f"Erro ao atualizar status: {str(e)}")
    
    def run_diagnostics(self, agent_id):
        """Executa diagnóstico em um agente específico"""
        self.command_worker = CommandWorker(
            agent_id=agent_id,
            action="run_diagnostic",
            parameters={"scope": "full"}
        )
        self.command_worker.commandCompleted.connect(self.handle_command_result)
        self.command_worker.error.connect(self.show_error)
        self.command_worker.start()
        
        QMessageBox.information(self, "Diagnóstico Iniciado", 
                              f"Iniciando diagnóstico do agente {agent_id}.\nOs resultados serão exibidos em breve.")
    
    def toggle_agent(self, agent_id, currently_enabled):
        """Ativa ou desativa um agente"""
        # Atualizar a configuração
        for i, agent_config in enumerate(mpc_communication.config.get("agents", [])):
            if agent_config.get("id") == agent_id:
                mpc_communication.config["agents"][i]["enabled"] = not currently_enabled
                break
        
        # Salvar a configuração atualizada
        try:
            with open(mpc_communication._agent_config_file, "w") as f:
                json.dump(mpc_communication.config, f, indent=4)
            
            msg = f"Agente {agent_id} {'desativado' if currently_enabled else 'ativado'} com sucesso!"
            QMessageBox.information(self, "Estado do Agente Alterado", msg)
            
            # Forçar atualização do status
            self.refresh_status()
        except Exception as e:
            self.show_error(f"Erro ao salvar configuração: {str(e)}")
    
    def send_command(self):
        """Envia um comando para o agente selecionado"""
        agent_id = self.command_agent.currentData()
        if not agent_id:
            self.show_error("Selecione um agente.")
            return
        
        action = self.command_action.text().strip()
        if not action:
            self.show_error("Informe uma ação.")
            return
        
        # Processar parâmetros
        params_text = self.command_params.toPlainText().strip()
        if params_text:
            try:
                parameters = json.loads(params_text)
            except json.JSONDecodeError as e:
                self.show_error(f"Erro no formato JSON dos parâmetros: {str(e)}")
                return
        else:
            parameters = {}
        
        # Processar contexto
        context_text = self.command_context.toPlainText().strip()
        if context_text:
            try:
                context = json.loads(context_text)
            except json.JSONDecodeError as e:
                self.show_error(f"Erro no formato JSON do contexto: {str(e)}")
                return
        else:
            context = {}
        
        # Executar comando em thread separada
        self.command_worker = CommandWorker(
            agent_id=agent_id,
            action=action,
            parameters=parameters,
            context=context
        )
        self.command_worker.commandCompleted.connect(self.handle_command_result)
        self.command_worker.error.connect(self.show_error)
        self.command_worker.start()
        
        # Feedback visual
        self.command_result.setPlainText("Comando enviado, aguardando resposta...")
    
    @pyqtSlot(dict)
    def handle_command_result(self, result):
        """Processa o resultado de um comando"""
        if result["status"] == "success":
            output = f"Comando executado com sucesso!\n\n"
            if result["data"]:
                output += f"Dados:\n{json.dumps(result['data'], indent=2)}"
            else:
                output += "Nenhum dado retornado."
        else:
            output = f"Erro ao executar comando!\n\n"
            output += f"Mensagem: {result['error_message']}"
        
        if result["execution_time"]:
            output += f"\n\nTempo de execução: {result['execution_time']:.2f}s"
        
        self.command_result.setPlainText(output)
        
        # Forçar atualização do status e histórico
        self.refresh_status()
    
    def show_error(self, message):
        """Exibe uma mensagem de erro"""
        QMessageBox.critical(self, "Erro", message)
    
    def closeEvent(self, event):
        """Interrompe os threads ao fechar a janela"""
        if hasattr(self, 'background_worker'):
            self.background_worker.stop()
            self.background_worker.wait()
        
        if hasattr(self, 'command_worker'):
            self.command_worker.wait()
        
        event.accept()

def main():
    """Função principal"""
    # Verificar ambiente
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_inteligente")):
        logger.error("Diretório core_inteligente não encontrado.")
        sys.exit(1)
    
    # Iniciar a aplicação
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Aplicar tema escuro
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    # Criar e exibir a janela principal
    window = MPCStatusPanel()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
