from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from src.analytics import PlayerScoutingData, Badge

class PlayerCardWidget(QFrame):
    """Clean, high-density monochrome player card for in-game scouting."""

    def __init__(self, player: PlayerScoutingData, parent=None):
        super().__init__(parent)
        self.player = player
        self.setObjectName("PlayerCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(5)

        # ---------------- 1. Top Header Row ----------------
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Position / Role tag
        pos_text = self.player.assigned_position or "FLEX"
        pos_label = QLabel(pos_text)
        pos_label.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 700; "
            "background: rgba(255, 255, 255, 0.06); border-radius: 3px; padding: 1px 4px;"
        )
        top_row.addWidget(pos_label)

        # Champion Name
        champ_label = QLabel(self.player.champion_name)
        champ_label.setObjectName("ChampionName")
        top_row.addWidget(champ_label)

        # Player Riot ID
        player_name_label = QLabel(self.player.display_riot_id)
        player_name_label.setObjectName("PlayerName")
        top_row.addWidget(player_name_label)

        top_row.addStretch()

        # Level tag
        if self.player.level > 1:
            lvl_label = QLabel(f"Lv.{self.player.level}")
            lvl_label.setObjectName("StatLabel")
            top_row.addWidget(lvl_label)

        main_layout.addLayout(top_row)

        # ---------------- 2. Middle Stats Row ----------------
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Rank badge
        rank_label = QLabel(self.player.rank_label)
        rank_label.setObjectName("RankText")
        mid_row.addWidget(rank_label)

        # Seasonal Winrate
        if (self.player.ranked_wins + self.player.ranked_losses) > 0:
            wr_text = f"{self.player.ranked_winrate:.0f}% ({self.player.ranked_wins}W {self.player.ranked_losses}L)"
        else:
            wr_text = "No Games"
        wr_label = QLabel(f"Rank WR: <span style='color:#f8fafc; font-weight:600;'>{wr_text}</span>")
        wr_label.setObjectName("StatLabel")
        wr_label.setTextFormat(Qt.TextFormat.RichText)
        mid_row.addWidget(wr_label)

        # Champion Winrate
        if self.player.champion_games > 0:
            c_wr_text = f"{self.player.champion_winrate:.0f}% ({self.player.champion_games}G)"
        else:
            c_wr_text = "0G"
        c_wr_label = QLabel(f"Champ: <span style='color:#f8fafc; font-weight:600;'>{c_wr_text}</span>")
        c_wr_label.setObjectName("StatLabel")
        c_wr_label.setTextFormat(Qt.TextFormat.RichText)
        mid_row.addWidget(c_wr_label)

        # Recent KDA
        if self.player.recent_matches:
            kda_text = f"{self.player.recent_kda:.1f} ({self.player.recent_kills:.1f}/{self.player.recent_deaths:.1f}/{self.player.recent_assists:.1f})"
            kda_label = QLabel(f"KDA: <span style='color:#f8fafc; font-weight:600;'>{kda_text}</span>")
            kda_label.setObjectName("StatLabel")
            kda_label.setTextFormat(Qt.TextFormat.RichText)
            mid_row.addWidget(kda_label)

        mid_row.addStretch()
        main_layout.addLayout(mid_row)

        # ---------------- 3. Bottom Row: Badges & Recent Match Dots ----------------
        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)

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

        # Mini Recent Match History (5 indicator blocks)
        if self.player.recent_matches:
            match_dots_layout = QHBoxLayout()
            match_dots_layout.setSpacing(3)
            
            recent_label = QLabel("Recent:")
            recent_label.setObjectName("StatLabel")
            match_dots_layout.addWidget(recent_label)

            for m in self.player.recent_matches[:5]:
                dot = QLabel("W" if m.win else "L")
                if m.win:
                    dot.setStyleSheet(
                        "color: #ffffff; background-color: rgba(255, 255, 255, 0.18); "
                        "border: 1px solid rgba(255, 255, 255, 0.3); font-size: 9px; "
                        "font-weight: 700; border-radius: 3px; padding: 1px 3px;"
                    )
                else:
                    dot.setStyleSheet(
                        "color: #94a3b8; background-color: rgba(255, 255, 255, 0.04); "
                        "border: 1px solid rgba(255, 255, 255, 0.08); font-size: 9px; "
                        "font-weight: 600; border-radius: 3px; padding: 1px 3px;"
                    )
                dot.setToolTip(f"{m.champion} ({m.kills}/{m.deaths}/{m.assists}) - {'Victory' if m.win else 'Defeat'}")
                match_dots_layout.addWidget(dot)

            bot_row.addLayout(match_dots_layout)

        main_layout.addLayout(bot_row)
