import requests
import time
import os
from datetime import datetime

# ==============================
# CONFIG RAILWAY
# ==============================
API_KEY = os.environ["API_KEY"]
WEBHOOK = os.environ["WEBHOOK"]
GAME_REGION = os.getenv("GAME_REGION", "europe")  # pour spectator/v5, correspond à la région (europe pour EUW)
ACCOUNT_REGION = os.getenv("ACCOUNT_REGION", "europe")  # pour account/v1
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
DISCORD_MENTION = os.getenv("DISCORD_MENTION", "")

# Liste des Riot IDs à suivre
FRIEND_IDS_ENV = os.environ.get("FRIEND_IDS", "")
FRIEND_IDS = [fid.strip() for fid in FRIEND_IDS_ENV.split(",") if fid.strip()]

# ==============================
# UTILS
# ==============================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(title, desc, color=5814783):
    content = DISCORD_MENTION if DISCORD_MENTION else ""
    data = {
        "content": content,
        "allowed_mentions": {"parse": ["users", "roles"]},
        "embeds": [{"title": title, "description": desc, "color": color}]
    }
    try:
        requests.post(WEBHOOK, json=data, timeout=10)
    except Exception as e:
        log(f"Erreur Discord: {e}")

def riot_get(url):
    headers = {"X-Riot-Token": API_KEY}
    return requests.get(url, headers=headers, timeout=10)

def get_puuid(riot_id):
    """Récupère le PUUID depuis RiotID#Tag"""
    try:
        name, tag = riot_id.split("#")
    except:
        log(f"Format RiotID invalide: {riot_id}")
        return None

    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    r = riot_get(url)
    if r.status_code == 200:
        data = r.json()
        puuid = data.get("puuid")
        log(f"PUUID pour {riot_id} : {puuid}")
        return puuid
    else:
        log(f"Impossible de récupérer PUUID {riot_id}: {r.status_code} / {r.text}")
        return None

# ==============================
# INITIALISATION
# ==============================
log("Initialisation joueurs depuis Railway...")

if not FRIEND_IDS:
    log("⚠️ Aucun RiotID trouvé dans FRIEND_IDS, arrête le bot.")
    exit(1)

# Map RiotID → PUUID
PUUID_MAP = {}
for riot_id in FRIEND_IDS:
    puuid = get_puuid(riot_id)
    if puuid:
        PUUID_MAP[riot_id] = puuid
    else:
        log(f"{riot_id} ignoré (PUUID non trouvé)")

if not PUUID_MAP:
    log("⚠️ Aucun joueur valide trouvé, arrête le bot.")
    exit(1)

# Etat in_game
in_game = {riot_id: False for riot_id in PUUID_MAP}
log(f"Bot démarré pour {len(PUUID_MAP)} joueurs.")

# ==============================
# LOOP PRINCIPALE
# ==============================
while True:
    for riot_id, puuid in PUUID_MAP.items():
        url = f"https://{GAME_REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
        r = riot_get(url)

        if r.status_code == 200:
            if not in_game[riot_id]:
                in_game[riot_id] = True
                log(f"{riot_id} EN GAME")
                send_discord(
                    f"🎮 {riot_id} vient de lancer une game",
                    f"{riot_id} est en jeu 👀",
                    5763719
                )
        elif r.status_code == 404:
            if in_game[riot_id]:
                in_game[riot_id] = False
                log(f"{riot_id} plus en game")
                send_discord(
                    f"🏁 Partie terminée pour {riot_id}",
                    f"{riot_id} a terminé sa game",
                    15548997
                )
            else:
                # Log pour dire que le joueur n'est pas en game
                log(f"{riot_id} n'est pas en game")
                send_discord(
                    f"ℹ️ {riot_id} n'est pas en game",
                    f"{riot_id} est actuellement hors partie",
                    15548997
                )
        elif r.status_code == 403:
            log(f"⚠️ 403 clé API invalide/expirée pour {riot_id}")
        elif r.status_code == 429:
            log("⚠️ Rate limit atteint — pause 2 minutes")
            time.sleep(120)
        else:
            log(f"Erreur API {riot_id}: {r.status_code}")

    time.sleep(CHECK_INTERVAL)
