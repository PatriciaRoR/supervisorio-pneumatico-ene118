"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura das variáveis do processo.
"""
class monitoramento(object):
    "classe responsável pelo monitoramento das variáveis do sistema pneumático"
    
    def __init__(self):
        "Incializa as variáveis"
        
        self.variaveis = {}

    def atualizar_variavel(self, nome, valor):
        "Atualiza o valor de uma variável monitorada"

        self.variaveis[nome] = valor