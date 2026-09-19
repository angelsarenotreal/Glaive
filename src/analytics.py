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

    # Detailed Heuristic Attributes
    champion_mastery_points: int = 0
    cs_per_minute: float = 7.5
    kill_participation_pct: float = 50.0
    vision_score_per_minute: float = 1.0
    first_blood_participation_pct: float = 15.0
    kills_at_15: float = 1.5
    deaths_at_15: float = 1.0

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
    """
    Calculates tactical tags, streaks, and threat evaluations matching Porofessor's Heuristics Engine.
    Implements all 9 core rules from the technical specification.
    """

    @staticmethod
    def compute_player_badges(player: PlayerScoutingData) -> List[Badge]:
        # If player already has curated badges (e.g. from mock/LeagueOfGraphs), return them
        if player.badges:
            return player.badges

        badges: List[Badge] = []

        # 1. OTP {Champion}: Mastery > 200k OR Winrate >= 60% with games >= 15
        recent_champ_count = sum(1 for m in player.recent_matches if m.champion.lower() == player.champion_name.lower())
        recent_total = len(player.recent_matches) or 1
        if (player.champion_mastery_points > 200_000 or player.champion_mastery_level >= 50 or (player.champion_winrate >= 60.0 and player.champion_games >= 15) or player.champion_games >= 25):
            badges.append(Badge(f"OTP {player.champion_name}", "good", "Champion Specialist / High game volume"))

        # 2. First Time / Casual: Mastery level < 4 OR games <= 1
        if player.champion_games <= 1 and (player.ranked_wins + player.ranked_losses) >= 10:
            badges.append(Badge("First Time", "warning", f"Only {player.champion_games} games recorded on {player.champion_name}"))
        elif player.champion_mastery_level < 4 or (player.champion_games < 3 and player.ranked_wins + player.ranked_losses >= 10):
            badges.append(Badge(f"{player.champion_name} casual", "danger", f"Low games on {player.champion_name}"))

        # 3. Good CSer: Average CS/min >= 8.0
        if player.cs_per_minute >= 8.0 and player.assigned_position.upper() in ["TOP", "MIDDLE", "BOTTOM"]:
            badges.append(Badge("Good CSer", "good", f"Averages {player.cs_per_minute:.1f} CS/Min"))

        # 4. Aggressive Laner: First Blood part >= 30% OR kills @ 15 >= 2.5
        if player.first_blood_participation_pct >= 30.0 or player.kills_at_15 >= 2.5:
            badges.append(Badge("Aggressive Laner", "good", "High early forward kill pressure in lane"))

        # 5. Vulnerable Laner: Deaths before 15 min >= 2.0
        if player.deaths_at_15 >= 2.0:
            badges.append(Badge("Vulnerable Laner", "danger", "High early death frequency in lane"))

        # 6. Good vision: Vision score/min >= 1.5 (or >= 2.5 for Support)
        is_support = player.assigned_position.upper() == "UTILITY"
        threshold = 2.5 if is_support else 1.5
        if player.vision_score_per_minute >= threshold:
            badges.append(Badge("Good vision", "good", "Places high quantity of control & stealth wards"))

        # 7. High Kill Participation: KP >= 65%
        if player.kill_participation_pct >= 65.0:
            badges.append(Badge("High Kill Participation", "good", f"Involved in {player.kill_participation_pct:.0f}% of team kills"))

        # 8. Waking up: Has not played a game in > 7 days or 0 games in past 12h
        if player.twelve_hr_games == 0:
            badges.append(Badge("Waking up", "warning", "First game of the day / Inactive recently"))

        # 9. Godlike {Champion}: Win rate on champ >= 70% with at least 15 games
        if player.champion_winrate >= 70.0 and player.champion_games >= 15:
            badges.append(Badge(f"Godlike {player.champion_name}", "good", f"{player.champion_winrate:.0f}% WR on {player.champion_name}"))

        # Millionaire Badge
        if player.champion_mastery_level >= 100 or player.champion_mastery_points >= 1_000_000:
            badges.append(Badge(f"Millionaire: {player.champion_name}", "good", "Over 1 Million Mastery Points"))

        # Win/Loss Streaks
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

