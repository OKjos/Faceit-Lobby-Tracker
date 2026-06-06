"""
app.py
------
Entry point and main controller for the Faceit Companion desktop app.

Responsibilities:
  1. Create the window (1100×750, dark background)
  2. Decide which screen to show (Setup or Main) based on saved config
  3. Handle the Connect flow: validate on a background thread, save config, switch screens
  4. Run the polling loop: every 15 seconds, check if the user is in a match
  5. When a match is detected, fetch all player stats and update the UI
  6. Handle Logout: cancel polling, clear config, return to Setup screen

Threading model:
  - ALL API calls run on daemon background threads (threading.Thread)
  - ALL UI updates use self.after(0, fn) to run back on the main thread
  - This prevents the window from freezing during network requests

Run with:
  python app.py
"""

import threading
import customtkinter as ctk

from config import load_config, save_config
from api.faceit import get_player, get_active_match, get_match, get_match_player_stats
from ui.setup_frame import SetupFrame
from ui.main_frame import MainFrame

# How often (ms) to poll Faceit for an active match
POLL_INTERVAL_MS = 15_000


class FaceitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window setup ─────────────────────────────────────────────────────
        self.title("Faceit Companion")
        self.geometry("1100x750")
        self.minsize(800, 600)
        self.configure(fg_color="#0f1116")

        # ── App state ─────────────────────────────────────────────────────────
        self.config_data     = load_config()   # dict from ~/.faceit_companion.json, or None
        self.current_match_id = None           # ID of the match currently displayed
        self.poll_after_id   = None            # handle for the scheduled poll (used to cancel)

        # ── Show initial screen ───────────────────────────────────────────────
        if self.config_data:
            self._show_main()   # already logged in from a previous session
        else:
            self._show_setup()  # first time — ask for nickname + API key

    # ── Screen switching ──────────────────────────────────────────────────────

    def _show_setup(self):
        """Replace current screen with the login/setup card."""
        self._clear_window()
        self.setup_frame = SetupFrame(self, on_connect=self._handle_connect)
        self.setup_frame.pack(fill="both", expand=True)

    def _show_main(self):
        """Replace current screen with the main app (status bar + match area)."""
        self._clear_window()
        self.main_frame = MainFrame(
            self,
            config=self.config_data,
            on_logout=self._handle_logout,
        )
        self.main_frame.pack(fill="both", expand=True)
        self._start_polling()

    def _clear_window(self):
        """Destroy all current child widgets."""
        for widget in self.winfo_children():
            widget.destroy()

    # ── Connect flow ──────────────────────────────────────────────────────────

    def _handle_connect(self, nickname, api_key):
        """
        Called when user clicks Connect on the setup screen.
        Runs the API call on a background thread to avoid freezing the UI.
        """
        def do_connect():
            try:
                player = get_player(api_key, nickname)
                cfg = {
                    "nickname":  player["nickname"],
                    "player_id": player["player_id"],
                    "api_key":   api_key,
                    "avatar":    player.get("avatar", ""),
                }
                save_config(cfg)
                self.config_data = cfg
                # Switch to main screen on the main thread
                self.after(0, self._show_main)
            except Exception as e:
                # Show error message back on the main thread
                err_msg = str(e)
                if hasattr(e, "response") and e.response is not None:
                    err_msg = e.response.json().get("message", err_msg)
                self.after(0, lambda: self.setup_frame.show_error(err_msg))

        threading.Thread(target=do_connect, daemon=True).start()

    # ── Logout flow ───────────────────────────────────────────────────────────

    def _handle_logout(self):
        """Cancel polling, clear saved config, return to setup screen."""
        if self.poll_after_id:
            self.after_cancel(self.poll_after_id)
            self.poll_after_id = None
        self.current_match_id = None
        self.config_data = None
        save_config(None)      # deletes ~/.faceit_companion.json
        self._show_setup()

    # ── Polling loop ──────────────────────────────────────────────────────────

    def _start_polling(self):
        """Kick off the first poll immediately, then every POLL_INTERVAL_MS after that."""
        self._poll_once()

    def _poll_once(self):
        """
        Run one poll cycle on a background thread.
        Schedules the next poll after completion regardless of outcome.
        """
        def do_poll():
            try:
                match_id = get_active_match(
                    self.config_data["api_key"],
                    self.config_data["player_id"],
                )

                if match_id and match_id != self.current_match_id:
                    # New match detected — fetch all player stats
                    self.current_match_id = match_id
                    match   = get_match(self.config_data["api_key"], match_id)
                    players = get_match_player_stats(self.config_data["api_key"], match)
                    # Hand results to the UI on the main thread
                    self.after(0, lambda: self.main_frame.show_match(match, players))

                elif not match_id and self.current_match_id:
                    # Match ended — go back to waiting state
                    self.current_match_id = None
                    self.after(0, self.main_frame.show_waiting)

                # Update the "Last check: HH:MM:SS" timestamp
                self.after(0, self.main_frame.update_last_checked)

            except Exception as e:
                print(f"[Poll error] {e}")

            # Schedule the next poll (always, even on error)
            self.poll_after_id = self.after(POLL_INTERVAL_MS, self._poll_once)

        threading.Thread(target=do_poll, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = FaceitApp()
    app.mainloop()
