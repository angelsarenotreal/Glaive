from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from src.analytics import PlayerScoutingData, Badge
from src.asset_manager import AssetManager, CircularGaugeWidget


class PlayerCardWidget(QFrame):
    """
    1:1 Reconstructed Porofessor In-Game Player Card.
    Separated with edge-to-edge 1px grid divider lines matching Porofessor reference:
    - Section 1: Header (Profile Icon + Name + Level + History button)
    - Divider 1: Full-width team accent bar (2px cyan/red)
    - Section 2: Upper Stats (50/50 split with vertical divider)
    - Divider 2: Full-width horizontal divider (1px)
    - Section 3: Middle Gauges (33/33/33 split with 2 vertical dividers)
    - Divider 3: Full-width horizontal divider (1px)
    - Section 4: Filling Tactical Tags Matrix
    """

    def __init__(self, player: PlayerScoutingData, parent=None):
        super().__init__(parent)
        self.player = player
        self.asset_mgr = AssetManager()
        self.setObjectName("PlayerCard")
        self.setFixedWidth(314)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------- 1. TOP HEADER: Profile Icon + Summoner Name + Level ----------------
        header_frame = QFrame()
        header_frame.setObjectName("CardHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.setSpacing(10)

        # Profile Icon (36x36)
        profile_label = QLabel()
        profile_pixmap = self.asset_mgr.get_profile_icon(self.player.profile_icon_id, size=36, radius=0)
        profile_label.setPixmap(profile_pixmap)
        profile_label.setFixedSize(36, 36)
        header_layout.addWidget(profile_label)

        # Name & Level
        name_col = QVBoxLayout()
        name_col.setSpacing(1)

        name_label = QLabel(self.player.display_riot_id)
        name_label.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800;")
        name_col.addWidget(name_label)

        level_label = QLabel(f"Level {self.player.level}")
        level_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        name_col.addWidget(level_label)

        header_layout.addLayout(name_col, 1)

        # History icon on top-right
        hist_icon = QLabel("↺")
        hist_icon.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(hist_icon)

        main_layout.addWidget(header_frame)

        # ---------------- DIVIDER 1: Full-Width Team Accent Bar ----------------
        div1 = QFrame()
        div1.setFixedHeight(2)
        accent_color = "#ef4444" if self.player.team_id == 200 else "#38bdf8"
        div1.setStyleSheet(f"background-color: {accent_color};")
        main_layout.addWidget(div1)

        # ---------------- 2. UPPER STATS: 2-Column (50% / 50% with Vertical Divider) ----------------
        stats_frame = QFrame()
        stats_frame.setObjectName("CardStats")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 8, 0, 8)
        stats_layout.setSpacing(0)

        # --- Left Column: Champion Stats (50%) ---
        left_widget = QWidget()
        left_col = QVBoxLayout(left_widget)
        left_col.setContentsMargins(6, 0, 6, 0)
        left_col.setSpacing(2)
        left_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        champ_row = QHBoxLayout()
        champ_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        champ_row.setSpacing(6)

        # Dual Spells stacked vertically (20x20 each)
        spells_col = QVBoxLayout()
        spells_col.setSpacing(2)
        sp1 = QLabel()
        sp1.setPixmap(self.asset_mgr.get_spell_icon(self.player.spell1_name, size=20, radius=0))
        sp1.setFixedSize(20, 20)
        sp2 = QLabel()
        sp2.setPixmap(self.asset_mgr.get_spell_icon(self.player.spell2_name, size=20, radius=0))
        sp2.setFixedSize(20, 20)
        spells_col.addWidget(sp1)
        spells_col.addWidget(sp2)
        champ_row.addLayout(spells_col)

        # Champion Square Icon (46x46)
        champ_icon = QLabel()
        champ_icon.setPixmap(self.asset_mgr.get_champion_icon(self.player.champion_name, size=46, radius=0))
        champ_icon.setFixedSize(46, 46)
        champ_row.addWidget(champ_icon)

        # Mastery Level Badge
        mastery_label = QLabel(f"LVL {self.player.champion_mastery_level}")
        mastery_label.setStyleSheet(
            "color: #cbd5e1; font-size: 9px; font-weight: 800; "
            "background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255, 255, 255, 0.2); "
            "border-radius: 0px; padding: 2px 5px;"
        )
        champ_row.addWidget(mastery_label)
        left_col.addLayout(champ_row)

        # KDA line: Green kills / Red deaths / Amber assists
        kda_label = QLabel(
            f"<span style='color:#34d399; font-weight:800;'>{self.player.champion_kills_str}</span> / "
            f"<span style='color:#f87171; font-weight:800;'>{self.player.champion_deaths_str}</span> / "
            f"<span style='color:#fbbf24; font-weight:800;'>{self.player.champion_assists_str}</span>"
        )
        kda_label.setStyleSheet("font-size: 12px;")
        kda_label.setTextFormat(Qt.TextFormat.RichText)
        kda_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(kda_label)

        # Champion Winrate line
        c_wr_color = "#38bdf8" if self.player.champion_winrate >= 50 else "#f87171"
        champ_wr_label = QLabel(
            f"<span style='color:{c_wr_color}; font-weight:700;'>{self.player.champion_winrate:.0f}%</span> "
            f"<span style='color:#94a3b8;'>({self.player.champion_wins} / {self.player.champion_games})</span>"
        )
        champ_wr_label.setStyleSheet("font-size: 11px;")
        champ_wr_label.setTextFormat(Qt.TextFormat.RichText)
        champ_wr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(champ_wr_label)

        # Champion Leaderboard Rank
        champ_rank_label = QLabel(self.player.champion_server_rank)
        champ_rank_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600;")
        champ_rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(champ_rank_label)

        stats_layout.addWidget(left_widget, 1)

        # Vertical Divider between Champion & Ranked columns
        v_sep1 = QFrame()
        v_sep1.setFixedWidth(1)
        v_sep1.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        stats_layout.addWidget(v_sep1)

        # --- Right Column: Ranked Stats (50%) ---
        right_widget = QWidget()
        right_col = QVBoxLayout(right_widget)
        right_col.setContentsMargins(6, 0, 6, 0)
        right_col.setSpacing(2)
        right_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Rank Wings Image (46x46)
        crest_row = QHBoxLayout()
        crest_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        crest_label = QLabel()
        crest_pixmap = self.asset_mgr.get_ranked_crest(self.player.tier, size=46)
        crest_label.setPixmap(crest_pixmap)
        crest_label.setFixedSize(46, 46)
        crest_row.addWidget(crest_label)
        right_col.addLayout(crest_row)

        # Tier & LP
        rank_tier_label = QLabel(self.player.rank_label)
        rank_tier_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 800;")
        rank_tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(rank_tier_label)

        # Ranked Winrate line
        r_wr_color = "#38bdf8" if self.player.ranked_winrate >= 50 else "#f87171"
        total_ranked = self.player.ranked_wins + self.player.ranked_losses
        ranked_wr_label = QLabel(
            f"<span style='color:{r_wr_color}; font-weight:700;'>{self.player.ranked_winrate:.0f}%</span> "
            f"<span style='color:#94a3b8;'>({self.player.ranked_wins} / {total_ranked})</span>"
        )
        ranked_wr_label.setStyleSheet("font-size: 11px;")
        ranked_wr_label.setTextFormat(Qt.TextFormat.RichText)
        ranked_wr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(ranked_wr_label)

        # Overall Server Rank
        srv_rank_label = QLabel(self.player.server_rank)
        srv_rank_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600;")
        srv_rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(srv_rank_label)

        stats_layout.addWidget(right_widget, 1)
        main_layout.addWidget(stats_frame)

        # ---------------- DIVIDER 2: Full-Width Horizontal Line ----------------
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        main_layout.addWidget(div2)

        # ---------------- 3. MIDDLE GAUGES: 3 Columns with 2 Vertical Dividers ----------------
        gauges_frame = QFrame()
        gauges_frame.setObjectName("CardGauges")
        gauges_layout = QHBoxLayout(gauges_frame)
        gauges_layout.setContentsMargins(0, 6, 0, 6)
        gauges_layout.setSpacing(0)

        # 1. 12 Hr Gauge Column
        g12_color = QColor(16, 185, 129) if self.player.twelve_hr_winrate >= 50 else (QColor(239, 68, 68) if self.player.twelve_hr_games > 0 else QColor(100, 116, 139))
        gauge_12hr = CircularGaugeWidget(
            percentage=self.player.twelve_hr_winrate,
            header_text="12 Hr",
            sub_text1=f"{self.player.twelve_hr_games} Games",
            sub_text2=f"({self.player.twelve_hr_wins} Wins)",
            ring_color=g12_color
        )
        gauges_layout.addWidget(gauge_12hr, 1)

        # Vertical Divider 1
        g_vsep1 = QFrame()
        g_vsep1.setFixedWidth(1)
        g_vsep1.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        gauges_layout.addWidget(g_vsep1)

        # 2. Main Role Gauge Column
        role_icon = self.asset_mgr.get_role_icon(self.player.main_role, size=24)
        role_ring_color = QColor(245, 158, 11) if self.player.is_autofilled else QColor(56, 189, 248)
        gauge_role = CircularGaugeWidget(
            percentage=100.0,
            header_text="",
            sub_text1="Main Role:",
            sub_text2=self.player.main_role,
            ring_color=role_ring_color,
            center_pixmap=role_icon
        )
        gauges_layout.addWidget(gauge_role, 1)

        # Vertical Divider 2
        g_vsep2 = QFrame()
        g_vsep2.setFixedWidth(1)
        g_vsep2.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        gauges_layout.addWidget(g_vsep2)

        # 3. 30 Day Gauge Column
        g30_color = QColor(16, 185, 129) if self.player.thirty_day_winrate >= 50 else QColor(239, 68, 68)
        gauge_30d = CircularGaugeWidget(
            percentage=self.player.thirty_day_winrate,
            header_text="30 Day",
            sub_text1=f"{self.player.thirty_day_games} Games",
            sub_text2=f"({self.player.thirty_day_wins} Wins)",
            ring_color=g30_color
        )
        gauges_layout.addWidget(gauge_30d, 1)

        main_layout.addWidget(gauges_frame)

        # ---------------- DIVIDER 3: Full-Width Horizontal Line ----------------
        div3 = QFrame()
        div3.setFixedHeight(1)
        div3.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        main_layout.addWidget(div3)

        # ---------------- 4. BOTTOM: Tag Badges Matrix (Adaptive Fit & Rounded Corners) ----------------
        tags_frame = QFrame()
        tags_frame.setObjectName("CardTags")
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(8, 8, 8, 8)
        tags_layout.setSpacing(6)
        tags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def get_badge_style(category: str) -> str:
            if category in ["good", "highlight"]:
                return (
                    "border: 1px solid #10b981; color: #34d399; background-color: rgba(16, 185, 129, 0.14); "
                    "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 700; min-height: 22px;"
                )
            elif category == "warning":
                return (
                    "border: 1px solid #f59e0b; color: #fbbf24; background-color: rgba(245, 158, 11, 0.14); "
                    "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 700; min-height: 22px;"
                )
            elif category == "danger":
                return (
                    "border: 1px solid #ef4444; color: #f87171; background-color: rgba(239, 68, 68, 0.14); "
                    "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 700; min-height: 22px;"
                )
            elif category == "pro":
                return (
                    "border: 1px solid #38bdf8; color: #38bdf8; background-color: rgba(56, 189, 248, 0.18); "
                    "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 800; min-height: 22px;"
                )
            else:
                return (
                    "border: 1px solid rgba(255, 255, 255, 0.22); color: #e2e8f0; background-color: rgba(255, 255, 255, 0.08); "
                    "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600; min-height: 22px;"
                )

        # Group badges into adaptive rows
        badge_rows = []
        i = 0
        badges = self.player.badges
        n = len(badges)
        while i < n:
            if i + 3 <= n:
                b1, b2, b3 = badges[i], badges[i+1], badges[i+2]
                if len(b1.label) + len(b2.label) + len(b3.label) <= 30 and max(len(b1.label), len(b2.label), len(b3.label)) <= 12:
                    badge_rows.append([b1, b2, b3])
                    i += 3
                    continue
            if i + 2 <= n:
                b1, b2 = badges[i], badges[i+1]
                if len(b1.label) + len(b2.label) <= 34:
                    badge_rows.append([b1, b2])
                    i += 2
                    continue
            badge_rows.append([badges[i]])
            i += 1

        for row_badges in badge_rows:
            row_layout = QHBoxLayout()
            row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.setSpacing(6)
            row_layout.addStretch()

            for b in row_badges:
                b_label = QLabel(b.label)
                if b.tooltip:
                    b_label.setToolTip(b.tooltip)
                b_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                b_label.setStyleSheet(get_badge_style(b.category))
                row_layout.addWidget(b_label)

            row_layout.addStretch()
            tags_layout.addLayout(row_layout)

        main_layout.addWidget(tags_frame)
        main_layout.addStretch()
