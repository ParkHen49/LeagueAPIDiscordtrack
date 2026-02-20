import requests
import time
import os
from datetime import datetime

API_KEY = os.environ["API_KEY"]
WEBHOOK = os.environ["WEBHOOK"]

REGION = "euw1"
CHECK_INTERVAL = 30

PLAYERS = {
    "Joueur1": "SUMMONER_ID_1",
    "Joueur2": "SUMMONER_ID_2",
}

in_game = {name: False for name in PLAYERS}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(title, desc, color=5814783):
    data = {
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color
        }]
    }
    requests.post(WEBHOOK, json=data)

def check_player(name, summoner_id):
    global in_game

    url = f"https://{REGION}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}?api_key={API_KEY}"

    try:
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            if not in_game[name]:
                in_game[name] = True
                log(f"{name} EN GAME")
                send_discord(
                    f"🎮 {name} vient de lancer une game",
                    "Surveille le client 👀",
                    5763719
                )

        elif r.status_code == 404:
            if in_game[name]:
                in_game[name] = False
                log(f"{name} plus en game")
                send_discord(
                    f"🏁 Game terminée pour {name}",
                    "Check le résultat !",
                    15548997
                )

        elif r.status_code == 403:
            log("⚠️ Clé Riot expirée")

        else:
            log(f"Erreur API {name}: {r.status_code}")

    except Exception as e:
        log(f"Erreur réseau {name}: {e}")

log("Bot démarré")

while True:
    for name, sid in PLAYERS.items():
        check_player(name, sid)

    time.sleep(CHECK_INTERVAL)
