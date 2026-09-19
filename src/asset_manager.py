import os
import threading
import requests
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

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


class AssetManager:
    """
    Manages downloading, local disk caching, and rendering of all visual game assets:
    - Champion Square Icons
    - Summoner Spells
    - Profile Icons
    - Ranked Tier Emblems / Crests
    - Lane / Role Emblems
    """

    _instance = None
    _pixmap_cache: Dict[str, QPixmap] = {}
    _downloading_set = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._init_cache_dirs()
        return cls._instance

    def _init_cache_dirs(self):
        self.champ_dir = os.path.abspath("assets/champions")
        self.spell_dir = os.path.abspath("assets/spells")
        self.profile_dir = os.path.abspath("assets/profiles")
        self.ranked_dir = os.path.abspath("assets/ranked")
        self.roles_dir = os.path.abspath("assets/roles")

        for d in [self.champ_dir, self.spell_dir, self.profile_dir, self.ranked_dir, self.roles_dir]:
            os.makedirs(d, exist_ok=True)

        self._ensure_vector_assets()

    def _ensure_vector_assets(self):
        """Generates crisp vector ranked emblems and role icons if not already present."""
        # 1. Generate Ranked Crests (Challenger, Grandmaster, Master, Diamond, Emerald, Plat, Gold, Silver, Bronze, Iron)
        tiers = {
            "challenger": ((218, 165, 32), (56, 189, 248), "CH"),
            "grandmaster": ((239, 68, 68), (185, 28, 28), "GM"),
            "master": ((168, 85, 247), (126, 34, 206), "M"),
            "diamond": ((56, 189, 248), (30, 64, 175), "D"),
            "emerald": ((16, 185, 129), (6, 95, 70), "E"),
            "platinum": ((45, 212, 191), (19, 78, 74), "P"),
            "gold": ((245, 158, 11), (180, 83, 9), "G"),
            "silver": ((148, 163, 184), (71, 85, 105), "S"),
            "bronze": ((180, 83, 9), (120, 53, 15), "B"),
            "iron": ((100, 116, 139), (51, 65, 85), "I"),
            "unranked": ((71, 85, 105), (30, 41, 59), "U"),
        }

        for tier, (c1, c2, letter) in tiers.items():
            path = os.path.join(self.ranked_dir, f"{tier}.png")
            if not os.path.exists(path):
                img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Draw winged shield
                points = [(64, 10), (110, 35), (105, 85), (64, 118), (23, 85), (18, 35)]
                draw.polygon(points, fill=c1, outline=(255, 255, 255, 180), width=3)
                # Inner crest
                inner_points = [(64, 25), (95, 45), (90, 80), (64, 102), (38, 80), (33, 45)]
                draw.polygon(inner_points, fill=c2)
                # Wings
                draw.line([(18, 35), (2, 20), (10, 60), (23, 85)], fill=c1, width=4)
                draw.line([(110, 35), (126, 20), (118, 60), (105, 85)], fill=c1, width=4)
                img.save(path, format="PNG")

        # 2. Generate Role Icons (Top, Jungle, Mid, AD Carry, Support)
        roles = ["top", "jungle", "mid", "ad carry", "support"]
        for role in roles:
            path = os.path.join(self.roles_dir, f"{role.replace(' ', '_')}.png")
            if not os.path.exists(path):
                img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.ellipse([(8, 8), (56, 56)], fill=(15, 23, 42, 220), outline=(56, 189, 248, 180), width=2)
                if role == "top":
                    draw.polygon([(32, 16), (46, 30), (38, 48), (26, 48), (18, 30)], fill=(56, 189, 248, 255))
                elif role == "jungle":
                    draw.polygon([(32, 14), (40, 28), (48, 22), (40, 48), (24, 48), (16, 22), (24, 28)], fill=(56, 189, 248, 255))
                elif role == "mid":
                    draw.rectangle([(22, 22), (42, 42)], fill=(56, 189, 248, 255))
                elif role == "ad carry":
                    draw.polygon([(32, 16), (48, 44), (32, 38), (16, 44)], fill=(56, 189, 248, 255))
                elif role == "support":
                    draw.ellipse([(20, 20), (44, 44)], fill=(56, 189, 248, 255))
                img.save(path, format="PNG")

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

    def get_champion_icon(self, champ_name: str, size: int = 42, radius: int = 6) -> QPixmap:
        clean_name = self._normalize_champ_name(champ_name)
        cache_key = f"champ_{clean_name}_{size}_{radius}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.champ_dir, f"{clean_name}.png")
        if os.path.exists(local_file):
            raw = QPixmap(local_file)
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius)
                self._pixmap_cache[cache_key] = res
                return res

        # Download in background
        if clean_name not in self._downloading_set:
            self._downloading_set.add(clean_name)
            threading.Thread(target=self._download_asset, args=(f"{CDN_CHAMPION_URL}/{clean_name}.png", local_file, clean_name), daemon=True).start()

        return self._create_placeholder(clean_name[:2], size, radius)

    def get_spell_icon(self, spell_name: str, size: int = 18, radius: int = 3) -> QPixmap:
        clean_name = spell_name.lower().strip()
        spell_file = SPELL_MAPPING.get(clean_name, "SummonerFlash.png")
        cache_key = f"spell_{spell_file}_{size}_{radius}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.spell_dir, spell_file)
        if os.path.exists(local_file):
            raw = QPixmap(local_file)
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius)
                self._pixmap_cache[cache_key] = res
                return res

        # Download spell
        threading.Thread(target=self._download_asset, args=(f"{CDN_SPELL_URL}/{spell_file}", local_file, spell_file), daemon=True).start()
        return self._create_placeholder(spell_name[:1], size, radius)

    def get_profile_icon(self, icon_id: int, size: int = 32) -> QPixmap:
        cache_key = f"profile_{icon_id}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.profile_dir, f"{icon_id}.png")
        if os.path.exists(local_file):
            raw = QPixmap(local_file)
            if not raw.isNull():
                res = self._create_rounded_pixmap(raw, size, radius=size // 2)
                self._pixmap_cache[cache_key] = res
                return res

        # Download profile icon
        threading.Thread(target=self._download_asset, args=(f"{CDN_PROFILE_ICON_URL}/{icon_id}.png", local_file, str(icon_id)), daemon=True).start()
        return self._create_placeholder("P", size, size // 2)

    def get_ranked_crest(self, tier: str, size: int = 40) -> QPixmap:
        t_clean = tier.lower().strip()
        if t_clean in ["master", "grandmaster", "challenger", "diamond", "emerald", "platinum", "gold", "silver", "bronze", "iron"]:
            tier_key = t_clean
        else:
            tier_key = "unranked"

        cache_key = f"rank_{tier_key}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.ranked_dir, f"{tier_key}.png")
        if os.path.exists(local_file):
            raw = QPixmap(local_file)
            scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._pixmap_cache[cache_key] = scaled
            return scaled

        return self._create_placeholder(tier_key[:2], size, 4)

    def get_role_icon(self, role: str, size: int = 24) -> QPixmap:
        r_clean = role.lower().strip().replace(" ", "_")
        cache_key = f"role_{r_clean}_{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_file = os.path.join(self.roles_dir, f"{r_clean}.png")
        if os.path.exists(local_file):
            raw = QPixmap(local_file)
            scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._pixmap_cache[cache_key] = scaled
            return scaled

        return self._create_placeholder(role[:1], size, size // 2)

    def _download_asset(self, url: str, local_path: str, tag: str):
        try:
            resp = requests.get(url, timeout=5)
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

        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), radius, radius)
        painter.end()
        return out

    def _create_placeholder(self, text: str, size: int, radius: int) -> QPixmap:
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
        painter.setBrush(QColor(20, 24, 32))
        painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)
        painter.setPen(QColor(160, 175, 190))
        painter.setFont(QFont("Segoe UI", max(7, int(size * 0.35)), QFont.Weight.Bold))
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
        self.setFixedSize(76, 88)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # 1. Outer Ring Area
        dial_size = 44
        dial_x = (self.width() - dial_size) / 2
        dial_y = 2
        rect = QRectF(dial_x, dial_y, dial_size, dial_size)

        # Background track
        painter.setPen(QPen(QColor(255, 255, 255, 20), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(QColor(15, 19, 26, 200))
        painter.drawEllipse(rect)

        # Foreground Progress Arc (90 degrees is top, span angle is negative for clockwise)
        span_angle = int(-(self.percentage / 100.0) * 360 * 16)
        painter.setPen(QPen(self.ring_color, 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, span_angle)

        # Center Content: Icon or Percentage Text
        if self.center_pixmap and not self.center_pixmap.isNull():
            icon_size = 20
            ix = dial_x + (dial_size - icon_size) / 2
            iy = dial_y + (dial_size - icon_size) / 2
            painter.drawPixmap(int(ix), int(iy), self.center_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            painter.setPen(QColor(248, 250, 252))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(QRectF(dial_x, dial_y + 6, dial_size, 14), Qt.AlignmentFlag.AlignCenter, f"{self.percentage:.1f}%" if self.percentage % 1 != 0 else f"{int(self.percentage)}%")
            
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.DemiBold))
            painter.drawText(QRectF(dial_x, dial_y + 20, dial_size, 14), Qt.AlignmentFlag.AlignCenter, self.header_text)

        # Subtext 1 (e.g. "2 Games" or "Main Role:")
        painter.setPen(QColor(226, 232, 240))
        painter.setFont(QFont("Segoe UI", 7, QFont.Weight.DemiBold))
        painter.drawText(QRectF(0, dial_size + 8, self.width(), 14), Qt.AlignmentFlag.AlignCenter, self.sub_text1)

        # Subtext 2 (e.g. "(2 Wins)" or "Top")
        if self.sub_text2:
            if "Win" in self.sub_text2:
                painter.setPen(QColor(56, 189, 248))  # Blue wins
            else:
                painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Normal))
            painter.drawText(QRectF(0, dial_size + 22, self.width(), 14), Qt.AlignmentFlag.AlignCenter, self.sub_text2)

        painter.end()
