#!/data/data/com.termux/files/usr/bin/bash
# Installeert de P1-alert in Termux en laat hem automatisch starten na een herstart.
# Gebruik: bash installeer.sh <ntfy-kanaal> [IP-van-de-dongle]
set -e
KANAAL="$1"
IP="$2"
BASIS="https://raw.githubusercontent.com/ProgettiLuigi/Laadplanner/p1-alert/p1alert"

if [ -z "$KANAAL" ]; then
  echo "Gebruik: bash installeer.sh <ntfy-kanaal> [IP-van-de-dongle]"
  exit 1
fi

echo "== Pakketten installeren =="
# Alles bijwerken (anders kan curl stukgaan door een half bijgewerkte bibliotheek)
pkg update -y
apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold full-upgrade
pkg install -y python termux-api curl

echo "== Script downloaden =="
mkdir -p ~/p1alert ~/.termux/boot
curl -fsSL "$BASIS/p1alert.py" -o ~/p1alert/p1alert.py
curl -fsSL "$BASIS/zoek_p1.py" -o ~/p1alert/zoek_p1.py

if [ -z "$IP" ]; then
  echo "== P1-dongle zoeken op je wifi =="
  IP=$(python ~/p1alert/zoek_p1.py) || { echo "Installatie gestopt."; exit 1; }
fi
echo "P1-dongle gevonden op $IP"

cat > ~/p1alert/start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
while true; do
  python ~/p1alert/p1alert.py $IP $KANAAL
  sleep 30
done
EOF
chmod +x ~/p1alert/start.sh

cat > ~/.termux/boot/p1alert <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
exec ~/p1alert/start.sh
EOF
chmod +x ~/.termux/boot/p1alert

echo "== Oude versie stoppen en nieuwe starten =="
pkill -f "p1alert/start.sh" || true
pkill -f "p1alert/p1alert.py" || true
nohup ~/p1alert/start.sh >/dev/null 2>&1 &

MODEL=$(getprop ro.product.model 2>/dev/null || echo "gsm")
curl -fsS -H "Title: P1-alert actief" -d "P1-alert draait nu op $MODEL (dongle $IP)." \
  "https://ntfy.sh/$KANAAL" >/dev/null && echo "Testmelding verstuurd."

echo
echo "Klaar. De P1-alert draait en start automatisch na een herstart"
echo "(op voorwaarde dat Termux:Boot geinstalleerd is en 1 keer geopend werd)."
