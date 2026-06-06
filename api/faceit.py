"""
api/faceit.py
-------------
All communication with the Faceit Data API v4.
Every function makes an HTTP GET request and returns the parsed JSON.

Base URL: https://open.faceit.com/data/v4
Auth:     Bearer token (your API key) in the Authorization header.

Functions:
  get_player()             — find a player by nickname
  get_player_details()     — get full profile (ELO, level, etc.)
  get_player_stats()       — get lifetime CS2 stats (K/D, win rate, etc.)
  get_active_match()       — check if the player is currently in a match room
  get_match()              — get full details for a specific match
  get_match_player_stats() — fetch all 10 players' details + stats in parallel
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://open.faceit.com/data/v4"


def _headers(api_key):
    """Build the auth header required by every Faceit API request."""
    return {"Authorization": f"Bearer {api_key}"}


def get_player(api_key, nickname):
    """
    Look up a player by their Faceit nickname.
    Returns their player_id, avatar URL, skill level, etc.
    Raises an exception if the nickname doesn't exist.
    """
    resp = requests.get(
        f"{BASE_URL}/players",
        params={"nickname": nickname, "game": "cs2"},
        headers=_headers(api_key),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_player_details(api_key, player_id):
    """
    Get full player profile by player ID.
    Includes ELO, skill level, country, memberships, etc.
    """
    resp = requests.get(
        f"{BASE_URL}/players/{player_id}",
        headers=_headers(api_key),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_player_stats(api_key, player_id):
    """
    Get a player's lifetime CS2 statistics.
    Returns a dict with 'lifetime' (overall averages) and 'segments' (per-map stats).

    Key lifetime fields:
      - 'Average K/D Ratio'
      - 'Win Rate %'
      - 'Average Headshots %'
      - 'Average Kills'
      - 'Matches'
    """
    resp = requests.get(
        f"{BASE_URL}/players/{player_id}/stats/cs2",
        headers=_headers(api_key),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_active_match(api_key, player_id):
    """
    Check if a player is currently in an active match room.

    How it works:
      1. Fetch the player's most recent match from history (limit=1)
      2. If the match status is not FINISHED or CANCELLED, it's still active
      3. Return the match_id if active, otherwise None

    Returns: match_id string or None
    """
    resp = requests.get(
        f"{BASE_URL}/players/{player_id}/history",
        params={"game": "cs2", "limit": 1},
        headers=_headers(api_key),
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    if not items:
        return None

    latest = items[0]
    status = latest.get("status", "")

    # If the match isn't finished/cancelled, the player is still in it
    if status not in ("FINISHED", "CANCELLED"):
        return latest["match_id"]

    return None


def get_match(api_key, match_id):
    """
    Get full details for a match — teams, rosters, map voting, status.
    The roster contains each player's nickname, player_id, and avatar.
    """
    resp = requests.get(
        f"{BASE_URL}/matches/{match_id}",
        headers=_headers(api_key),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_match_player_stats(api_key, match):
    """
    Fetch details + stats for all 10 players in a match simultaneously.

    Uses ThreadPoolExecutor to make all API calls in parallel instead of
    one by one — fetching 10 players takes ~2s instead of ~20s.

    Returns a list of dicts, each containing:
      id, nickname, avatar, details (ELO/level), stats (K/D/win rate/etc.)
    """
    # Collect all players from both teams
    all_players = []
    for faction_key in ("faction1", "faction2"):
        roster = match.get("teams", {}).get(faction_key, {}).get("roster", [])
        all_players.extend(roster)

    def fetch_one(player):
        """Fetch details and stats for a single player. Errors are swallowed so one
        bad player doesn't break the whole match view."""
        try:
            details = get_player_details(api_key, player["player_id"])
        except Exception:
            details = None
        try:
            stats = get_player_stats(api_key, player["player_id"])
        except Exception:
            stats = None
        return {
            "id": player["player_id"],
            "nickname": player["nickname"],
            "avatar": player.get("avatar", ""),
            "details": details,
            "stats": stats,
        }

    results = []
    # max_workers=10 — one thread per player, all fetched at the same time
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_one, p): p for p in all_players}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                pass

    return results
