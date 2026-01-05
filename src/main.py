from monitoramento import Monitoramento


def main():
    monitor = Monitoramento()
    monitor.executar_monitoramento(scan_time=1)


if __name__ == "__main__":
    main()
