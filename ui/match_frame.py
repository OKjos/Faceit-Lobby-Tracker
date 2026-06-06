"""
ui/match_frame.py
-----------------
Displays the full match room — two teams side by side with a VS divider.

Layout:
  ┌─────────────────────────────────────────────────────┐
  │  MAP NAME                              #match_id     │  ← match header
  ├──────────────────────────┬────┬────────────────────┤
  │  TEAM 1 NAME             │    │  TEAM 2 NAME        │
  │  ┌──────────────────┐   │ VS │  ┌──────────────┐   │
  │  │  PlayerCard      │   │    │  │  PlayerCard  │   │
  │  │  PlayerCard      │   │    │  │  PlayerCard  │   │
  │  │  PlayerCard      │   │    │  │  PlayerCard  │   │
  │  │  PlayerCard      │   │    │  │  PlayerCard  │   │
  │  │  PlayerCard      │   │    │  │  PlayerCard  │   │
  │  └──────────────────┘   │    │  └──────────────┘   │
  └──────────────────────────┴────┴────────────────────┘

Each PlayerCard (see player_card.py) shows stats for one player.
"""

import customtkinter as ctk
from ui.player_card import PlayerCard

BG      = "#0f1116"
BG2     = "#1a1d24"
BORDER  = "#2e3340"
TEXT    = "#e2e8f0"
MUTED   = "#6b7280"
ACCENT  = "#ff5500"


class MatchFrame(ctk.CTkFrame):
    def __init__(self, parent, match, players, my_id):
        """
        match   — full match dict from Faceit API (/matches/{id})
        players — list of enriched player dicts from get_match_player_stats()
        my_id   — the logged-in user's player_id (used to highlight their card)
        """
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.match   = match
        self.players = players
        self.my_id   = my_id
        self._build()

    def _build(self):
        # ── Match header ─────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=BG2, height=46, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Map name from the vote result, e.g. "de_mirage" → "DE_MIRAGE"
        voting = self.match.get("voting") or {}
        map_pick = voting.get("map", {}).get("pick", [])
        map_name = map_pick[0] if map_pick else "TBD"

        # Last 8 chars of match ID as a short reference number
        match_id_short = self.match.get("match_id", "")[-8:]

        ctk.CTkLabel(
            header,
            text=map_name.upper(),
            font=("Segoe UI", 15, "bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            header,
            text=f"#{match_id_short}",
            font=("Segoe UI", 11),
            text_color=MUTED,
        ).pack(side="left")

        # Border below header
        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # ── Teams container ───────────────────────────────────────────────────
        teams = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        teams.pack(fill="both", expand=True)

        faction1 = self.match.get("teams", {}).get("faction1", {})
        faction2 = self.match.get("teams", {}).get("faction2", {})

        # Build sets of player IDs per faction so we can sort players into teams
        f1_ids = {p["player_id"] for p in faction1.get("roster", [])}
        f2_ids = {p["player_id"] for p in faction2.get("roster", [])}

        f1_players = [p for p in self.players if p["id"] in f1_ids]
        f2_players = [p for p in self.players if p["id"] in f2_ids]

        # Team 1 column (left)
        self._team_column(teams, faction1.get("name", "Team 1"), f1_players, side="left")

        # VS divider (center strip)
        vs_bar = ctk.CTkFrame(teams, fg_color=BG2, width=44, corner_radius=0)
        vs_bar.pack(side="left", fill="y")
        vs_bar.pack_propagate(False)
        ctk.CTkLabel(
            vs_bar,
            text="VS",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Team 2 column (right)
        self._team_column(teams, faction2.get("name", "Team 2"), f2_players, side="left")

    def _team_column(self, parent, team_name, players, side):
        """Build one team column: name header + scrollable player list."""
        col = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        col.pack(side=side, fill="both", expand=True)

        # Team name header
        name_bar = ctk.CTkFrame(col, fg_color=BG2, height=36, corner_radius=0)
        name_bar.pack(fill="x")
        name_bar.pack_propagate(False)
        ctk.CTkLabel(
            name_bar,
            text=team_name.upper(),
            font=("Segoe UI", 12, "bold"),
            text_color=TEXT,
        ).pack(side="left", padx=12)

        # Scrollable list of PlayerCard widgets
        scroll = ctk.CTkScrollableFrame(col, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        if not players:
            ctk.CTkLabel(scroll, text="Loading...", text_color=MUTED).pack(pady=20)
        else:
            for player in players:
                PlayerCard(
                    scroll,
                    player=player,
                    is_me=(player["id"] == self.my_id),
                ).pack(fill="x", pady=3)
