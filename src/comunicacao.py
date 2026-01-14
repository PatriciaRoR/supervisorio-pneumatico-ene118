"""
Ponte de comunicação simples e thread-safe entre módulos
Utilizada para troca de dados e comandos entre:
- Monitoramento (backend)
- Interface gráfica (Kivy)
- Banco de dados
"""

import threading
import time
from collections import deque


class Mensagem:
    """
    Estrutura padrão de mensagem entre módulos.
    """
    def __init__(self, tipo, dados=None, origem=None):
        self.tipo = tipo
        self.dados = dados
        self.origem = origem
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "tipo": self.tipo,
            "dados": self.dados,
            "origem": self.origem,
            "timestamp": self.timestamp
        }


class Comunicacao:
    """
    Classe para comunicação entre threads/módulos.
    """

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        self._dados = {}
        self._comandos = deque(maxlen=100)
        self._callbacks = {}
        self._lock = threading.Lock()
        self._ultima_atualizacao = 0

    
    # ENVIO DE DADOS (MONITORAMENTO → KIVY / BD)
    
    def enviar(self, mensagem: Mensagem):
        """
        Envia dados do monitoramento para os demais módulos.
        """
        with self._lock:
            self._dados = mensagem.to_dict()
            self._ultima_atualizacao = time.time()

    def obter_dados(self):
        """
        Obtém os últimos dados disponíveis.
        """
        with self._lock:
            return self._dados.copy()

    def tem_dados_recentes(self, segundos=5):
        """
        Verifica se os dados são recentes.
        """
        with self._lock:
            return (time.time() - self._ultima_atualizacao) < segundos

    
    # COMANDOS (KIVY → MONITORAMENTO)
    
    def enviar_comando(self, comando: dict):
        """
        Envia comando para o backend.
        """
        with self._lock:
            comando["timestamp"] = time.time()
            self._comandos.append(comando)

    def obter_proximo_comando(self):
        """
        Retorna o próximo comando pendente.
        """
        with self._lock:
            if self._comandos:
                return self._comandos.popleft()
        return None

    
    # CALLBACKS (EVENTOS)
    
    def receber(self, tipo, callback):
        """
        Registra callback para um tipo de comando.
        """
        with self._lock:
            self._callbacks[tipo] = callback

    def despachar_comandos(self):
        """
        Executa callbacks registrados para comandos recebidos.
        """
        comando = self.obter_proximo_comando()
        if comando:
            tipo = comando.get("acao")
            callback = self._callbacks.get(tipo)
            if callback:
                callback(comando)


# Instância global
com = Comunicacao()
