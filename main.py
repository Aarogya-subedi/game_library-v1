import webview
import json
import base64
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
import win32ui
import win32gui
import win32con
import win32api


# ============================================================
# PATHS
# ============================================================

def get_app_directory():
    """
    Returns the directory where the application is running.

    When running normally:
        project_folder/

    When running as a PyInstaller EXE:
        folder containing the EXE
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


APP_DIR = get_app_directory()

DATA_FILE = APP_DIR / "games.json"
INDEX_FILE = APP_DIR / "index.html"


# ============================================================
# EXE ICON EXTRACTION
# ============================================================

def extract_exe_icon(exe_path):
    """
    Extracts the primary icon from a Windows .exe
    and returns it as a Base64 PNG string.
    """

    try:
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

        large, small = win32gui.ExtractIconEx(
            str(exe_path),
            0
        )

        if not large and not small:
            return None

        hicon = large[0] if large else small[0]

        # Get screen device context
        screen_dc = win32gui.GetDC(0)
        hdc = win32ui.CreateDCFromHandle(screen_dc)

        # Create bitmap
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(
            hdc,
            ico_x,
            ico_y
        )

        # Create compatible drawing context
        memory_dc = hdc.CreateCompatibleDC()
        memory_dc.SelectObject(hbmp)

        # Draw icon
        memory_dc.DrawIcon(
            (0, 0),
            hicon
        )

        # Get bitmap data
        bmpstr = hbmp.GetBitmapBits(True)

        img = Image.frombuffer(
            "RGBA",
            (ico_x, ico_y),
            bmpstr,
            "raw",
            "BGRA",
            0,
            1
        )

        # Release Windows icons
        for icon in large:
            win32gui.DestroyIcon(icon)

        for icon in small:
            win32gui.DestroyIcon(icon)

        # Convert image to PNG in memory
        buffered = BytesIO()
        img.save(
            buffered,
            format="PNG"
        )

        # Convert PNG to Base64
        img_str = base64.b64encode(
            buffered.getvalue()
        ).decode("utf-8")

        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Icon extraction failed: {e}")
        return None


# ============================================================
# GAME LIBRARY API
# ============================================================

class GameLibraryAPI:

    # --------------------------------------------------------
    # LOAD GAMES
    # --------------------------------------------------------

    def load_games(self):
        """
        Loads saved games from games.json.
        """

        if DATA_FILE.exists():

            try:
                return json.loads(
                    DATA_FILE.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception as e:
                print(f"Could not read games.json: {e}")
                return []

        return []

    # --------------------------------------------------------
    # SAVE GAMES
    # --------------------------------------------------------

    def save_games(self, games_list):
        """
        Saves the game list to games.json.
        """

        try:

            DATA_FILE.write_text(
                json.dumps(
                    games_list,
                    indent=4
                ),
                encoding="utf-8"
            )

        except Exception as e:
            print(f"Could not save games.json: {e}")

    # --------------------------------------------------------
    # ADD GAME
    # --------------------------------------------------------

    def add_game(self):
        """
        Opens a Windows file picker and lets the user
        select a game executable.
        """

        file_types = (
            "Executable Files (*.exe)",
            "All Files (*.*)"
        )

        result = webview.active_window().create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )

        # User cancelled
        if not result:
            return None

        file_path = Path(result[0])

        # Extract game icon
        icon_data = extract_exe_icon(file_path)

        # Create game information
        new_game = {
            "name": file_path.stem,
            "path": str(file_path),
            "icon": icon_data
        }

        # Load existing games
        games = self.load_games()

        # Prevent duplicate games
        if not any(
            g.get("path") == new_game["path"]
            for g in games
        ):
            games.append(new_game)
            self.save_games(games)

        return games

    # --------------------------------------------------------
    # REMOVE GAME FROM LIBRARY
    # --------------------------------------------------------

    def remove_game(self, path):
        """
        Removes a game from the library.

        IMPORTANT:
        This does NOT delete the actual game from the PC.
        It only removes the game from games.json.
        """

        games = self.load_games()

        games = [
            g for g in games
            if g.get("path") != path
        ]

        self.save_games(games)

        return games

    # --------------------------------------------------------
    # LAUNCH GAME
    # --------------------------------------------------------

    def launch_game(self, path):
        """
        Launches the selected game executable.
        """

        try:

            game_path = Path(path)

            if not game_path.exists():
                print(f"Game not found: {game_path}")
                return False

            # Game's own directory
            game_dir = str(
                game_path.parent
            )

            # Launch game
            subprocess.Popen(
                str(game_path),
                cwd=game_dir
            )

            return True

        except Exception as e:

            print(f"Launch error: {e}")

            return False


# ============================================================
# CREATE API
# ============================================================

api = GameLibraryAPI()


# ============================================================
# CREATE WINDOW
# ============================================================

webview.create_window(
    "Game Library",
    str(INDEX_FILE),
    js_api=api,
    width=1100,
    height=750,
    background_color="#07070b"
)


# ============================================================
# START APPLICATION
# ============================================================

webview.start()
