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
    champion_mastery_level: int = 1
    champion_kills_str: str = ""
    champion_deaths_str: str = ""
    champion_assists_str: str = ""
    champion_games: int = 0
    champion_wins: int = 0
    champion_server_rank: str = ""

    # Ranked Overview
    tier: str = "UNRANKED"
    rank: str = ""
    league_points: int = 0
    ranked_wins: int = 0
    ranked_losses: int = 0
    server_rank: str = ""

    # 12-Hour & 30-Day Activity
    twelve_hr_games: int = 0
    twelve_hr_wins: int = 0
    thirty_day_games: int = 0
    thirty_day_wins: int = 0
    main_role: str = ""
    is_autofilled: bool = False

    # Detailed Heuristic Attributes
    champion_mastery_points: int = 0
    cs_per_minute: float = 0.0
    kill_participation_pct: float = 0.0
    vision_score_per_minute: float = 0.0
    first_blood_participation_pct: float = 0.0
    kills_at_15: float = 0.0
    deaths_at_15: float = 0.0

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
        if self.tier.upper() == "UNRANKED" or not self.tier:
            return "Unranked"
        if self.tier.upper() in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            return f"{t} {self.league_points} LP"
        return f"{t} {self.rank} {self.league_points} LP"


class AnalyticsEngine:
    """
    Calculates tactical tags, streaks, and threat evaluations matching Porofessor's Heuristics Engine.
    Implements core rules grounded in genuine, verified player statistics.
    """

    @staticmethod
    def compute_player_badges(player: PlayerScoutingData) -> List[Badge]:
        # If player already has curated badges, return them
        if player.badges:
            return player.badges

        badges: List[Badge] = []

        # 1. Millionaire Badge: Real 1,000,000+ points or mastery lvl >= 100
        if player.champion_mastery_points >= 1_000_000 or player.champion_mastery_level >= 100:
            badges.append(Badge(f"Millionaire: {player.champion_name}", "good", "Over 1 Million Mastery Points"))

        # 2. OTP {Champion}: Mastery > 300k OR Winrate >= 60% with games >= 15
        elif (player.champion_mastery_points >= 300_000 or player.champion_mastery_level >= 30 or (player.champion_winrate >= 60.0 and player.champion_games >= 15)):
            badges.append(Badge(f"OTP {player.champion_name}", "good", "Champion Specialist / High mastery volume"))

        # 3. High Mastery Veteran: 100k+ points or level >= 10
        elif player.champion_mastery_points >= 100_000 or player.champion_mastery_level >= 10:
            badges.append(Badge(f"Mastery Lvl {player.champion_mastery_level}", "highlight", f"{player.champion_mastery_points:,} mastery points on {player.champion_name}"))

        # 4. First Time / Casual: Mastery level <= 2 AND low points
        if player.champion_mastery_level <= 1 and player.champion_mastery_points < 3_000:
            badges.append(Badge(f"First Time {player.champion_name}", "warning", f"Under 3,000 mastery points on {player.champion_name}"))
        elif player.champion_mastery_level <= 3 and player.champion_mastery_points < 15_000:
            badges.append(Badge(f"{player.champion_name} casual", "danger", f"Low games ({player.champion_mastery_points:,} pts) on {player.champion_name}"))

        # 5. Good CSer: Average CS/min >= 8.0
        if player.cs_per_minute >= 8.0 and player.assigned_position.upper() in ["TOP", "MIDDLE", "BOTTOM"]:
            badges.append(Badge("Good CSer", "good", f"Averages {player.cs_per_minute:.1f} CS/Min"))

        # 6. Aggressive Laner
        if player.first_blood_participation_pct >= 30.0 or player.kills_at_15 >= 2.5:
            badges.append(Badge("Aggressive Laner", "good", "High early forward kill pressure in lane"))

        # 7. Vulnerable Laner
        if player.deaths_at_15 >= 2.0:
            badges.append(Badge("Vulnerable Laner", "danger", "High early death frequency in lane"))

        # 8. Good vision
        is_support = player.assigned_position.upper() == "UTILITY"
        threshold = 2.5 if is_support else 1.5
        if player.vision_score_per_minute >= threshold:
            badges.append(Badge("Good vision", "good", "Places high quantity of control & stealth wards"))

        # 9. High Kill Participation
        if player.kill_participation_pct >= 65.0:
            badges.append(Badge("High Kill Participation", "good", f"Involved in {player.kill_participation_pct:.0f}% of team kills"))

        # 10. Godlike {Champion}: Win rate on champ >= 70% with at least 10 games
        if player.champion_winrate >= 70.0 and player.champion_games >= 10:
            badges.append(Badge(f"Godlike {player.champion_name}", "good", f"{player.champion_winrate:.0f}% WR on {player.champion_name}"))

        # 11. Streaks
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
                badges.append(Badge(label=f"{wins_streak}W Streak", category="highlight", tooltip=f"Currently on a {wins_streak}-game win streak"))
            elif loss_streak >= 3:
                badges.append(Badge(label=f"{loss_streak}L Cold", category="danger", tooltip=f"Currently on a {loss_streak}-game loss streak"))

        return badges

