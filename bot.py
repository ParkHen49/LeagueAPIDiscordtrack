import requests
import time
import os
from datetime import datetime

# ==============================
# CONFIG RAILWAY
# ==============================
API_KEY = os.environ["API_KEY"]
WEBHOOK = os.environ["WEBHOOK"]
GAME_REGION = os.getenv("GAME_REGION", "euw1")  # serveur du joueur
ACCOUNT_REGION = os.getenv("ACCOUNT_REGION", "europe")  # pour account API
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

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

def get_account_info(riot_id):
    """Récupère les infos publiques via account/v1 API"""
    try:
        game_name, tag = riot_id.split("#")
    except:
        log(f"Format RiotID invalide: {riot_id}")
        return None

    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}"
    r = riot_get(url)
    if r.status_code == 200:
        data = r.json()
        log(f"Infos compte {riot_id} : puuid={data.get('puuid')}, gameName={data.get('gameName')}, tagLine={data.get('tagLine')}, level={data.get('summonerLevel','N/A')}")
        return data
    else:
        log(f"Impossible de récupérer infos {riot_id}: {r.status_code} / {r.text}")
        return None

# ==============================
# INITIALISATION
# ==============================
log("Initialisation amis depuis Railway...")

if not FRIEND_IDS:
    log("⚠️ Aucun summonerId trouvé dans FRIEND_IDS, arrête le bot.")
    exit(1)

in_game = {fid: False for fid in FRIEND_IDS}

# Affichage infos comptes amis
for fid in FRIEND_IDS:
    get_account_info(fid)  # affiche dans logs

log(f"Bot démarré pour {len(FRIEND_IDS)} amis.")

# ==============================
# LOOP PRINCIPALE
# ==============================
while True:
    for fid in FRIEND_IDS:
        url = f"https://{GAME_REGION}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{fid}"
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
            else:
                # Nouveau log pour dire que le joueur n'est pas en game
                log(f"{fid} n'est pas en game")
        elif r.status_code == 403:
            log("⚠️ 403 — Clé API invalide, expirée ou serveur incorrect")
        elif r.status_code == 429:
            log("⚠️ Rate limit atteint — pause 2 minutes")
            time.sleep(120)
        else:
            log(f"Erreur API {fid}: {r.status_code}")

    time.sleep(CHECK_INTERVAL)
