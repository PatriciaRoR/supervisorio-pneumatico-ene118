"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura e organização das variáveis dp processo.
"""

# Módulo time não é importado automaticamente
import time


class Monitoramento(object):
    """
    Classe responsável pelo monitoramento das variáveis do sistema pneumático. 
    """
    
    def __init__(self):
        """
        Incializa as variáveis monitoradas do processo e o historico temporal
        """
        
        self.variaveis = {}
        self.historico = {}
        self.executando = False  # controle do loop de monitoramento

    def atualizar_variavel(self, nome, valor):
        """
        Atualiza o valor de uma variável monitorada
        Se uma variável ainda não existir ela é criada
        """
        # tempo real
        timestamp = time.time()

        # cria a variável se não existir
        if nome not in self.variaveis: 
            self.variaveis[nome] = valor
            self.historico[nome] = []
        else:
            self.variaveis[nome] = valor

        # salva histórico
        self.historico[nome].append((timestamp, valor))

    def obter_variaveis(self):
        """
        Retorna o dicionário com todas as variáveis monitoradas. 
        """
        return self.variaveis

    def obter_historico(self, nome):
        """
        Retorna o historico temporal de uma variável especifica.
        """
        return self.historico.get(nome, [])

    def obter_todas(self):
        """
        Retorna todas as variáveis monitoradas.
        """
        return self.variaveis

    def executar_monitoramento(self, scan_time=1):
        """
        Executa o ciclo contínuo de monitoramento.
        scan_time: tempo de varredura em segundos.
        """
        self.executando = True

        while self.executando:
            # Simulação provisória de leitura do processo
            valor_atual = self.variaveis.get("pressao_ar", 0)
            self.atualizar_variavel("pressao_ar", valor_atual + 0.1)

            time.sleep(scan_time)

    def parar_monitoramento(self):
        """
        Interrompe o ciclo de monitoramento.
        """
        self.executando = False

    