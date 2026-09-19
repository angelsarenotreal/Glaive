import os
import subprocess
import sys
from generate_assets import generate_glaive_icon

def build():
    print("[Build] Ensuring assets are generated...")
    generate_glaive_icon()

    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/f", "/im", "Glaive.exe"], capture_output=True)
        except Exception:
            pass

    print("[Build] Running PyInstaller to package Glaive.exe...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--windowed",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets",
        "--name=Glaive",
        "--clean",
        "src/main.py"
    ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe_path = os.path.abspath("dist/Glaive.exe")
        print(f"\n[Build Success] Standalone executable created at:\n{exe_path}")
    else:
        print(f"\n[Build Failed] PyInstaller exited with code {result.returncode}")

if __name__ == "__main__":
    build()
