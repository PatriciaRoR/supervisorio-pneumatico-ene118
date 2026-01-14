"""
Arquivo principal de TESTE do módulo de monitoramento.

Usado para:
- Validar comunicação Modbus
- Testar leitura das variáveis
- Testar atuação (motor, válvula, velocidade)
ANTES da integração com Kivy e Banco de Dados.
"""

import time
from monitoramento import Monitoramento


def main():
    
    # CONFIGURAÇÃO DA BANCADA / CLP
    
    IP_CLP = "127.0.0.1"      # simulador 
    PORTA_CLP = 502

    sistema = Monitoramento(ip=IP_CLP, port=PORTA_CLP)

    print("=" * 70)
    print(" TESTE DE BANCADA – MONITORAMENTO PNEUMÁTICO ")
    print("=" * 70)
    print(f"Conectando em {IP_CLP}:{PORTA_CLP}")
    print("CTRL+C para encerrar\n")

    try:
       
        # TESTES INICIAIS DE ATUAÇÃO
       

        print(">> Teste: método de partida = INVERSOR")
        sistema.set_metodo_partida(2)
        time.sleep(1)

        print(">> Teste: ligando motor")
        sistema.set_motor(True)
        time.sleep(2)

        print(">> Teste: velocidade = 40%")
        sistema.set_velocidade(40)
        time.sleep(2)

        print(">> Iniciando leitura contínua...\n")

        # LOOP DE MONITORAMENTO
        
        while True:
            sistema.readData()
            sistema.atualizar_variaveis_calculadas()

            dados = sistema.get_measurements()

            print("\nTimestamp:",
                  time.strftime("%H:%M:%S",
                                time.localtime(dados["timestamp"])))
            print("-" * 60)

            for tag, valor in dados["values"].items():
                print(f"{tag:25s} : {valor}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nEncerrando teste...")
        print(">> Desligando motor por segurança")
        sistema.set_motor(False)

    except Exception as e:
        print("\nERRO:", e)
        sistema.set_motor(False)


if __name__ == "__main__":
    main()
