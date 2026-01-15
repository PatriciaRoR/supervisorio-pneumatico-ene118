"""
Arquivo para iniciar todos os módulos do sistema
Execute: python iniciar_sistema.py
"""

import threading
import time

def iniciar_monitoramento():
    """Inicia módulo de monitoramento"""
    from monitoramento import Monitoramento
    
    print("=" * 60)
    print("INICIANDO SISTEMA SUPERVISÓRIO")
    print("=" * 60)
    
    print("\n1. Iniciando monitoramento MODBUS...")
    

    monitor = Monitoramento()

    
    def loop_monitoramento():
        try:
            monitor.executar_monitoramento(scan_time=2)
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
    
    thread = threading.Thread(target=loop_monitoramento, daemon=True)
    thread.start()
    
    return monitor

def iniciar_bd():
    """Inicia módulo de banco de dados"""
    from bdhandler import BDHandler
    
    print("2. Iniciando banco de dados...")
    bd = BDHandler()
    bd.start()
    
    return bd

def main():
    """Função principal"""
    monitor = iniciar_monitoramento()
    bd = iniciar_bd()
    
    print("\n" + "=" * 60)
    print("BACKEND PRONTO!")
    print("=" * 60)
    print("\nAgora execute a interface Kivy em OUTRO terminal:")
    print("  python main.py")
    print("\nPressione Ctrl+C para encerrar o backend...")
    
    try:
        # Mantém o programa principal rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando sistema...")
        monitor.parar_monitoramento()
        bd.stop()
        print("Sistema encerrado.")

if __name__ == "__main__":
    main()