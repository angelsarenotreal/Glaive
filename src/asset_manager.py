import os
import sys
import threading
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtWidgets import QWidget

DATA_DRAGON_VERSION = "14.24.1"
CDN_CHAMPION_URL = f"https://ddragon.leagueoflegends.com/cdn/{DATA_DRAGON_VERSION}/img/champion"
CDN_SPELL_URL = f"https://ddragon.leagueoflegends.com/cdn/{DATA_DRAGON_VERSION}/img/spell"
CDN_PROFILE_ICON_URL = f"https://ddragon.leagueoflegends.com/cdn/{DATA_DRAGON_VERSION}/img/profileicon"

SPELL_MAPPING = {
    "flash": "SummonerFlash.png",
    "teleport": "SummonerTeleport.png",
    "tp": "SummonerTeleport.png",
    "smite": "SummonerSmite.png",
    "ignite": "SummonerDot.png",
    "heal": "SummonerHeal.png",
    "exhaust": "SummonerExhaust.png",
    "ghost": "SummonerHaste.png",
    "barrier": "SummonerBarrier.png",
    "cleanse": "SummonerBoost.png",
}


def get_base_asset_dir() -> Path:
    """Returns the correct path to assets directory whether frozen (PyInstaller) or running from source."""
    # 1. If running as PyInstaller onefile bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_assets = Path(sys._MEIPASS) / "assets"
        if meipass_assets.exists():
            return meipass_assets

    # 2. If running from repository root / dev mode
    dev_assets = Path(__file__).resolve().parent.parent / "assets"
    if dev_assets.exists():
        return dev_assets

    # 3. If running next to executable
    exe_assets = Path(sys.executable).parent / "assets"
    if exe_assets.exists():
        return exe_assets

    # 4. Fallback to AppData writable directory
    appdata_assets = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Glaive" / "assets"
    appdata_assets.mkdir(parents=True, exist_ok=True)
    return appdata_assets


class AssetManager:
    """
    Bulletproof Game Asset Manager for League of Legends:
    - Loads bundled assets from disk with 0ms latency.
    - Caches runtime downloads to persistent disk storage.
    - Masks and renders rounded portraits, spell icons, ranked crests, and circular gauges.
    """

    _instance = None
    _pixmap_cache: Dict[str, QPixmap] = {}
    _downloading_set = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance.base_dir = get_base_asset_dir()
            cls._instance.champ_dir = cls._instance.base_dir / "champions"
            cls._instance.spell_dir = cls._instance.base_dir / "spells"
            cls._instance.profile_dir = cls._instance.base_dir / "profiles"
            cls._instance.ranked_dir = cls._instance.base_dir / "ranked"
            cls._instance.roles_dir = cls._instance.base_dir / "roles"
            cls._instance.mastery_dir = cls._instance.base_dir / "mastery"

            for d in [cls._instance.champ_dir, cls._instance.spell_dir, cls._instance.profile_dir, cls._instance.ranked_dir, cls._instance.roles_dir, cls._instance.mastery_dir]:
                d.mkdir(parents=True, exist_ok=True)

        return cls._instance

    def _normalize_champ_name(self, champ_name: str) -> str:
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
        name = champ_name.strip()
        if name in mapping:
            return mapping[name]
        return name.replace(" ", "").replace("'", "").replace(".", "")

    def get_champion_icon(self, champ_name: str, size: int = 46, radius: int = 0) -> QPixmap:
        clean_name = self._normalize_champ_name(champ_name)
        cache_key = f"champ_{clean_name}_{size}_{radius}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.champ_dir / f"{clean_name}.png"
        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius)
                self._pixmap_cache[cache_key] = res
                return res

        # Download in background if not found
        if clean_name not in self._downloading_set:
            self._downloading_set.add(clean_name)
            url = f"{CDN_CHAMPION_URL}/{clean_name}.png"
            threading.Thread(target=self._download_asset, args=(url, local_file, clean_name), daemon=True).start()

        return self._create_placeholder(clean_name[:2], size, radius)

    def get_spell_icon(self, spell_name: str, size: int = 20, radius: int = 0) -> QPixmap:
        clean_name = spell_name.lower().strip()
        spell_file = SPELL_MAPPING.get(clean_name, "SummonerFlash.png")
        cache_key = f"spell_{spell_file}_{size}_{radius}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.spell_dir / spell_file
        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius)
                self._pixmap_cache[cache_key] = res
                return res

        url = f"{CDN_SPELL_URL}/{spell_file}"
        threading.Thread(target=self._download_asset, args=(url, local_file, spell_file), daemon=True).start()
        return self._create_placeholder(spell_name[:1], size, radius)

    def get_profile_icon(self, icon_id: int, size: int = 34, radius: int = 0) -> QPixmap:
        cache_key = f"profile_{icon_id}_{size}_{radius}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.profile_dir / f"{icon_id}.png"
        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius=radius)
                self._pixmap_cache[cache_key] = res
                return res

        url = f"{CDN_PROFILE_ICON_URL}/{icon_id}.png"
        threading.Thread(target=self._download_asset, args=(url, local_file, str(icon_id)), daemon=True).start()
        return self._create_placeholder("P", size, radius)

    def get_ranked_crest(self, tier: str, size: int = 46) -> QPixmap:
        t_clean = tier.lower().strip()
        cache_key = f"rank_{t_clean}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.ranked_dir / f"{t_clean}.png"
        if not local_file.exists():
            local_file = self.ranked_dir / "unranked.png"

        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._pixmap_cache[cache_key] = scaled
                return scaled

        return self._create_placeholder(t_clean[:2], size, 0)

    def get_mastery_crest(self, level: int, size: int = 34) -> QPixmap:
        """
        Returns official high-res League of Legends Champion Mastery Crest:
        - level 0: mastery_0.png
        - level 1-9: mastery_{level}.png
        - level >= 10: mastery_10.png (supreme crest used for levels 10+)
        """
        tier = min(10, max(0, level))
        cache_key = f"mastery_{tier}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.mastery_dir / f"mastery_{tier}.png"
        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._pixmap_cache[cache_key] = scaled
                return scaled

        # Background download if not found locally
        tag = f"mastery_{tier}"
        if tag not in self._downloading_set:
            self._downloading_set.add(tag)
            url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/mastery-{tier}.png" if tier > 0 else "https://raw.communitydragon.org/latest/game/assets/ux/mastery/legendarychampionmastery/masterycrest_level0.png"
            threading.Thread(target=self._download_asset, args=(url, local_file, tag), daemon=True).start()

        return self._create_placeholder(f"M{tier}", size, 0)

    ROLE_FILE_MAP = {
        "top": "top.png",
        "jungle": "jungle.png",
        "jungler": "jungle.png",
        "jgl": "jungle.png",
        "mid": "mid.png",
        "middle": "mid.png",
        "bot": "bot.png",
        "bottom": "bot.png",
        "ad_carry": "bot.png",
        "ad carry": "bot.png",
        "adc": "bot.png",
        "carry": "bot.png",
        "support": "support.png",
        "utility": "support.png",
        "sup": "support.png",
    }

    def get_role_icon(self, role: str, size: int = 24) -> QPixmap:
        r_clean = role.lower().strip()
        filename = self.ROLE_FILE_MAP.get(r_clean, f"{r_clean.replace(' ', '_')}.png")
        cache_key = f"role_{filename}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = self.roles_dir / filename
        if local_file.exists():
            raw = QPixmap(str(local_file))
            if not raw.isNull():
                scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._pixmap_cache[cache_key] = scaled
                return scaled

        return self._create_placeholder(role[:1] if role else "R", size, size // 2)

    def _download_asset(self, url: str, local_path: Path, tag: str):
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
        except Exception as e:
            pass
        finally:
            self._downloading_set.discard(tag)

    def _create_rounded_pixmap(self, raw: QPixmap, size: int, radius: int) -> QPixmap:
        scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)

        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), radius, radius)
        painter.end()
        return out

    def _create_placeholder(self, text: str, size: int, radius: int) -> QPixmap:
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        painter.setBrush(QColor(20, 26, 36))
        painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)
        painter.setPen(QColor(180, 195, 210))
        painter.setFont(QFont("Segoe UI", max(8, int(size * 0.35)), QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, text.upper())
        painter.end()
        return out


class CircularGaugeWidget(QWidget):
    """
    Antialiased circular progress ring matching Porofessor's 12-Hour and 30-Day gauges.
    Supports percentage rings and central icon mode for roles!
    """

    def __init__(
        self,
        percentage: float,
        header_text: str,
        sub_text1: str,
        sub_text2: str = "",
        ring_color: QColor = QColor(16, 185, 129),  # Green
        center_pixmap: Optional[QPixmap] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.percentage = max(0.0, min(100.0, percentage))
        self.header_text = header_text
        self.sub_text1 = sub_text1
        self.sub_text2 = sub_text2
        self.ring_color = ring_color
        self.center_pixmap = center_pixmap
        self.setFixedHeight(98)
        self.setMinimumWidth(80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # 1. Outer Ring Area
        dial_size = 50
        dial_x = (self.width() - dial_size) / 2
        dial_y = 2
        rect = QRectF(dial_x, dial_y, dial_size, dial_size)

        # Background track
        painter.setPen(QPen(QColor(255, 255, 255, 25), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(QColor(13, 17, 23, 255))
        painter.drawEllipse(rect)

        # Foreground Progress Arc
        span_angle = int(-(self.percentage / 100.0) * 360 * 16)
        painter.setPen(QPen(self.ring_color, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, span_angle)

        # Center Content: Role Icon OR Percentage Text
        if self.center_pixmap and not self.center_pixmap.isNull():
            icon_size = 24
            ix = dial_x + (dial_size - icon_size) / 2
            iy = dial_y + (dial_size - icon_size) / 2
            painter.drawPixmap(int(ix), int(iy), self.center_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            pct_str = f"{self.percentage:.1f}%" if (self.percentage % 1 != 0 and self.percentage > 0) else f"{int(self.percentage)}%"
            painter.setPen(QColor(248, 250, 252))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(dial_x, dial_y + 8, dial_size, 16), Qt.AlignmentFlag.AlignCenter, pct_str)

            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.drawText(QRectF(dial_x, dial_y + 24, dial_size, 16), Qt.AlignmentFlag.AlignCenter, self.header_text)

        # Subtext 1 (e.g. "2 Games" or "Main Role:")
        painter.setPen(QColor(226, 232, 240))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.drawText(QRectF(0, dial_size + 9, self.width(), 16), Qt.AlignmentFlag.AlignCenter, self.sub_text1)

        # Subtext 2 (e.g. "(2 Wins)" or "Top")
        if self.sub_text2:
            if "Win" in self.sub_text2:
                painter.setPen(QColor(56, 189, 248))  # Blue wins
            else:
                painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            painter.drawText(QRectF(0, dial_size + 25, self.width(), 16), Qt.AlignmentFlag.AlignCenter, self.sub_text2)

        painter.end()
