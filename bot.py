import requests
import time
import os
from datetime import datetime

# ==============================
# CONFIG RAILWAY
# ==============================
API_KEY = os.environ["API_KEY"]
WEBHOOK = os.environ["WEBHOOK"]
GAME_REGION = os.getenv("GAME_REGION", "euw1")  # serveur des joueurs
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "120"))

# Liste des amis à suivre (summonerId) séparés par des virgules
FRIEND_IDS_ENV = os.environ.get("FRIEND_IDS", "")
FRIEND_IDS = [fid.strip() for fid in FRIEND_IDS_ENV.split(",") if fid.strip()]

# ==============================
# UTILS
# ==============================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(title, desc, color=5814783):
    data = {"embeds": [{"title": title, "description": desc, "color": color}]}
    try:
        requests.post(WEBHOOK, json=data, timeout=10)
    except Exception as e:
        log(f"Erreur Discord: {e}")

def riot_get(url):
    headers = {"X-Riot-Token": API_KEY}
    return requests.get(url, headers=headers, timeout=10)

# ==============================
# INITIALISATION
# ==============================
log("Initialisation amis depuis Railway...")

if not FRIEND_IDS:
    log("⚠️ Aucun summonerId trouvé dans FRIEND_IDS, arrête le bot.")
    exit(1)

in_game = {fid: False for fid in FRIEND_IDS}

log(f"Bot démarré pour {len(FRIEND_IDS)} amis.")

# ==============================
# LOOP PRINCIPALE
# ==============================
while True:
    for fid in FRIEND_IDS:
        url = f"https://{GAME_REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{fid}"
        r = riot_get(url)

        if r.status_code == 200:
            if not in_game[fid]:
                in_game[fid] = True
                log(f"{fid} EN GAME")
                send_discord(
                    f"🎮 Un ami vient de lancer une game",
                    f"SummonerId: {fid} est en jeu 👀",
                    5763719
                )

        elif r.status_code == 404:
            if in_game[fid]:
                in_game[fid] = False
                log(f"{fid} plus en game")
                send_discord(
                    f"🏁 Partie terminée",
                    f"SummonerId: {fid} a terminé sa game",
                    15548997
                )

        elif r.status_code == 403:
            log("⚠️ 403 — Clé API invalide, expirée ou serveur incorrect")

        elif r.status_code == 429:
            log("⚠️ Rate limit atteint — pause 2 minutes")
            time.sleep(120)

        else:
            log(f"Erreur API {fid}: {r.status_code}")

    time.sleep(CHECK_INTERVAL)
