import webview
import json
import base64
import subprocess
from io import BytesIO
from pathlib import Path
from PIL import Image
import win32ui
import win32gui
import win32con
import win32api

DATA_FILE = Path("games.json")


def extract_exe_icon(exe_path):
    """Extracts the primary icon from a Windows .exe and returns a Base64 PNG string."""
    try:
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

        large, small = win32gui.ExtractIconEx(str(exe_path), 0)
        if not large and not small:
            return None

        hicon = large[0] if large else small[0]

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hicon)

        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGBA',
            (ico_x, ico_y),
            bmpstr,
            'raw',
            'BGRA',
            0,
            1
        )

        for icon in large:
            win32gui.DestroyIcon(icon)
        for icon in small:
            win32gui.DestroyIcon(icon)

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"Icon extraction failed: {e}")
        return None


class GameLibraryAPI:

    def load_games(self):
        if DATA_FILE.exists():
            try:
                return json.loads(DATA_FILE.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_games(self, games_list):
        DATA_FILE.write_text(json.dumps(games_list, indent=4), encoding="utf-8")

    def add_game(self):
        file_types = ('Executable Files (*.exe)', 'All Files (*.*)')
        result = webview.active_window().create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )

        if not result:
            return None

        file_path = Path(result[0])
        icon_data = extract_exe_icon(file_path)

        new_game = {
            "name": file_path.stem,
            "path": str(file_path),
            "icon": icon_data
        }

        games = self.load_games()
        if not any(g["path"] == new_game["path"] for g in games):
            games.append(new_game)
            self.save_games(games)

        return games

    def remove_game(self, path):
        games = self.load_games()
        games = [g for g in games if g["path"] != path]
        self.save_games(games)
        return games

    def launch_game(self, path):
        try:
            game_dir = str(Path(path).parent)
            subprocess.Popen(path, cwd=game_dir)
            return True
        except Exception as e:
            print(f"Launch error: {e}")
            return False


api = GameLibraryAPI()

webview.create_window(
    "Game Library",
    "index.html",
    js_api=api,
    width=1100,
    height=750,
    background_color='#07070b'
)
webview.start()