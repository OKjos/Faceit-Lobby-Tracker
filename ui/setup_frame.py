"""
ui/setup_frame.py
-----------------
The first screen the user sees if they haven't connected yet.

Contains:
  - FACEIT COMPANION logo/title
  - Nickname input field
  - API key input field (hidden with dots)
  - Connect button
  - Error message display

When the user clicks Connect, it calls on_connect(nickname, api_key)
which is provided by app.py. The actual API call happens in app.py on
a background thread so the UI doesn't freeze.
"""

import customtkinter as ctk

# ── Colour palette (matches the dark Faceit theme) ──────────────────────────
BG      = "#0f1116"   # main window background
BG2     = "#1a1d24"   # card / panel background
BG3     = "#22262f"   # input field background
BORDER  = "#2e3340"   # border lines
TEXT    = "#e2e8f0"   # primary text
MUTED   = "#6b7280"   # secondary / label text
ACCENT  = "#ff5500"   # Faceit orange


class SetupFrame(ctk.CTkFrame):
    """Login card shown in the center of the window."""

    def __init__(self, parent, on_connect):
        super().__init__(parent, fg_color=BG)
        self.on_connect = on_connect  # callback: fn(nickname, api_key)
        self._build()

    def _build(self):
        # Centered card — uses place() so it stays centered on resize
        card = ctk.CTkFrame(
            self,
            fg_color=BG2,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
            width=420,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # ── Logo ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="FACEIT",
            font=("Segoe UI", 30, "bold"),
            text_color=ACCENT,
        ).pack(pady=(36, 0))

        ctk.CTkLabel(
            card,
            text="COMPANION",
            font=("Segoe UI", 11),
            text_color=MUTED,
        ).pack(pady=(0, 32))

        # ── Nickname field ───────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="FACEIT NICKNAME",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=36)

        self.nickname_var = ctk.StringVar()
        ctk.CTkEntry(
            card,
            textvariable=self.nickname_var,
            placeholder_text="your_nickname",
            fg_color=BG3,
            border_color=BORDER,
            text_color=TEXT,
            height=42,
            width=348,
            corner_radius=6,
        ).pack(padx=36, pady=(4, 18))

        # ── API key field ────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="API KEY",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=36)

        self.apikey_var = ctk.StringVar()
        ctk.CTkEntry(
            card,
            textvariable=self.apikey_var,
            placeholder_text="Paste your Faceit API key here",
            show="•",                    # hides the key with dots
            fg_color=BG3,
            border_color=BORDER,
            text_color=TEXT,
            height=42,
            width=348,
            corner_radius=6,
        ).pack(padx=36, pady=(4, 4))

        ctk.CTkLabel(
            card,
            text="Stored locally on your PC. Never sent anywhere except Faceit.",
            font=("Segoe UI", 10),
            text_color=MUTED,
        ).pack(padx=36, pady=(0, 18))

        # ── Error message (hidden until an error occurs) ─────────────────────
        self.error_label = ctk.CTkLabel(
            card,
            text="",
            font=("Segoe UI", 12),
            text_color="#f87171",  # red
        )
        self.error_label.pack(padx=36, pady=(0, 8))

        # ── Connect button ───────────────────────────────────────────────────
        self.connect_btn = ctk.CTkButton(
            card,
            text="Connect",
            command=self._on_click,
            fg_color=ACCENT,
            hover_color="#ff7733",
            text_color="white",
            font=("Segoe UI", 14, "bold"),
            height=46,
            width=348,
            corner_radius=6,
        )
        self.connect_btn.pack(padx=36, pady=(0, 36))

    def _on_click(self):
        """Validate inputs then hand off to app.py via the on_connect callback."""
        nickname = self.nickname_var.get().strip()
        api_key  = self.apikey_var.get().strip()
        if not nickname or not api_key:
            return
        # Disable button while the API call is in progress
        self.connect_btn.configure(text="Connecting...", state="disabled")
        self.error_label.configure(text="")
        self.on_connect(nickname, api_key)

    def show_error(self, message):
        """Called from app.py (on main thread) when login fails."""
        self.error_label.configure(text=message)
        self.connect_btn.configure(text="Connect", state="normal")
