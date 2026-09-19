from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from src.analytics import PlayerScoutingData, Badge
from src.asset_manager import AssetManager

class PlayerCardWidget(QFrame):
    """Clean, high-density player card with champion icons and colored W/L indicators."""

    def __init__(self, player: PlayerScoutingData, parent=None):
        super().__init__(parent)
        self.player = player
        self.asset_mgr = AssetManager()
        self.setObjectName("PlayerCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 7, 8, 7)
        main_layout.setSpacing(5)

        # ---------------- 1. Top Header Row: Champion Icon + Name + Riot ID ----------------
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Champion Square Icon
        champ_icon_label = QLabel()
        champ_pixmap = self.asset_mgr.get_champion_icon(self.player.champion_name, size=36, radius=6)
        champ_icon_label.setPixmap(champ_pixmap)
        champ_icon_label.setFixedSize(36, 36)
        champ_icon_label.setToolTip(f"Champion: {self.player.champion_name}")
        top_row.addWidget(champ_icon_label)

        # Name, Role, and Riot ID Container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)

        # Position Tag (TOP, JGL, MID, BOT, SUP)
        pos_text = self.player.assigned_position or "FLEX"
        pos_label = QLabel(pos_text)
        pos_label.setStyleSheet(
            "color: #94a3b8; font-size: 9px; font-weight: 700; "
            "background: rgba(255, 255, 255, 0.08); border-radius: 3px; padding: 1px 4px;"
        )
        name_row.addWidget(pos_label)

        # Champion Name
        champ_label = QLabel(self.player.champion_name)
        champ_label.setObjectName("ChampionName")
        name_row.addWidget(champ_label)

        # Player Riot ID
        player_name_label = QLabel(self.player.display_riot_id)
        player_name_label.setObjectName("PlayerName")
        name_row.addWidget(player_name_label)

        name_row.addStretch()

        # Level tag
        if self.player.level > 1:
            lvl_label = QLabel(f"Lv.{self.player.level}")
            lvl_label.setObjectName("StatLabel")
            name_row.addWidget(lvl_label)

        info_layout.addLayout(name_row)

        # Stats Sub-Row (Rank, WR%, Champ WR, KDA)
        stats_sub_row = QHBoxLayout()
        stats_sub_row.setSpacing(10)

        # Rank badge
        rank_label = QLabel(self.player.rank_label)
        rank_label.setObjectName("RankText")
        stats_sub_row.addWidget(rank_label)

        # Seasonal Winrate with color tint
        if (self.player.ranked_wins + self.player.ranked_losses) > 0:
            wr_val = self.player.ranked_winrate
            wr_color = "#38bdf8" if wr_val >= 55.0 else ("#f87171" if wr_val <= 46.0 else "#f8fafc")
            wr_text = f"<span style='color:{wr_color}; font-weight:700;'>{wr_val:.0f}%</span> ({self.player.ranked_wins}W {self.player.ranked_losses}L)"
        else:
            wr_text = "No Games"
        wr_label = QLabel(f"Rank: {wr_text}")
        wr_label.setObjectName("StatLabel")
        wr_label.setTextFormat(Qt.TextFormat.RichText)
        stats_sub_row.addWidget(wr_label)

        # Champion Winrate
        if self.player.champion_games > 0:
            c_val = self.player.champion_winrate
            c_color = "#38bdf8" if c_val >= 55.0 else ("#f87171" if c_val <= 46.0 else "#f8fafc")
            c_wr_text = f"<span style='color:{c_color}; font-weight:700;'>{c_val:.0f}%</span> ({self.player.champion_games}G)"
        else:
            c_wr_text = "0G"
        c_wr_label = QLabel(f"Champ: {c_wr_text}")
        c_wr_label.setObjectName("StatLabel")
        c_wr_label.setTextFormat(Qt.TextFormat.RichText)
        stats_sub_row.addWidget(c_wr_label)

        # Recent KDA
        if self.player.recent_matches:
            kda_color = "#38bdf8" if self.player.recent_kda >= 3.5 else ("#f87171" if self.player.recent_deaths >= 7.5 else "#f8fafc")
            kda_text = f"<span style='color:{kda_color}; font-weight:700;'>{self.player.recent_kda:.1f}</span> ({self.player.recent_kills:.1f}/{self.player.recent_deaths:.1f}/{self.player.recent_assists:.1f})"
            kda_label = QLabel(f"KDA: {kda_text}")
            kda_label.setObjectName("StatLabel")
            kda_label.setTextFormat(Qt.TextFormat.RichText)
            stats_sub_row.addWidget(kda_label)

        stats_sub_row.addStretch()
        info_layout.addLayout(stats_sub_row)

        top_row.addLayout(info_layout, 1)
        main_layout.addLayout(top_row)

        # ---------------- 2. Bottom Row: Badges & Colored W/L Indicators ----------------
        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)
        bot_row.setContentsMargins(44, 0, 0, 0)  # Align with info layout past the icon

        # Render Badges
        for badge in self.player.badges:
            b_label = QLabel(badge.label)
            if badge.tooltip:
                b_label.setToolTip(badge.tooltip)

            if badge.category == "highlight":
                b_label.setProperty("class", "BadgeHighlight")
            elif badge.category == "good":
                b_label.setProperty("class", "BadgeGood")
            elif badge.category == "warning":
                b_label.setProperty("class", "BadgeWarning")
            elif badge.category == "danger":
                b_label.setProperty("class", "BadgeDanger")
            else:
                b_label.setProperty("class", "BadgeNeutral")

            bot_row.addWidget(b_label)

        bot_row.addStretch()

        # Mini Recent Match History (5 Blue W / Red L indicator blocks)
        if self.player.recent_matches:
            match_dots_layout = QHBoxLayout()
            match_dots_layout.setSpacing(3)
            
            recent_label = QLabel("Recent:")
            recent_label.setObjectName("StatLabel")
            match_dots_layout.addWidget(recent_label)

            for m in self.player.recent_matches[:5]:
                dot = QLabel("W" if m.win else "L")
                if m.win:
                    # Blue for Wins
                    dot.setStyleSheet(
                        "color: #38bdf8; background-color: rgba(56, 189, 248, 0.16); "
                        "border: 1px solid rgba(56, 189, 248, 0.45); font-size: 9px; "
                        "font-weight: 800; border-radius: 3px; padding: 1px 4px;"
                    )
                else:
                    # Red for Losses
                    dot.setStyleSheet(
                        "color: #f87171; background-color: rgba(239, 68, 68, 0.16); "
                        "border: 1px solid rgba(239, 68, 68, 0.45); font-size: 9px; "
                        "font-weight: 800; border-radius: 3px; padding: 1px 4px;"
                    )
                dot.setToolTip(f"{m.champion} ({m.kills}/{m.deaths}/{m.assists}) - {'Victory' if m.win else 'Defeat'}")
                match_dots_layout.addWidget(dot)

            bot_row.addLayout(match_dots_layout)

        main_layout.addLayout(bot_row)
