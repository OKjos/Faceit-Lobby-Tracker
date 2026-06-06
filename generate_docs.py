"""
generate_docs.py
----------------
Run this script to regenerate docs/documentation.pdf.

Usage:
  python generate_docs.py
"""

import os
from fpdf import FPDF

OUTPUT_DIR  = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "documentation.pdf")

ORANGE = (255, 85,   0)
MUTED  = (107, 114, 128)
WHITE  = (226, 232, 240)
GREEN  = (52,  211, 153)
BLUE   = (96,  165, 250)


class DocPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*ORANGE)
        self.cell(0, 8, "Faceit Companion - Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ORANGE)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def chapter_title(self, text):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*ORANGE)
        self.ln(4)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ORANGE)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, text):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BLUE)
        self.ln(3)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(2)

    def bullet(self, label, description):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ORANGE)
        self.multi_cell(0, 6, f"  {label}:", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, f"    {description}")
        self.ln(1)


def build_pdf():
    pdf = DocPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(14, 18, 14)

    # -- Cover page ------------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*ORANGE)
    pdf.ln(40)
    pdf.cell(0, 20, "FACEIT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 12, "Companion - Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_draw_color(*ORANGE)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(14)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0, 7,
        "A Python desktop app that monitors your Faceit CS2 match room\n"
        "and shows K/D, Win%, HS%, ELO and map stats for all 10 players.",
        align="C",
    )

    # -- Table of Contents -----------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc = [
        ("1",  "Overview & How It Works"),
        ("2",  "Tech Stack & Libraries"),
        ("3",  "File Structure"),
        ("4",  "app.py - Main Controller"),
        ("5",  "config.py - Settings Storage"),
        ("6",  "api/faceit.py - Faceit API Layer"),
        ("7",  "ui/setup_frame.py - Login Screen"),
        ("8",  "ui/main_frame.py - Main Screen"),
        ("9",  "ui/match_frame.py - Match Room"),
        ("10", "ui/player_card.py - Player Card"),
        ("11", "Editing the Map Pool"),
        ("12", "Threading Model"),
        ("13", "Faceit API Reference"),
        ("14", "How to Run"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(16, 8, num + ".")
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    # -- Section 1: Overview ---------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("1. Overview & How It Works")
    pdf.body(
        "Faceit Companion is a Windows desktop app that sits open while you play CS2. "
        "It watches your Faceit account and automatically detects when you enter a match room. "
        "The moment a match is found, it fetches stats for all 10 players and displays them "
        "side by side before the game even starts."
    )
    pdf.section_title("Step-by-step flow:")
    steps = [
        ("Step 1", "App starts. Loads saved nickname and API key from disk."),
        ("Step 2", "If no saved data, shows the Setup screen to collect them."),
        ("Step 3", "User enters their Faceit nickname and API key, clicks Connect."),
        ("Step 4", "App calls Faceit API to verify the nickname and fetch the player ID."),
        ("Step 5", "Credentials saved to disk. Main screen shown. Polling begins."),
        ("Step 6", "Every 15 seconds: checks if the player's most recent match is still active."),
        ("Step 7", "Active match detected: fetches match details and all 10 players' stats in parallel."),
        ("Step 8", "Match room shown with two team columns and one card per player."),
        ("Step 9", "When the match ends, polling detects it and returns to the waiting screen."),
    ]
    for label, desc in steps:
        pdf.bullet(label, desc)

    # -- Section 2: Tech Stack -------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("2. Tech Stack & Libraries")
    pdf.body("Everything is Python. No JavaScript, no Electron, no browser.")
    libs = [
        ("customtkinter",      "Modern dark-themed GUI widgets built on top of Python's Tkinter."),
        ("requests",           "HTTP library for calling the Faceit REST API."),
        ("Pillow (PIL)",       "Downloads and displays player avatar images."),
        ("fpdf2",              "Generates this documentation PDF."),
        ("threading",          "Runs API calls in the background without freezing the window."),
        ("concurrent.futures", "Fetches all 10 players' stats simultaneously (ThreadPoolExecutor)."),
    ]
    for name, desc in libs:
        pdf.bullet(name, desc)

    # -- Section 3: File Structure ---------------------------------------------
    pdf.add_page()
    pdf.chapter_title("3. File Structure")
    pdf.code_block(
        "FaceitSite/\n"
        "+-- app.py              Entry point. Run this to launch the app.\n"
        "+-- config.py           Saves/loads nickname + API key to a local JSON file.\n"
        "+-- requirements.txt    pip dependencies.\n"
        "+-- generate_docs.py    Run this to regenerate docs/documentation.pdf.\n"
        "+-- api/\n"
        "|   +-- faceit.py       All Faceit API calls.\n"
        "+-- ui/\n"
        "    +-- setup_frame.py  Login screen.\n"
        "    +-- main_frame.py   Main screen (status bar + content area).\n"
        "    +-- match_frame.py  Two-column match room layout.\n"
        "    +-- player_card.py  One stat card per player.\n"
        "+-- dist/\n"
        "    +-- Faceit Companion.exe  Standalone executable (built by PyInstaller).\n"
    )

    # -- Section 4: app.py -----------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("4. app.py - Main Controller")
    pdf.body(
        "Entry point. FaceitApp inherits from customtkinter.CTk (the main window). "
        "Run 'python app.py' to launch."
    )
    sections_apppy = [
        ("__init__",          "Sets window to 1100x750, loads saved config, shows Setup or Main screen."),
        ("_show_setup()",     "Clears all widgets and shows the login card."),
        ("_show_main()",      "Clears all widgets, shows the main screen, starts polling."),
        ("_handle_connect()", "Called on Connect click. Runs the API lookup on a background thread. "
                              "On success saves config and switches to main screen. On failure shows error."),
        ("_handle_logout()",  "Cancels the polling timer, deletes saved config, returns to setup."),
        ("_poll_once()",      "Runs on a background thread every 15 seconds. Checks for an active match. "
                              "Fetches all player stats if a new match is found. Returns to waiting if match ended."),
    ]
    for name, desc in sections_apppy:
        pdf.bullet(name, desc)

    # -- Section 5: config.py --------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("5. config.py - Settings Storage")
    pdf.body(
        "Saves the user's nickname, player ID, and API key to a hidden JSON file "
        "in their home folder so they don't have to re-enter it every launch."
    )
    pdf.body("File location:  C:\\Users\\YourName\\.faceit_companion.json")
    pdf.body("Example contents:")
    pdf.code_block(
        '{\n'
        '  "nickname":  "YourFaceitName",\n'
        '  "player_id": "abc123def456...",\n'
        '  "api_key":   "your-api-key-here",\n'
        '  "avatar":    "https://assets.faceit-cdn.net/..."\n'
        '}'
    )
    pdf.bullet("load_config()",    "Returns the dict from disk, or None if no file exists yet.")
    pdf.bullet("save_config(cfg)", "Writes cfg to disk. Pass None to delete the file (used on logout).")

    # -- Section 6: api/faceit.py ----------------------------------------------
    pdf.add_page()
    pdf.chapter_title("6. api/faceit.py - Faceit API Layer")
    pdf.body(
        "All HTTP calls to Faceit go through this file. Every function takes api_key as its "
        "first argument, used in a Bearer token Authorization header. "
        "resp.raise_for_status() is called after each request so HTTP errors bubble up as exceptions."
    )
    api_fns = [
        ("get_player(api_key, nickname)",
         "GET /players?nickname=X&game=cs2\n"
         "Finds a player by nickname. Returns player_id, avatar, ELO, etc."),
        ("get_player_details(api_key, player_id)",
         "GET /players/{id}\n"
         "Full profile: ELO, skill level, country."),
        ("get_player_stats(api_key, player_id)",
         "GET /players/{id}/stats/cs2\n"
         "Returns lifetime stats and a segments list.\n"
         "Lifetime: Average K/D Ratio, Win Rate %, Average Headshots %, Matches.\n"
         "Segments: one entry per map with type='Map', label='Mirage' etc."),
        ("get_active_match(api_key, player_id)",
         "GET /players/{id}/history?game=cs2&limit=1\n"
         "Gets the most recent match. Returns match_id if status is not FINISHED or CANCELLED, else None."),
        ("get_match(api_key, match_id)",
         "GET /matches/{match_id}\n"
         "Full match: both team rosters, map vote result, status."),
        ("get_match_player_stats(api_key, match)",
         "Calls get_player_details + get_player_stats for all 10 players at once "
         "using ThreadPoolExecutor(max_workers=10). Returns a list of enriched player dicts."),
    ]
    for name, desc in api_fns:
        pdf.section_title(name)
        pdf.body(desc)

    # -- Section 7: ui/setup_frame.py ------------------------------------------
    pdf.add_page()
    pdf.chapter_title("7. ui/setup_frame.py - Login Screen")
    pdf.body(
        "A centered login card using place(relx=0.5, rely=0.5) so it stays centered on resize. "
        "Width is set in the CTkFrame constructor, not in place()."
    )
    setup_parts = [
        ("Logo",           "FACEIT in orange (size 30 bold), COMPANION in muted text below."),
        ("Nickname field", "Plain text entry. Just checks it is not empty before connecting."),
        ("API key field",  "Entry with show='*' so the key is hidden behind dots."),
        ("Error label",    "Starts empty. show_error(msg) is called from app.py to display errors in red."),
        ("Connect button", "Disables itself with 'Connecting...' while the API call runs, re-enables on failure."),
    ]
    for name, desc in setup_parts:
        pdf.bullet(name, desc)

    # -- Section 8: ui/main_frame.py -------------------------------------------
    pdf.add_page()
    pdf.chapter_title("8. ui/main_frame.py - Main Screen")
    pdf.body(
        "The screen shown after login. A status bar sits at the top; a content area below "
        "swaps between the waiting view and the match view."
    )
    main_parts = [
        ("Status bar",          "Shows your nickname (gold), a coloured dot (green=watching, blue=in match), "
                                "last poll timestamp, and a Logout button."),
        ("_show_waiting_view()", "Idle state: big CS2 label with a message to queue up."),
        ("show_match()",        "Called by app.py when a match is detected. Inserts a MatchFrame. Dot turns blue."),
        ("show_waiting()",      "Called by app.py when match ends. Returns to waiting view. Dot turns green."),
        ("update_last_checked()","Updates the HH:MM:SS timestamp shown after each poll."),
    ]
    for name, desc in main_parts:
        pdf.bullet(name, desc)

    # -- Section 9: ui/match_frame.py ------------------------------------------
    pdf.add_page()
    pdf.chapter_title("9. ui/match_frame.py - Match Room")
    pdf.body(
        "Displays the two teams side by side. Separates players into the correct team "
        "by comparing their player_id against each faction's roster."
    )
    match_parts = [
        ("Match header",   "Shows the map name (from match voting result) in orange and a short match ID."),
        ("Team columns",   "Two CTkFrames side by side. Each has a team name header and a "
                           "CTkScrollableFrame containing PlayerCard widgets."),
        ("VS divider",     "44px strip in the center with 'VS'. Visual only."),
        ("_team_column()", "Builds one team's column: name header + scrollable player list."),
    ]
    for name, desc in match_parts:
        pdf.bullet(name, desc)

    # -- Section 10: ui/player_card.py -----------------------------------------
    pdf.add_page()
    pdf.chapter_title("10. ui/player_card.py - Player Card")
    pdf.body(
        "One card per player. Horizontal layout: coloured ELO accent bar on the left edge, "
        "then avatar, name + level badge, stats row, and map chips below."
    )
    card_parts = [
        ("ELO accent bar",  "4px coloured strip on the left edge: grey/green/blue/purple/orange by ELO tier."),
        ("Avatar",          "36px circle placeholder shown instantly. Real image loaded in a background thread."),
        ("Nickname",        "Gold text for the logged-in user, white for everyone else."),
        ("Level badge",     "Coloured pill: 1-3 green, 4 lime, 5-6 yellow, 7-9 orange, 10 red."),
        ("K/D ratio",       "Green if >= 1.2, white otherwise."),
        ("Win rate %",      "Lifetime win rate, rounded to nearest integer."),
        ("HS %",            "Average headshot percentage per match."),
        ("Games",           "Total matches on record."),
        ("ELO",             "Coloured by tier. Sits to the right of the stat columns."),
        ("Map chips",       "One chip per map in MAP_NAMES pool. Shows: map name, win rate (or N/A), "
                            "and games played on that map. Chips are sorted by most played first. "
                            "Displayed in a 2-per-row grid below the stats."),
    ]
    for name, desc in card_parts:
        pdf.bullet(name, desc)

    # -- Section 11: Editing the Map Pool --------------------------------------
    pdf.add_page()
    pdf.chapter_title("11. Editing the Map Pool")
    pdf.body(
        "The map pool is defined at the top of ui/player_card.py in a dict called MAP_NAMES. "
        "Only maps listed here are shown on player cards. To add or remove a map, "
        "edit this dict and rebuild the exe."
    )
    pdf.body("Current pool:")
    pdf.code_block(
        'MAP_NAMES = {\n'
        '    "Dust2":    "Dust 2",\n'
        '    "Mirage":   "Mirage",\n'
        '    "Nuke":     "Nuke",\n'
        '    "Ancient":  "Ancient",\n'
        '    "Inferno":  "Inferno",\n'
        '    "Overpass": "Overpass",\n'
        '    "Anubis":   "Anubis",\n'
        '    "Cache":    "Cache",\n'
        '}'
    )
    pdf.body(
        "The key must match the label the Faceit API returns (e.g. 'Mirage', 'Dust2'). "
        "The value is what appears on the card. To find the correct key for a new map, "
        "check what label appears in the /players/{id}/stats/cs2 segments response."
    )
    pdf.body("After editing, rebuild the exe:")
    pdf.code_block("pyinstaller --onefile --windowed --name \"Faceit Companion\" app.py")

    # -- Section 12: Threading -------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("12. Threading Model")
    pdf.body(
        "CustomTkinter is single-threaded. Network requests on the main thread freeze the window. "
        "This app avoids that by running all API calls on background threads and using self.after() "
        "to push UI updates back to the main thread."
    )
    pdf.bullet("API calls",   "Run on daemon threads: threading.Thread(target=fn, daemon=True).start()")
    pdf.bullet("UI updates",  "Always via self.after(0, fn) - schedules fn() on the main thread.")
    pdf.bullet("daemon=True", "Threads die automatically when the window closes.")
    pdf.body("Pattern used throughout:")
    pdf.code_block(
        "def _some_action(self):\n"
        "    def do_work():\n"
        "        result = some_api_call()   # background thread\n"
        "        self.after(0, lambda: self.label.configure(text=result))  # main thread\n"
        "    threading.Thread(target=do_work, daemon=True).start()"
    )

    # -- Section 13: API Reference ---------------------------------------------
    pdf.add_page()
    pdf.chapter_title("13. Faceit API Reference")
    pdf.body("Base URL:  https://open.faceit.com/data/v4")
    pdf.body("Auth:      Authorization: Bearer <your_api_key>")
    pdf.body("API key:   developers.faceit.com -> create a Server-side app -> copy the key.")
    endpoints = [
        ("GET /players",                  "?nickname=X&game=cs2  -  Find player by nickname"),
        ("GET /players/{id}",             "Full profile: ELO, skill level, country"),
        ("GET /players/{id}/stats/cs2",   "Lifetime stats + per-map segments"),
        ("GET /players/{id}/history",     "?game=cs2&limit=1  -  Most recent match (used for polling)"),
        ("GET /matches/{match_id}",       "Full match: teams, rosters, map vote, status"),
    ]
    for endpoint, desc in endpoints:
        pdf.bullet(endpoint, desc)

    # -- Section 14: How to Run ------------------------------------------------
    pdf.add_page()
    pdf.chapter_title("14. How to Run")
    pdf.section_title("Option A: Run from source")
    pdf.code_block(
        "# 1. Open a terminal in the FaceitSite folder\n"
        "# 2. Install dependencies\n"
        "pip install -r requirements.txt\n\n"
        "# 3. Launch\n"
        "python app.py"
    )
    pdf.section_title("Option B: Double-click the exe")
    pdf.body("Open dist\\Faceit Companion.exe  -  no Python or terminal needed.")
    pdf.section_title("Rebuild the exe after code changes:")
    pdf.code_block(
        "pyinstaller --onefile --windowed --name \"Faceit Companion\" app.py\n"
        "# Output: dist\\Faceit Companion.exe"
    )
    pdf.section_title("Regenerate this PDF:")
    pdf.code_block("python generate_docs.py")
    pdf.section_title("First-time setup:")
    pdf.body(
        "1. The Setup screen appears.\n"
        "2. Enter your Faceit nickname exactly as it shows on your profile.\n"
        "3. Paste your API key.\n"
        "4. Click Connect.\n"
        "5. Your info is saved. The main screen appears.\n"
        "6. Queue up on Faceit. Within 15 seconds of entering a match room\n"
        "   the app detects it and shows all 10 players stats."
    )

    # -- Save ------------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf.output(OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_pdf()
