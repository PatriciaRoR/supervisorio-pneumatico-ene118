from monitoramento import Monitoramento

def main():
    monitor = Monitoramento(ip="10.15.30.182", port=502)

    try:
        monitor.executar_monitoramento(scan_time=1)
    except KeyboardInterrupt:
        monitor.parar_monitoramento()
        print("Monitoramento encerrado.")

if __name__ == "__main__":
    main()
