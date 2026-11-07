# Zoekt de HomeWizard P1-dongle op het lokale wifi-netwerk.
# Print het IP-adres (stdout) of stopt met foutcode 1.
# Optioneel argument: netwerkprefix, bv. 192.168.1 (anders automatisch).
import concurrent.futures
import ipaddress
import json
import socket
import sys
import urllib.request


def eigen_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 80))  # er wordt niets verstuurd
        return s.getsockname()[0]
    finally:
        s.close()


def is_p1(ip):
    try:
        with urllib.request.urlopen(f"http://{ip}/api/v1/data", timeout=1.5) as r:
            d = json.load(r)
        return ip if "active_power_w" in d else None
    except Exception:
        return None


def main():
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    else:
        ip = eigen_ip()
        if not ipaddress.ip_address(ip).is_private or not ip.startswith("192.168."):
            print(f"Je gsm lijkt niet op je thuiswifi te zitten (IP {ip}).", file=sys.stderr)
            sys.exit(1)
        prefix = ip.rsplit(".", 1)[0]
    print(f"Zoeken op {prefix}.1 - {prefix}.254 ...", file=sys.stderr)
    kandidaten = [f"{prefix}.{i}" for i in range(1, 255)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        gevonden = [ip for ip in ex.map(is_p1, kandidaten) if ip]
    if not gevonden:
        print("Geen P1-dongle gevonden. Staat 'Lokale API' aan in de HomeWizard-app?",
              file=sys.stderr)
        sys.exit(1)
    print(gevonden[0])


if __name__ == "__main__":
    main()
