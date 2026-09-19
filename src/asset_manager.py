import os
import threading
import requests
from typing import Dict, Tuple, Optional
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen
from PyQt6.QtCore import Qt, QRectF

DATA_DRAGON_VERSION = "14.24.1"
DATA_DRAGON_CDN_URL = f"https://ddragon.leagueoflegends.com/cdn/{DATA_DRAGON_VERSION}/img/champion"


class AssetManager:
    """
    Manages downloading, local disk caching, and rounded rendering of League Champion icons.
    Guarantees non-blocking async downloads and instant in-memory cache lookups.
    """

    _instance = None
    _pixmap_cache: Dict[str, QPixmap] = {}
    _downloading_set = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._init_cache_dir()
        return cls._instance

    def _init_cache_dir(self):
        self.cache_dir = os.path.abspath("assets/champions")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _normalize_champ_name(self, champ_name: str) -> str:
        """Normalizes champion names to DataDragon format (e.g. LeeSin, DrMundo, KaiSa)."""
        name = champ_name.strip()
        # Common DataDragon special cases
        mapping = {
            "Wukong": "MonkeyKing",
            "Nunu & Willump": "Nunu",
            "Renata Glasc": "Renata",
            "Kog'Maw": "KogMaw",
            "Rek'Sai": "RekSai",
            "Cho'Gath": "Chogath",
            "Vel'Koz": "Velkoz",
            "Kha'Zix": "Khazix",
            "Kai'Sa": "Kaisa",
            "Bel'Veth": "Belveth",
            "K'Sante": "KSante",
            "LeBlanc": "Leblanc",
        }
        if name in mapping:
            return mapping[name]
        return name.replace(" ", "").replace("'", "").replace(".", "")

    def get_champion_icon(self, champ_name: str, size: int = 38, radius: int = 6) -> QPixmap:
        """Returns a rounded QPixmap for the requested champion."""
        clean_name = self._normalize_champ_name(champ_name)
        cache_key = f"{clean_name}_{size}_{radius}"

        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.cache_dir, f"{clean_name}.png")

        # 1. If exists on disk, load and round it
        if os.path.exists(local_file):
            raw_pixmap = QPixmap(local_file)
            if not raw_pixmap.isNull():
                rounded = self._create_rounded_pixmap(raw_pixmap, size, radius)
                self._pixmap_cache[cache_key] = rounded
                return rounded

        # 2. If not on disk, trigger async background download
        if clean_name not in self._downloading_set:
            self._downloading_set.add(clean_name)
            threading.Thread(target=self._download_champ_icon, args=(clean_name,), daemon=True).start()

        # 3. Return sleek placeholder in the meantime
        placeholder = self._create_placeholder(clean_name, size, radius)
        return placeholder

    def _download_champ_icon(self, clean_name: str):
        try:
            url = f"{DATA_DRAGON_CDN_URL}/{clean_name}.png"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                local_file = os.path.join(self.cache_dir, f"{clean_name}.png")
                with open(local_file, "wb") as f:
                    f.write(resp.content)
        except Exception as e:
            print(f"[AssetManager] Error downloading icon for {clean_name}: {e}")
        finally:
            self._downloading_set.discard(clean_name)

    def _create_rounded_pixmap(self, raw_pixmap: QPixmap, size: int, radius: int) -> QPixmap:
        scaled = raw_pixmap.scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )

        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, scaled)

        # Subtle inner border
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), radius, radius)

        painter.end()
        return out

    def _create_placeholder(self, clean_name: str, size: int, radius: int) -> QPixmap:
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Background
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QColor(24, 28, 36))
        painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

        # Text Initials
        initials = clean_name[:2].upper() if clean_name else "??"
        painter.setPen(QColor(180, 195, 210))
        font = QFont("Segoe UI", int(size * 0.35), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initials)

        painter.end()
        return out
