from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Badge:
    label: str
    category: str  # "highlight", "good", "warning", "danger", "neutral", "pro"
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
    team_id: int  # 100 for Blue/Order (Top Row), 200 for Red/Chaos (Bottom Row)
    assigned_position: str = "TOP"  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
    level: int = 1
    profile_icon_id: int = 588

    # Summoner Spells
    spell1_name: str = "flash"
    spell2_name: str = "teleport"

    # Champion Specific Form & Mastery
    champion_mastery_level: int = 209
    champion_kills_str: str = "6.2"
    champion_deaths_str: str = "3.7"
    champion_assists_str: str = "4.7"
    champion_games: int = 201
    champion_wins: int = 117
    champion_server_rank: str = "Rank: #80"

    # Ranked Overview
    tier: str = "GRANDMASTER"
    rank: str = ""
    league_points: int = 807
    ranked_wins: int = 198
    ranked_losses: int = 164
    server_rank: str = "Rank: #4,608"

    # 12-Hour & 30-Day Activity
    twelve_hr_games: int = 2
    twelve_hr_wins: int = 2
    thirty_day_games: int = 277
    thirty_day_wins: int = 162
    main_role: str = "Top"
    is_autofilled: bool = False

    # Recent Matches
    recent_matches: List[RecentMatchSummary] = field(default_factory=list)
    badges: List[Badge] = field(default_factory=list)

    @property
    def display_riot_id(self) -> str:
        if self.tag_line:
            return f"{self.game_name}#{self.tag_line}"
        return self.game_name

    @property
    def twelve_hr_winrate(self) -> float:
        if self.twelve_hr_games == 0:
            return 0.0
        return round((self.twelve_hr_wins / self.twelve_hr_games) * 100, 1)

    @property
    def thirty_day_winrate(self) -> float:
        if self.thirty_day_games == 0:
            return 0.0
        return round((self.thirty_day_wins / self.thirty_day_games) * 100, 1)

    @property
    def champion_winrate(self) -> float:
        if self.champion_games == 0:
            return 0.0
        return round((self.champion_wins / self.champion_games) * 100, 1)

    @property
    def ranked_winrate(self) -> float:
        total = self.ranked_wins + self.ranked_losses
        if total == 0:
            return 0.0
        return round((self.ranked_wins / total) * 100, 1)

    @property
    def rank_label(self) -> str:
        t = self.tier.capitalize()
        if self.tier.upper() in ["MASTER", "GRANDMASTER", "CHALLENGER", "UNRANKED"]:
            return f"{t} {self.league_points} LP" if self.tier.upper() != "UNRANKED" else "Unranked"
        return f"{t} {self.rank} {self.league_points} LP"


class AnalyticsEngine:
    """Calculates tactical tags, streaks, and threat evaluations matching Porofessor."""

    @staticmethod
    def compute_player_badges(player: PlayerScoutingData) -> List[Badge]:
        # If player already has curated badges (e.g. from mock/live), return them
        if player.badges:
            return player.badges

        badges: List[Badge] = []

        # 1. First game of day
        if player.twelve_hr_games == 0:
            badges.append(Badge("Waking up", "warning", "First game of the day"))

        # 2. OTP / Mastery / First Time
        if player.champion_mastery_level >= 100:
            badges.append(Badge(f"Millionaire: {player.champion_name}", "good", f"Mastery Level {player.champion_mastery_level}"))
        if player.champion_winrate >= 60.0 and player.champion_games >= 15:
            badges.append(Badge(f"Godlike {player.champion_name}", "good", f"High win rate on {player.champion_name}"))
            badges.append(Badge(f"OTP {player.champion_name}", "good", f"{player.champion_games} games played"))
        elif player.champion_games <= 1 and (player.ranked_wins + player.ranked_losses) >= 10:
            badges.append(Badge("First Time", "warning", f"Only {player.champion_games} games recorded on {player.champion_name}"))

        # 3. Recent Streaks (from recent matches)
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

        # 4. Aggression / CS / Vision
        if player.assigned_position.upper() in ["TOP", "MIDDLE", "BOTTOM"]:
            badges.append(Badge("Good CSer", "good", "Averages >7.5 CS/Min"))
            badges.append(Badge("Aggressive Laner", "good", "High early lane pressure"))
        elif player.assigned_position.upper() == "JUNGLE":
            badges.append(Badge("Aggressive Jungler", "good", "Frequent early invades and ganks"))
            badges.append(Badge("Good vision", "good", "High vision score"))
        elif player.assigned_position.upper() == "UTILITY":
            badges.append(Badge("Roaming", "warning", "Roams frequently to other lanes"))
            badges.append(Badge("Good vision", "good", "High vision score"))

        return badges

