"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura e organização das variáveis dp processo.
"""
class monitoramento(object):
    "classe responsável pelo monitoramento das variáveis do sistema pneumático. "
    
    def __init__(self):
        "Incializa as variáveis monitoradas do processo. "
        
        self.variaveis = {}

    def atualizar_variavel(self, nome, valor):
        "Atualiza o valor de uma variável monitorada. "

        if nome in self.variaveis: 

        self.variaveis[nome] = valor

    def obter_variaveis(self):
        "Retorna o dicionário com todas as variáveis monitoradas. "

        return self.variaveis
    def obter_historico(self, nome):
        "Retorna o historico temporal de uma variável especifica. "

        return self.historico.get(nome, [])
    
    