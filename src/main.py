"""
Main de testes para o módulo Monitoramento.
Testas individuais para todas as funções do supervisório
"""

import time
from monitoramento import Monitoramento


def menu():
    print("\n================ MENU DE TESTES ================")
    print("1  - Ler todas as variáveis (1 ciclo)")
    print("2  - Loop de leitura contínua")
    print("3  - Selecionar método de partida")
    print("4  - Ligar motor")
    print("5  - Desligar motor")
    print("6  - Resetar motor")
    print("7  - Ajustar velocidade do motor")
    print("8  - Abrir válvula")
    print("9  - Fechar válvula")
    print("10 - Ajustar PID (P, I, D, SP)")
    print("0  - Sair")
    print("================================================")


def main():
    print("=== TESTE DO SUPERVISÓRIO - MODBUS TCP ===")

    ip = input("IP do CLP: ").strip()
    porta = int(input("Porta Modbus (ex: 502): "))

    mon = Monitoramento(ip=ip, port=porta)

    while True:
        menu()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            mon.readData()
            print("\n--- DADOS LIDOS ---")
            for k, v in mon._meas["values"].items():
                print(f"{k:25s}: {v}")

        elif opcao == "2":
            print("Leitura contínua (CTRL+C para parar)")
            try:
                while True:
                    mon.readData()
                    print("\nTimestamp:", mon._meas["timestamp"])
                    for k, v in mon._meas["values"].items():
                        print(f"{k:25s}: {v}")
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nLeitura interrompida.")

        elif opcao == "3":
            print("1 = Soft | 2 = Inversor | 3 = Direta")
            metodo = int(input("Selecione o método: "))
            mon.set_metodo_partida(metodo)
            print("Método de partida enviado.")

        elif opcao == "4":
            mon.ligar_motor(1)
            print("Comando LIGAR enviado.")

        elif opcao == "5":
            mon.ligar_motor(0)
            print("Comando DESLIGAR enviado.")

        elif opcao == "6":
            mon.ligar_motor(2)
            print("Comando RESET enviado.")

        elif opcao == "7":
            vel = float(input("Velocidade (ex: 30 Hz): "))
            mon.set_velocidade(vel)
            print("Velocidade enviada.")

        elif opcao == "8":
            num = int(input("Número da válvula (1 a 6): "))
            mon.set_valvula(num, True)
            print(f"Válvula XV{num} ABERTA.")

        elif opcao == "9":
            num = int(input("Número da válvula (1 a 6): "))
            mon.set_valvula(num, False)
            print(f"Válvula XV{num} FECHADA.")

        elif opcao == "10":
            print("Deixe em branco para não alterar.")
            p = input("P: ")
            i = input("I: ")
            d = input("D: ")
            sp = input("SP: ")

            params = {}
            if p: params["p"] = float(p)
            if i: params["i"] = float(i)
            if d: params["d"] = float(d)
            if sp: params["sp"] = float(sp)

            mon.set_pid(**params)
            print("Parâmetros PID enviados.")

        elif opcao == "0":
            print("Encerrando testes.")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
