from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from src.analytics import PlayerScoutingData, Badge
from src.asset_manager import AssetManager, CircularGaugeWidget


class FlowLayout(QHBoxLayout):
    """Simple wrapping layout for dynamic badge pills."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(4)


class PlayerCardWidget(QFrame):
    """
    1:1 Reconstructed Porofessor In-Game Player Card.
    Features profile icon, dual summoner spells, mastery crest, rank wings,
    3 circular gauges (12 Hr, Main Role, 30 Day), and color-coded tactical tags.
    """

    def __init__(self, player: PlayerScoutingData, parent=None):
        super().__init__(parent)
        self.player = player
        self.asset_mgr = AssetManager()
        self.setObjectName("PlayerCard")
        self.setFixedWidth(295)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ---------------- 1. TOP HEADER: Profile Icon + Summoner Name + Level ----------------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Circular Profile Icon
        profile_label = QLabel()
        profile_pixmap = self.asset_mgr.get_profile_icon(self.player.profile_icon_id, size=28)
        profile_label.setPixmap(profile_pixmap)
        profile_label.setFixedSize(28, 28)
        header_layout.addWidget(profile_label)

        # Name & Level
        name_col = QVBoxLayout()
        name_col.setSpacing(0)

        name_label = QLabel(self.player.display_riot_id)
        name_label.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 700;")
        name_col.addWidget(name_label)

        level_label = QLabel(f"Level {self.player.level}")
        level_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 500;")
        name_col.addWidget(level_label)

        header_layout.addLayout(name_col, 1)

        # Subtle history icon on top-right
        hist_icon = QLabel("↺")
        hist_icon.setStyleSheet("color: #64748b; font-size: 12px;")
        header_layout.addWidget(hist_icon)

        main_layout.addLayout(header_layout)

        # Divider
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
        main_layout.addWidget(div1)

        # ---------------- 2. UPPER STATS: 2-Column Champion vs Ranked Crest ----------------
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        # --- Left Column: Spells + Champion Icon + KDA + Champ WR + Champ Rank ---
        left_col = QVBoxLayout()
        left_col.setSpacing(2)

        champ_row = QHBoxLayout()
        champ_row.setSpacing(4)

        # Dual Spells stacked vertically
        spells_col = QVBoxLayout()
        spells_col.setSpacing(2)
        sp1 = QLabel()
        sp1.setPixmap(self.asset_mgr.get_spell_icon(self.player.spell1_name, size=16, radius=3))
        sp1.setFixedSize(16, 16)
        sp2 = QLabel()
        sp2.setPixmap(self.asset_mgr.get_spell_icon(self.player.spell2_name, size=16, radius=3))
        sp2.setFixedSize(16, 16)
        spells_col.addWidget(sp1)
        spells_col.addWidget(sp2)
        champ_row.addLayout(spells_col)

        # Champion Square Icon
        champ_icon = QLabel()
        champ_icon.setPixmap(self.asset_mgr.get_champion_icon(self.player.champion_name, size=36, radius=4))
        champ_icon.setFixedSize(36, 36)
        champ_row.addWidget(champ_icon)

        # Mastery Level Badge
        mastery_label = QLabel(f"LVL {self.player.champion_mastery_level}")
        mastery_label.setStyleSheet(
            "color: #cbd5e1; font-size: 8px; font-weight: 800; "
            "background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(255, 255, 255, 0.15); "
            "border-radius: 3px; padding: 2px 4px;"
        )
        champ_row.addWidget(mastery_label)
        champ_row.addStretch()
        left_col.addLayout(champ_row)

        # KDA line: Green kills / Red deaths / Amber assists
        kda_label = QLabel(
            f"<span style='color:#34d399; font-weight:700;'>{self.player.champion_kills_str}</span> / "
            f"<span style='color:#f87171; font-weight:700;'>{self.player.champion_deaths_str}</span> / "
            f"<span style='color:#fbbf24; font-weight:700;'>{self.player.champion_assists_str}</span>"
        )
        kda_label.setStyleSheet("font-size: 10px;")
        kda_label.setTextFormat(Qt.TextFormat.RichText)
        left_col.addWidget(kda_label)

        # Champion Winrate line
        c_wr_color = "#38bdf8" if self.player.champion_winrate >= 50 else "#f87171"
        champ_wr_label = QLabel(
            f"<span style='color:{c_wr_color}; font-weight:600;'>{self.player.champion_winrate:.0f}%</span> "
            f"<span style='color:#94a3b8;'>({self.player.champion_wins} / {self.player.champion_games})</span>"
        )
        champ_wr_label.setStyleSheet("font-size: 9px;")
        champ_wr_label.setTextFormat(Qt.TextFormat.RichText)
        left_col.addWidget(champ_wr_label)

        # Champion Leaderboard Rank
        champ_rank_label = QLabel(self.player.champion_server_rank)
        champ_rank_label.setStyleSheet("color: #64748b; font-size: 9px; font-weight: 500;")
        left_col.addWidget(champ_rank_label)

        stats_layout.addLayout(left_col, 1)

        # Vertical Divider
        v_sep = QFrame()
        v_sep.setFixedWidth(1)
        v_sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")
        stats_layout.addWidget(v_sep)

        # --- Right Column: Ranked Crest + Tier LP + Ranked WR + Server Rank ---
        right_col = QVBoxLayout()
        right_col.setSpacing(2)

        # Rank Wings Image
        crest_row = QHBoxLayout()
        crest_label = QLabel()
        crest_pixmap = self.asset_mgr.get_ranked_crest(self.player.tier, size=34)
        crest_label.setPixmap(crest_pixmap)
        crest_label.setFixedSize(34, 34)
        crest_row.addWidget(crest_label)
        crest_row.addStretch()
        right_col.addLayout(crest_row)

        # Tier & LP
        rank_tier_label = QLabel(self.player.rank_label)
        rank_tier_label.setStyleSheet("color: #ffffff; font-size: 10px; font-weight: 700;")
        right_col.addWidget(rank_tier_label)

        # Ranked Winrate line
        r_wr_color = "#38bdf8" if self.player.ranked_winrate >= 50 else "#f87171"
        total_ranked = self.player.ranked_wins + self.player.ranked_losses
        ranked_wr_label = QLabel(
            f"<span style='color:{r_wr_color}; font-weight:600;'>{self.player.ranked_winrate:.0f}%</span> "
            f"<span style='color:#94a3b8;'>({self.player.ranked_wins} / {total_ranked})</span>"
        )
        ranked_wr_label.setStyleSheet("font-size: 9px;")
        ranked_wr_label.setTextFormat(Qt.TextFormat.RichText)
        right_col.addWidget(ranked_wr_label)

        # Overall Server Rank
        srv_rank_label = QLabel(self.player.server_rank)
        srv_rank_label.setStyleSheet("color: #64748b; font-size: 9px; font-weight: 500;")
        right_col.addWidget(srv_rank_label)

        stats_layout.addLayout(right_col, 1)
        main_layout.addLayout(stats_layout)

        # Divider
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
        main_layout.addWidget(div2)

        # ---------------- 3. MIDDLE GAUGES: 12 Hr, Main Role, 30 Day ----------------
        gauges_layout = QHBoxLayout()
        gauges_layout.setSpacing(6)
        gauges_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. 12 Hr Gauge
        g12_color = QColor(16, 185, 129) if self.player.twelve_hr_winrate >= 50 else (QColor(239, 68, 68) if self.player.twelve_hr_games > 0 else QColor(100, 116, 139))
        gauge_12hr = CircularGaugeWidget(
            percentage=self.player.twelve_hr_winrate,
            header_text="12 Hr",
            sub_text1=f"{self.player.twelve_hr_games} Games",
            sub_text2=f"({self.player.twelve_hr_wins} Wins)",
            ring_color=g12_color
        )
        gauges_layout.addWidget(gauge_12hr)

        # 2. Main Role Gauge (Center icon mode)
        role_icon = self.asset_mgr.get_role_icon(self.player.main_role, size=22)
        role_ring_color = QColor(245, 158, 11) if self.player.is_autofilled else QColor(56, 189, 248)
        gauge_role = CircularGaugeWidget(
            percentage=100.0,
            header_text="",
            sub_text1="Main Role:",
            sub_text2=self.player.main_role,
            ring_color=role_ring_color,
            center_pixmap=role_icon
        )
        gauges_layout.addWidget(gauge_role)

        # 3. 30 Day Gauge
        g30_color = QColor(16, 185, 129) if self.player.thirty_day_winrate >= 50 else QColor(239, 68, 68)
        gauge_30d = CircularGaugeWidget(
            percentage=self.player.thirty_day_winrate,
            header_text="30 Day",
            sub_text1=f"{self.player.thirty_day_games} Games",
            sub_text2=f"({self.player.thirty_day_wins} Wins)",
            ring_color=g30_color
        )
        gauges_layout.addWidget(gauge_30d)

        main_layout.addLayout(gauges_layout)

        # Divider
        div3 = QFrame()
        div3.setFixedHeight(1)
        div3.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
        main_layout.addWidget(div3)

        # ---------------- 4. BOTTOM: Tag Badges Matrix ----------------
        tags_container = QVBoxLayout()
        tags_container.setSpacing(4)

        # Group badges into rows of 2 or 3
        current_row = QHBoxLayout()
        current_row.setSpacing(4)
        count_in_row = 0

        for badge in self.player.badges:
            b_label = QLabel(badge.label)
            if badge.tooltip:
                b_label.setToolTip(badge.tooltip)

            # Apply Porofessor colored border styles
            if badge.category in ["good", "highlight"]:
                # Cyan/Emerald border & text
                b_label.setStyleSheet(
                    "border: 1px solid #10b981; color: #34d399; background-color: rgba(16, 185, 129, 0.08); "
                    "border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 600;"
                )
            elif badge.category == "warning":
                # Amber/Gold border & text
                b_label.setStyleSheet(
                    "border: 1px solid #f59e0b; color: #fbbf24; background-color: rgba(245, 158, 11, 0.08); "
                    "border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 600;"
                )
            elif badge.category == "danger":
                # Red border & text
                b_label.setStyleSheet(
                    "border: 1px solid #ef4444; color: #f87171; background-color: rgba(239, 68, 68, 0.08); "
                    "border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 600;"
                )
            elif badge.category == "pro":
                # Electric Blue border & text
                b_label.setStyleSheet(
                    "border: 1px solid #38bdf8; color: #38bdf8; background-color: rgba(56, 189, 248, 0.12); "
                    "border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 700;"
                )
            else:
                b_label.setStyleSheet(
                    "border: 1px solid rgba(255, 255, 255, 0.15); color: #cbd5e1; background-color: rgba(255, 255, 255, 0.04); "
                    "border-radius: 4px; padding: 2px 6px; font-size: 9px; font-weight: 500;"
                )

            current_row.addWidget(b_label)
            count_in_row += 1

            if count_in_row >= 2:
                current_row.addStretch()
                tags_container.addLayout(current_row)
                current_row = QHBoxLayout()
                current_row.setSpacing(4)
                count_in_row = 0

        if count_in_row > 0:
            current_row.addStretch()
            tags_container.addLayout(current_row)

        main_layout.addLayout(tags_container)
        main_layout.addStretch()
