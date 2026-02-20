import requests
import time
import os
from datetime import datetime

# ==============================
# CONFIG RAILWAY
# ==============================

API_KEY = os.environ["API_KEY"]
WEBHOOK = os.environ["WEBHOOK"]

GAME_REGION = os.getenv("GAME_REGION", "euw1")
ACCOUNT_REGION = os.getenv("ACCOUNT_REGION", "europe")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Liste joueurs depuis Railway
PLAYERS_ENV = os.environ.get("PLAYERS", "")
PLAYERS = [p.strip() for p in PLAYERS_ENV.split(",") if p.strip()]

# ==============================
# UTILS
# ==============================

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
    try:
        requests.post(WEBHOOK, json=data, timeout=10)
    except Exception as e:
        log(f"Erreur Discord: {e}")

def riot_get(url):
    headers = {"X-Riot-Token": API_KEY}
    return requests.get(url, headers=headers, timeout=10)

# ==============================
# CONVERSION RiotID → SUMMONER_ID
# ==============================

def get_summoner_id(riot_id):
    try:
        game_name, tag = riot_id.split("#")
    except:
        log(f"Format RiotID invalide: {riot_id}")
        return None

    # RiotID → PUUID
    url_account = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}"
    r = riot_get(url_account)

    if r.status_code != 200:
        log(f"Erreur PUUID {riot_id}: {r.status_code}")
        return None

    puuid = r.json()["puuid"]

    # PUUID → SUMMONER_ID
    url_summoner = f"https://{GAME_REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    r = riot_get(url_summoner)

    if r.status_code != 200:
        log(f"Erreur SUMMONER_ID {riot_id}: {r.status_code}")
        return None

    return r.json()["id"]

# ==============================
# INITIALISATION
# ==============================

log("Initialisation joueurs depuis Railway...")

SUMMONERS = {}
for player in PLAYERS:
    sid = get_summoner_id(player)
    if sid:
        SUMMONERS[player] = sid
        log(f"{player} OK")
    else:
        log(f"{player} ignoré")

if not SUMMONERS:
    log("⚠️ Aucun joueur valide trouvé — vérifie la variable PLAYERS")

in_game = {player: False for player in SUMMONERS}

log("Bot démarré")

# ==============================
# LOOP
# ==============================

while True:
    for player, summoner_id in SUMMONERS.items():

        url = f"https://{GAME_REGION}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{summoner_id}"
        r = riot_get(url)

        if r.status_code == 200:
            if not in_game[player]:
                in_game[player] = True
                log(f"{player} EN GAME")
                send_discord(
                    f"🎮 {player} vient de lancer une game",
                    "Game détectée 👀",
                    5763719
                )

        elif r.status_code == 404:
            if in_game[player]:
                in_game[player] = False
                log(f"{player} plus en game")
                send_discord(
                    f"🏁 Game terminée pour {player}",
                    "Fin de partie détectée.",
                    15548997
                )

        elif r.status_code == 403:
            log("⚠️ 403 — Clé invalide, expirée ou région incorrecte")

        elif r.status_code == 429:
            log("⚠️ Rate limit atteint — pause 2 minutes")
            time.sleep(120)

        else:
            log(f"Erreur API {player}: {r.status_code}")

    time.sleep(CHECK_INTERVAL)
