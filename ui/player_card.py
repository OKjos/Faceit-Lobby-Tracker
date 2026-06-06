"""
ui/player_card.py
-----------------
One card showing stats for a single player in the match room.

Visual layout:
  ┌─[elo colour bar]──────────────────────────────────────────────┐
  │ [avatar] Nickname   K/D  Win%  HS%  Games   1234 ELO          │
  │          Lvl 7                                                 │
  │  ─────────────────────────────────────────────────────────    │
  │  Mirage 62% 8g  Dust2 55% 4g  Inferno N/A 0g  Nuke 44% 2g   │
  └───────────────────────────────────────────────────────────────┘

Stats displayed:
  - K/D ratio        (green if >= 1.2)
  - Win rate %
  - Headshot rate %
  - Total matches played
  - ELO              (coloured by tier)
  - Skill level badge (1-3 green, 4 lime, 5-6 yellow, 7-9 orange, 10 red)
  - Map win rates + games played for all maps in MAP_NAMES pool

Avatar images are loaded from Faceit's CDN in a background thread.
"""

import threading
import customtkinter as ctk
import requests
from io import BytesIO
from PIL import Image

# ── Map pool — edit this when Valve changes the pool ─────────────────────────
# Keys must match the label the Faceit API returns (e.g. "Mirage", "Dust2").
# Values are what shows on the card. Only maps listed here are displayed.
MAP_NAMES = {
    "Dust2":    "Dust 2",
    "Mirage":   "Mirage",
    "Nuke":     "Nuke",
    "Ancient":  "Ancient",
    "Inferno":  "Inferno",
    "Overpass": "Overpass",
    "Anubis":   "Anubis",
    "Cache":    "Cache",
}

# ── Colours ──────────────────────────────────────────────────────────────────
BG2       = "#1a1d24"
BG3       = "#22262f"
BG4       = "#0f1116"
BORDER    = "#2e3340"
ME_BORDER = "#f5a623"
TEXT      = "#e2e8f0"
MUTED     = "#6b7280"
GREEN     = "#34d399"   # good K/D / high win rate
YELLOW    = "#fbbf24"   # average win rate
RED_MUTED = "#f87171"   # low win rate
ME_COLOR  = "#f5a623"   # gold — logged-in user's name


# ── Level colours: each level gets its own shade within its tier group ────────
# 1-3: green (light -> dark), 4: lime bridge, 5-6: yellow, 7-9: orange, 10: red
_LEVEL_COLORS = {
    1:  "#86efac",  # light green
    2:  "#22c55e",  # medium green
    3:  "#15803d",  # dark green
    4:  "#bef264",  # lime — bridge between green and yellow
    5:  "#fde047",  # light yellow
    6:  "#ca8a04",  # dark yellow / amber
    7:  "#fdba74",  # light orange
    8:  "#f97316",  # medium orange
    9:  "#c2410c",  # dark orange / red-orange
    10: "#ef4444",  # red
}


def _level_color(level):
    """Return the badge colour for a given Faceit skill level (1-10)."""
    try:
        return _LEVEL_COLORS.get(int(level), "#6b7280")
    except (TypeError, ValueError):
        return "#6b7280"


def _elo_color(elo):
    """Return a hex colour string based on ELO tier — used for the left accent bar and ELO label."""
    if not elo:     return "#4b5563"  # no data — dark grey
    if elo >= 2001: return "#f5a623"  # Diamond / Elite — orange
    if elo >= 1501: return "#a78bfa"  # Platinum — purple
    if elo >= 1001: return "#60a5fa"  # Gold — blue
    if elo >= 501:  return "#34d399"  # Silver — green
    return "#9ca3af"                   # Bronze — grey


def _win_rate_color(win_rate_pct):
    """Colour-code a map win rate: green >= 55%, yellow >= 45%, red below."""
    if win_rate_pct >= 55: return GREEN
    if win_rate_pct >= 45: return YELLOW
    return RED_MUTED


def _safe_float(value, fallback=0.0):
    """Convert a stat string to float without crashing on missing data."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _top_maps(segments):
    """Return (display_name, win_rate_or_None, matches_or_0) for all pool maps.
    Played maps first (sorted by matches), then unplayed maps."""
    played, seen = [], set()
    for seg in segments:
        if seg.get("type") != "Map":
            continue
        label = seg.get("label", "")
        if label not in MAP_NAMES:
            continue
        seg_stats = seg.get("stats", {})
        matches   = int(_safe_float(seg_stats.get("Matches", 0)))
        win_rate  = int(_safe_float(seg_stats.get("Win Rate %", 0)))
        seen.add(label)
        if matches > 0:
            played.append((MAP_NAMES[label], win_rate, matches))
    played.sort(key=lambda x: x[2], reverse=True)
    result = list(played)
    for label, display in MAP_NAMES.items():
        if label not in seen:
            result.append((display, None, 0))
    return result


class PlayerCard(ctk.CTkFrame):
    def __init__(self, parent, player, is_me=False):
        """
        player — dict with: id, nickname, avatar, details, stats
        is_me  — True if this is the logged-in user (adds gold border + gold name)
        """
        border_color = ME_BORDER if is_me else BORDER
        super().__init__(
            parent,
            fg_color=BG2,
            border_width=1,
            border_color=border_color,
            corner_radius=6,
        )
        self.player = player
        self.is_me  = is_me
        self._build()

        # Load avatar in a background thread — won't freeze the UI while downloading
        if player.get("avatar"):
            threading.Thread(target=self._load_avatar, daemon=True).start()

    def _build(self):
        # Pull all data out of the nested API response dicts upfront
        stats_data = self.player.get("stats") or {}
        lifetime   = stats_data.get("lifetime") or {}
        segments   = stats_data.get("segments") or []
        details    = self.player.get("details") or {}
        games      = details.get("games", {}).get("cs2", {})

        elo   = games.get("faceit_elo")
        level = games.get("skill_level")

        # Format lifetime stats — fall back to "—" if data is missing
        kd       = f"{_safe_float(lifetime.get('Average K/D Ratio')):.2f}" if lifetime else "—"
        win_rate = f"{round(_safe_float(lifetime.get('Win Rate %')))}%"    if lifetime else "—"
        hs_rate  = f"{round(_safe_float(lifetime.get('Average Headshots %')))}%" if lifetime else "—"
        matches  = lifetime.get("Matches", "—")

        # K/D highlighted green when 1.2 or above (better than average)
        kd_color = GREEN if _safe_float(lifetime.get("Average K/D Ratio")) >= 1.2 else TEXT

        top_maps = _top_maps(segments)

        # ── Left accent bar: coloured strip showing ELO tier at a glance ────
        accent = ctk.CTkFrame(self, fg_color=_elo_color(elo), width=4, corner_radius=0)
        accent.pack(side="left", fill="y")

        # ── Main content area ────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(6, 8), pady=5)

        # ── Left section: avatar + name, anchored top-left ──────────────────
        left_section = ctk.CTkFrame(content, fg_color="transparent")
        left_section.pack(side="left", anchor="n", pady=(1, 0))

        # Avatar — circular placeholder, real image loaded async
        self.avatar_label = ctk.CTkLabel(
            left_section, text="", width=36, height=36,
            fg_color=BG3, corner_radius=18,
        )
        self.avatar_label.pack(side="left", padx=(0, 7), anchor="n", pady=(1, 0))

        # Name + level badge stacked, anchored top-left
        name_col = ctk.CTkFrame(left_section, fg_color="transparent", width=138)
        name_col.pack(side="left", anchor="n")
        name_col.pack_propagate(False)

        name_color = ME_COLOR if self.is_me else TEXT
        ctk.CTkLabel(
            name_col,
            text=self.player["nickname"],
            font=("Segoe UI", 13, "bold"),
            text_color=name_color,
            anchor="w",
        ).pack(anchor="w")

        if level:
            # Coloured pill — shade depends on level tier (1-3 green, 5-6 yellow, 7-9 orange, 10 red)
            ctk.CTkLabel(
                name_col,
                text=f" Lvl {level} ",
                font=("Segoe UI", 10, "bold"),
                text_color=BG4,
                fg_color=_level_color(level),
                corner_radius=3,
            ).pack(anchor="w", pady=(2, 0))

        # ── Right section: stats + ELO on top, map chips below ───────────────
        # Both rows live in the same container so maps naturally align under stats
        right_section = ctk.CTkFrame(content, fg_color="transparent")
        right_section.pack(side="left", fill="both", expand=True)

        # Stats + ELO row — centered within right_section
        stats_row = ctk.CTkFrame(right_section, fg_color="transparent")
        stats_row.pack(fill="x")

        # anchor="w" keeps stats left-aligned inside right_section — prevents right-side clipping
        stats_inner = ctk.CTkFrame(stats_row, fg_color="transparent")
        stats_inner.pack(anchor="w", padx=(8, 0))

        self._stat_col(stats_inner, kd,           "K/D",   kd_color)
        self._stat_col(stats_inner, win_rate,     "Win%",  TEXT)
        self._stat_col(stats_inner, hs_rate,      "HS%",   TEXT)
        self._stat_col(stats_inner, str(matches), "Games", TEXT)

        # ELO sits just to the right of the stat columns with a small gap
        if elo:
            ctk.CTkLabel(
                stats_inner,
                text=f"{elo} ELO",
                font=("Segoe UI", 16, "bold"),
                text_color=_elo_color(elo),
            ).pack(side="left", padx=(8, 0))

        # ── Divider between stats and map row ─────────────────────────────────
        if top_maps:
            ctk.CTkFrame(right_section, fg_color=BORDER, height=1, corner_radius=0).pack(
                fill="x", pady=(4, 3)
            )

            # ── Map win rate chips — centered under stats in the same section ──
            # Each chip shows map name + win rate, colour-coded by performance
            maps_row = ctk.CTkFrame(right_section, fg_color="transparent")
            maps_row.pack(fill="x")

            # Grid layout: 2 chips per row, sorted by most played
            chips = ctk.CTkFrame(maps_row, fg_color="transparent")
            chips.pack(anchor="w", padx=(8, 0))

            for i, (map_name, wr, games) in enumerate(top_maps):
                wr_text    = f"{wr}%" if wr is not None else "N/A"
                wr_color   = _win_rate_color(wr) if wr is not None else MUTED
                games_text = f"{games}g" if games > 0 else "0g"

                chip = ctk.CTkFrame(chips, fg_color=BG3, corner_radius=4)
                chip.grid(row=i // 2, column=i % 2, padx=(0, 5), pady=(0, 3), sticky="w")

                ctk.CTkLabel(
                    chip,
                    text=map_name,
                    font=("Segoe UI", 12),
                    text_color=MUTED,
                ).pack(side="left", padx=(5, 0), pady=2)

                ctk.CTkLabel(
                    chip,
                    text=wr_text,
                    font=("Segoe UI", 12, "bold"),
                    text_color=wr_color,
                ).pack(side="left", padx=(6, 0), pady=2)

                ctk.CTkLabel(
                    chip,
                    text=games_text,
                    font=("Segoe UI", 12),
                    text_color=MUTED,
                ).pack(side="left", padx=(3, 5), pady=2)

    def _stat_col(self, parent, value, label, color):
        """One stat block: value on top, small muted label below."""
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left", padx=4)
        ctk.CTkLabel(col, text=value, font=("Segoe UI", 16, "bold"), text_color=color).pack()
        ctk.CTkLabel(col, text=label, font=("Segoe UI", 12),          text_color=MUTED).pack()

    def _load_avatar(self):
        """
        Download the player's avatar image from Faceit's CDN.
        Runs on a background thread. Updates the label on the main thread
        via after() — direct widget updates from threads crash Tkinter.
        """
        try:
            resp    = requests.get(self.player["avatar"], timeout=5)
            img     = Image.open(BytesIO(resp.content)).resize((36, 36))
            ctk_img = ctk.CTkImage(img, size=(36, 36))
            # Schedule the UI update back on the main thread
            self.after(0, lambda: self.avatar_label.configure(
                image=ctk_img, text="", fg_color="transparent"
            ))
        except Exception:
            pass  # Avatar fails silently — circular placeholder stays
