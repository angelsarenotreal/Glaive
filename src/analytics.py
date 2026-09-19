from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Badge:
    label: str
    category: str  # "highlight", "good", "warning", "danger", "neutral"
    tooltip: str = ""

@dataclass
class RecentMatchSummary:
    champion: str
    kills: int
    deaths: int
    assists: int
    win: bool

@dataclass
class PlayerScoutingData:
    game_name: str
    tag_line: str
    champion_name: str
    team_id: int  # 100 for Blue/Order, 200 for Red/Chaos
    assigned_position: str = ""  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
    level: int = 1
    
    # Ranked Info
    tier: str = "UNRANKED"
    rank: str = ""
    league_points: int = 0
    ranked_wins: int = 0
    ranked_losses: int = 0
    
    # Champion Specific Form
    champion_games: int = 0
    champion_wins: int = 0
    
    # Recent Form (last 5-10 matches)
    recent_matches: List[RecentMatchSummary] = field(default_factory=list)
    recent_kills: float = 0.0
    recent_deaths: float = 0.0
    recent_assists: float = 0.0
    
    # Computed Tags & Badges
    badges: List[Badge] = field(default_factory=list)

    @property
    def display_riot_id(self) -> str:
        if self.tag_line:
            return f"{self.game_name} #{self.tag_line}"
        return self.game_name

    @property
    def ranked_winrate(self) -> float:
        total = self.ranked_wins + self.ranked_losses
        if total == 0:
            return 0.0
        return round((self.ranked_wins / total) * 100, 1)

    @property
    def champion_winrate(self) -> float:
        if self.champion_games == 0:
            return 0.0
        return round((self.champion_wins / self.champion_games) * 100, 1)

    @property
    def recent_kda(self) -> float:
        if self.recent_deaths == 0:
            return round(self.recent_kills + self.recent_assists, 2)
        return round((self.recent_kills + self.recent_assists) / self.recent_deaths, 2)

    @property
    def rank_label(self) -> str:
        if self.tier.upper() in ["UNRANKED", ""]:
            return "Unranked"
        if self.tier.upper() in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            return f"{self.tier.capitalize()} {self.league_points} LP"
        return f"{self.tier.capitalize()} {self.rank} ({self.league_points} LP)"


class AnalyticsEngine:
    """Calculates tactical tags, streaks, and threat evaluations for players."""

    @staticmethod
    def compute_player_badges(player: PlayerScoutingData) -> List[Badge]:
        badges: List[Badge] = []

        # 1. One-Trick / Main Champion Tag
        if player.champion_games >= 15:
            if player.champion_winrate >= 60.0:
                badges.append(Badge(
                    label=f"OTP {player.champion_winrate:.0f}%",
                    category="highlight",
                    tooltip=f"Champion specialist: {player.champion_games} games played with {player.champion_winrate}% win rate"
                ))
            elif player.champion_games >= 20:
                badges.append(Badge(
                    label="Main Champ",
                    category="good",
                    tooltip=f"{player.champion_games} games on {player.champion_name}"
                ))
        elif player.champion_games <= 1 and player.ranked_wins + player.ranked_losses >= 10:
            badges.append(Badge(
                label="First Time",
                category="warning",
                tooltip=f"Only {player.champion_games} ranked games recorded on {player.champion_name}"
            ))

        # 2. Recent Streaks (from recent matches)
        if player.recent_matches:
            wins_streak = 0
            loss_streak = 0
            for m in player.recent_matches:
                if m.win:
                    if loss_streak > 0:
                        break
                    wins_streak += 1
                else:
                    if wins_streak > 0:
                        break
                    loss_streak += 1

            if wins_streak >= 3:
                badges.append(Badge(
                    label=f"{wins_streak}W Streak",
                    category="highlight",
                    tooltip=f"Currently on a {wins_streak}-game win streak"
                ))
            elif loss_streak >= 3:
                badges.append(Badge(
                    label=f"{loss_streak}L Cold",
                    category="danger",
                    tooltip=f"Currently on a {loss_streak}-game loss streak"
                ))

        # 3. KDA Performance
        if player.recent_kda >= 4.0:
            badges.append(Badge(
                label=f"{player.recent_kda:.1f} KDA",
                category="good",
                tooltip=f"High recent KDA average: {player.recent_kda:.2f}"
            ))
        elif player.recent_deaths >= 8.0:
            badges.append(Badge(
                label="High Deaths",
                category="danger",
                tooltip=f"Averaging {player.recent_deaths:.1f} deaths per game recently"
            ))

        # 4. Seasonal Win Rate Skew
        total_ranked = player.ranked_wins + player.ranked_losses
        if total_ranked >= 20:
            if player.ranked_winrate >= 62.0:
                badges.append(Badge(
                    label=f"{player.ranked_winrate:.0f}% WR",
                    category="highlight",
                    tooltip=f"High seasonal win rate ({player.ranked_wins}W {player.ranked_losses}L)"
                ))
            elif player.ranked_winrate <= 44.0:
                badges.append(Badge(
                    label=f"{player.ranked_winrate:.0f}% Low WR",
                    category="warning",
                    tooltip=f"Low seasonal win rate ({player.ranked_wins}W {player.ranked_losses}L)"
                ))

        return badges
