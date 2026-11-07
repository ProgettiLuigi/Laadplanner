#!/data/data/com.termux/files/usr/bin/env python
# P1-alert voor het capaciteitstarief - draait in Termux op Android.
# Leest de HomeWizard P1-dongle lokaal uit (alleen bereikbaar op je eigen wifi).
# Melding als de netafname langer dan DUUR_S boven GRENS_W blijft.
#
# Gebruik:
#   Melding op deze gsm:          python p1alert.py <IP-dongle>
#   Melding via ntfy (naar Lorenzo): python p1alert.py <IP-dongle> <ntfy-kanaal>
# Met een ntfy-kanaal krijgt ALLEEN wie op dat kanaal geabonneerd is de melding;
# de gsm waarop het script draait toont zelf niets.
# Draait het op meerdere gsm's tegelijk, dan kijkt elk script eerst of er de
# laatste 15 min al een melding op het kanaal kwam, zodat je er geen 4 krijgt.

import json
import random
import subprocess
import sys
import time
import urllib.request

GRENS_W = 3900        # grens in watt
DUUR_S = 120          # zo lang moet de afname boven de grens blijven (2 min)
INTERVAL_S = 10       # om de 10 seconden uitlezen
RUST_S = 15 * 60      # na een melding 15 min geen nieuwe melding
MAX_FOUTEN = 3        # na 3 mislukte metingen op rij: timer resetten (niet thuis)

if len(sys.argv) < 2:
    print("Gebruik: python p1alert.py <IP-dongle> [ntfy-kanaal]")
    sys.exit(1)

URL = f"http://{sys.argv[1]}/api/v1/data"
NTFY = f"https://ntfy.sh/{sys.argv[2]}" if len(sys.argv) > 2 else None


def lees():
    """Geeft (actueel vermogen W, kwartiergemiddelde W) of (None, None)."""
    try:
        with urllib.request.urlopen(URL, timeout=5) as r:
            d = json.load(r)
        w = d.get("active_power_w")
        return (float(w) if w is not None else None), d.get("active_power_average_w")
    except Exception:
        return None, None


def recent_al_gemeld():
    """True als er de laatste RUST_S seconden al een melding op het kanaal kwam."""
    try:
        url = f"{NTFY}/json?poll=1&since={RUST_S // 60}m"
        with urllib.request.urlopen(url, timeout=10) as r:
            for regel in r.read().decode().splitlines():
                if regel.strip() and json.loads(regel).get("event") == "message":
                    return True
    except Exception:
        pass
    return False


def melding(titel, tekst):
    if NTFY:
        # Kleine willekeurige wachttijd: als 2 gsm's tegelijk meten,
        # ziet de tweede de melding van de eerste en zwijgt.
        time.sleep(random.uniform(0, 15))
        if recent_al_gemeld():
            return
        try:
            req = urllib.request.Request(
                NTFY, data=tekst.encode("utf-8"), method="POST",
                headers={"Title": titel, "Priority": "high", "Tags": "zap"})
            urllib.request.urlopen(req, timeout=10).close()
        except Exception:
            pass
        return
    subprocess.run(
        ["termux-notification", "--id", "p1alert", "--title", titel,
         "--content", tekst, "--priority", "high", "--sound",
         "--vibrate", "500,300,500"],
        check=False,
    )


def main():
    subprocess.run(["termux-wake-lock"], check=False)
    boven_sinds = None
    laatste_melding = 0.0
    fouten = 0
    print(f"P1-alert gestart: grens {GRENS_W} W gedurende {DUUR_S} s. Stoppen met Ctrl+C.")

    while True:
        w, gem = lees()
        nu = time.time()

        if w is None:
            # Niet op je wifi of dongle onbereikbaar: niets melden.
            fouten += 1
            if fouten >= MAX_FOUTEN:
                boven_sinds = None
        else:
            fouten = 0
            if w > GRENS_W:
                if boven_sinds is None:
                    boven_sinds = nu
                if nu - boven_sinds >= DUUR_S and nu - laatste_melding >= RUST_S:
                    minuten = int((nu - boven_sinds) // 60)
                    tekst = (f"Afname nu {w / 1000:.2f} kW, al {minuten} min "
                             f"boven {GRENS_W / 1000:.1f} kW.")
                    if gem is not None:
                        tekst += f" Kwartiergemiddelde: {float(gem) / 1000:.2f} kW."
                    melding("Hoog verbruik - let op je piek", tekst)
                    laatste_melding = nu
            else:
                boven_sinds = None

        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        subprocess.run(["termux-wake-unlock"], check=False)
        print("Gestopt.")
