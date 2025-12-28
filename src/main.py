from monitoramento import Monitoramento

def main():
    # cria o objeto de monitoramento
    monitor = Monitoramento()

    # cria as variáveis inicialmente (importante!)
    monitor.variaveis["pressao_ar"] = 0
    monitor.variaveis["nivel_reservatorio"] = 0
    monitor.variaveis["velocidade_esteira"] = 0

    # simula atualização das variáveis
    monitor.atualizar_variavel("pressao_ar", 6.2)
    monitor.atualizar_variavel("nivel_reservatorio", 72)
    monitor.atualizar_variavel("velocidade_esteira", 1.5)

    # leitura das variáveis
    print("Pressão do ar:", monitor.obter_variaveis()["pressao_ar"])
    print("Nível do reservatório:", monitor.obter_variaveis()["nivel_reservatorio"])
    print("Velocidade da esteira:", monitor.obter_variaveis()["velocidade_esteira"])

    print("\nTodas as variáveis:")
    print(monitor.obter_todas())

if __name__ == "__main__":
    main()
