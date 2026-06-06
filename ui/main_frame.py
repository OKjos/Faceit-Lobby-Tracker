"""
ui/main_frame.py
----------------
The main screen shown after the user connects.

Layout (top to bottom):
  1. StatusBar  — shows nickname, current status, last-checked time, logout button
  2. Content area — either:
       • WaitingView  — "Waiting for match room..." message shown when idle
       • MatchFrame   — full 5v5 stats display when a match is detected

This frame never makes API calls itself — app.py handles all that and
calls show_match() / show_waiting() / update_last_checked() from the main thread.
"""

import customtkinter as ctk
from datetime import datetime
from ui.match_frame import MatchFrame

# ── Colour palette ───────────────────────────────────────────────────────────
BG      = "#0f1116"
BG2     = "#1a1d24"
BORDER  = "#2e3340"
TEXT    = "#e2e8f0"
MUTED   = "#6b7280"
GREEN   = "#34d399"
BLUE    = "#60a5fa"
ME_COLOR = "#f5a623"  # gold — used to highlight the user's own nickname


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, config, on_logout):
        """
        config   — dict with: nickname, player_id, api_key, avatar
        on_logout — callback: fn() called when user clicks Logout
        """
        super().__init__(parent, fg_color=BG)
        self.config = config
        self.on_logout = on_logout
        self._build()
        self._show_waiting_view()  # start with the waiting state

    def _build(self):
        # ── Status bar ───────────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=BG2, height=48, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Left: player nickname (highlighted in gold so user can spot themselves)
        ctk.CTkLabel(
            bar,
            text=self.config["nickname"],
            font=("Segoe UI", 13, "bold"),
            text_color=ME_COLOR,
        ).pack(side="left", padx=14)

        # Right: logout button
        ctk.CTkButton(
            bar,
            text="Logout",
            command=self.on_logout,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=MUTED,
            hover_color=BG,
            font=("Segoe UI", 11),
            width=72,
            height=28,
            corner_radius=6,
        ).pack(side="right", padx=12)

        # Center: status label + last-checked time
        center = ctk.CTkFrame(bar, fg_color="transparent")
        center.pack(side="left", expand=True)

        self.status_label = ctk.CTkLabel(
            center,
            text="● Watching",
            font=("Segoe UI", 12, "bold"),
            text_color=GREEN,
        )
        self.status_label.pack(side="left", padx=8)

        self.time_label = ctk.CTkLabel(
            center,
            text="",
            font=("Segoe UI", 11),
            text_color=MUTED,
        )
        self.time_label.pack(side="left")

        # 1px border line below the status bar
        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # ── Content area — swapped between waiting and match views ───────────
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.pack(fill="both", expand=True)

    # ── Public methods called by app.py ──────────────────────────────────────

    def show_match(self, match, players):
        """Replace content with the match room (called when a match is detected)."""
        self._clear_content()
        self.status_label.configure(text="● In Match", text_color=BLUE)
        MatchFrame(
            self.content,
            match=match,
            players=players,
            my_id=self.config["player_id"],
        ).pack(fill="both", expand=True)

    def show_waiting(self):
        """Replace content with the waiting message (called when match ends)."""
        self.status_label.configure(text="● Watching", text_color=GREEN)
        self._clear_content()
        self._show_waiting_view()

    def update_last_checked(self):
        """Update the 'Last check: HH:MM:SS' label in the status bar."""
        t = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=f"Last check: {t}")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_waiting_view(self):
        """Idle view — shown while polling and no match is active."""
        ctk.CTkLabel(
            self.content,
            text="[ CS2 ]",
            font=("Segoe UI", 40, "bold"),
            text_color=MUTED,
        ).pack(pady=(110, 12))

        ctk.CTkLabel(
            self.content,
            text="Waiting for match room...",
            font=("Segoe UI", 17),
            text_color=TEXT,
        ).pack()

        ctk.CTkLabel(
            self.content,
            text="Checks every 15 seconds. Queue up in Faceit to see lobby stats.",
            font=("Segoe UI", 12),
            text_color=MUTED,
        ).pack(pady=(6, 0))
