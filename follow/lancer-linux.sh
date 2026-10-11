#!/bin/bash
# FOLLOW — lance la page en local (Linux) : ./lancer-linux.sh
cd "$(dirname "$0")"
PORT=8765
# si le port est déjà pris, on prend le suivant libre
if command -v python3 >/dev/null 2>&1; then
  PORT=$(python3 -c 'import socket
for p in range(8765, 8800):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p)); print(p); break
    except OSError: pass
    finally: s.close()')
fi
URL="http://localhost:$PORT/index.html"
if command -v python3 >/dev/null 2>&1; then
  echo "Serveur local : $URL  (Ctrl+C pour arrêter)"
  (sleep 1; xdg-open "$URL" >/dev/null 2>&1) &
  python3 -m http.server $PORT
elif command -v npx >/dev/null 2>&1; then
  echo "Serveur local : $URL  (Ctrl+C pour arrêter)"
  (sleep 3; xdg-open "$URL" >/dev/null 2>&1) &
  npx --yes http-server -p $PORT -c-1 .
else
  xdg-open index.html
fi
