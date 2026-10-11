#!/bin/bash
# FOLLOW — lance la page en local (Mac). Double-clique sur ce fichier.
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
  echo "Serveur local : $URL  (ferme cette fenêtre pour l'arrêter)"
  (sleep 1; open "$URL") &
  python3 -m http.server $PORT
elif command -v npx >/dev/null 2>&1; then
  echo "Serveur local : $URL  (ferme cette fenêtre pour l'arrêter)"
  (sleep 3; open "$URL") &
  npx --yes http-server -p $PORT -c-1 .
else
  echo "Ni Python ni Node trouvés : ouverture directe du fichier."
  open index.html
fi
