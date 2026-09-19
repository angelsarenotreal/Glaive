import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import AppConfig, PLATFORM_TO_REGION
from src.analytics import PlayerScoutingData, RecentMatchSummary, AnalyticsEngine
from src.leagueofgraphs import LeagueOfGraphsClient
from src.lcu_client import LCUClient


class RiotApiClient:
    """High-performance, rate-aware client for official Riot Games Web APIs & LeagueOfGraphs."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.session = requests.Session()
        self.log_client = LeagueOfGraphsClient()
        self.session.headers.update({
            "User-Agent": "GlaiveOverlay/1.0",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        # In-memory caches to guarantee zero duplicate network calls
        self._puuid_cache: Dict[str, str] = {}
        self._league_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._mastery_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._match_details_cache: Dict[str, Dict[str, Any]] = {}
        self._champ_name_to_id: Dict[str, int] = {}

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-Riot-Token": self.config.riot_api_key.strip()
        }

    def _get_regional_route(self, platform: str) -> str:
        return PLATFORM_TO_REGION.get(platform.lower(), "europe")

    def resolve_puuid(self, game_name: str, tag_line: str, platform: str) -> Optional[str]:
        """Resolves Riot ID (gameName#tagLine) to PUUID via ACCOUNT-V1."""
        cache_key = f"{game_name.lower()}#{tag_line.lower()}"
        if cache_key in self._puuid_cache:
            return self._puuid_cache[cache_key]

        if not self.config.riot_api_key:
            return None

        region = self._get_regional_route(platform)
        url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"

        try:
            resp = self.session.get(url, headers=self._get_headers(), timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                puuid = data.get("puuid")
                if puuid:
                    self._puuid_cache[cache_key] = puuid
                    return puuid
            elif resp.status_code == 403:
                print("[RiotAPI] API Key invalid or expired (403 Forbidden).")
            elif resp.status_code == 429:
                print("[RiotAPI] Rate limited (429).")
        except Exception as e:
            print(f"[RiotAPI] Error resolving PUUID for {game_name}#{tag_line}: {e}")

        return None

    def fetch_ranked_stats(self, puuid: str, platform: str) -> Tuple[str, str, int, int, int]:
        """Fetches Solo/Duo rank, tier, LP, wins, losses via LEAGUE-V4."""
        now = time.time()
        if puuid in self._league_cache:
            cached_time, entries = self._league_cache[puuid]
            if now - cached_time < 900:  # 15 minutes TTL
                return self._parse_league_entries(entries)

        if not self.config.riot_api_key:
            return "UNRANKED", "", 0, 0, 0

        url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        try:
            resp = self.session.get(url, headers=self._get_headers(), timeout=4)
            if resp.status_code == 200:
                entries = resp.json()
                self._league_cache[puuid] = (now, entries)
                return self._parse_league_entries(entries)
        except Exception as e:
            print(f"[RiotAPI] Error fetching ranked stats: {e}")

        return "UNRANKED", "", 0, 0, 0

    def _parse_league_entries(self, entries: List[Dict[str, Any]]) -> Tuple[str, str, int, int, int]:
        for entry in entries:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                tier = entry.get("tier", "UNRANKED")
                rank = entry.get("rank", "")
                lp = entry.get("leaguePoints", 0)
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                return tier, rank, lp, wins, losses

        # Fallback to Flex if Solo is unranked
        for entry in entries:
            if entry.get("queueType") == "RANKED_FLEX_SR":
                tier = entry.get("tier", "UNRANKED")
                rank = entry.get("rank", "")
                lp = entry.get("leaguePoints", 0)
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                return tier, rank, lp, wins, losses

        return "UNRANKED", "", 0, 0, 0

    def _get_champion_id(self, champ_name: str) -> Optional[int]:
        if not self._champ_name_to_id:
            try:
                r = self.session.get("https://ddragon.leagueoflegends.com/cdn/14.20.1/data/en_US/champion.json", timeout=4)
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    for c_id_str, c_info in data.items():
                        self._champ_name_to_id[c_info.get("name", "").lower()] = int(c_info.get("key", 0))
                        self._champ_name_to_id[c_id_str.lower()] = int(c_info.get("key", 0))
            except Exception:
                pass
        
        clean = champ_name.lower().replace(" ", "").replace("'", "").replace(".", "")
        for k, v in self._champ_name_to_id.items():
            if k.replace(" ", "").replace("'", "").replace(".", "") == clean:
                return v
        return None

    def _find_mastery_for_champion(self, entries: List[Dict[str, Any]], champion_name: str) -> Tuple[int, int]:
        c_id = self._get_champion_id(champion_name)
        if c_id:
            for e in entries:
                if e.get("championId") == c_id:
                    return e.get("championLevel", 1), e.get("championPoints", 0)
        return 1, 0

    def fetch_champion_mastery(self, puuid: str, platform: str, champion_name: str) -> Tuple[int, int]:
        """Fetches champion mastery level and total points via CHAMPION-MASTERY-V4."""
        now = time.time()
        if puuid in self._mastery_cache:
            cached_time, entries = self._mastery_cache[puuid]
            if now - cached_time < 900:
                return self._find_mastery_for_champion(entries, champion_name)

        if not self.config.riot_api_key:
            return 1, 0

        url = f"https://{platform}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        try:
            resp = self.session.get(url, headers=self._get_headers(), timeout=4)
            if resp.status_code == 200:
                entries = resp.json()
                self._mastery_cache[puuid] = (now, entries)
                return self._find_mastery_for_champion(entries, champion_name)
        except Exception as e:
            print(f"[RiotAPI] Error fetching champion mastery: {e}")

        return 1, 0

    def fetch_recent_matches(
        self, puuid: str, platform: str, champion_name: str, count: int = 5
    ) -> Tuple[List[RecentMatchSummary], int, int, float, float, float]:
        """Fetches recent match IDs and calculates champion winrate and recent KDA."""
        if not self.config.riot_api_key:
            return [], 0, 0, 0.0, 0.0, 0.0

        region = self._get_regional_route(platform)
        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        
        match_ids: List[str] = []
        try:
            resp = self.session.get(url, headers=self._get_headers(), timeout=4)
            if resp.status_code == 200:
                match_ids = resp.json()
        except Exception as e:
            print(f"[RiotAPI] Error fetching match IDs: {e}")
            return [], 0, 0, 0.0, 0.0, 0.0

        recent_summaries: List[RecentMatchSummary] = []
        champ_games = 0
        champ_wins = 0
        total_k, total_d, total_a = 0, 0, 0

        # Fetch match details (cached per matchId)
        for match_id in match_ids:
            match_data = self._get_match_detail(match_id, region)
            if not match_data:
                continue

            info = match_data.get("info", {})
            participants = info.get("participants", [])
            for p in participants:
                if p.get("puuid") == puuid:
                    c_name = p.get("championName", "")
                    k = p.get("kills", 0)
                    d = p.get("deaths", 0)
                    a = p.get("assists", 0)
                    win = p.get("win", False)

                    total_k += k
                    total_d += d
                    total_a += a

                    if c_name.lower() == champion_name.lower():
                        champ_games += 1
                        if win:
                            champ_wins += 1

                    recent_summaries.append(RecentMatchSummary(c_name, k, d, a, win))
                    break

        num_matches = max(len(recent_summaries), 1)
        avg_k = total_k / num_matches
        avg_d = total_d / num_matches
        avg_a = total_a / num_matches

        return recent_summaries, champ_games, champ_wins, avg_k, avg_d, avg_a

    def _get_match_detail(self, match_id: str, region: str) -> Optional[Dict[str, Any]]:
        if match_id in self._match_details_cache:
            return self._match_details_cache[match_id]

        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        try:
            resp = self.session.get(url, headers=self._get_headers(), timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                self._match_details_cache[match_id] = data
                return data
        except Exception as e:
            print(f"[RiotAPI] Error fetching match {match_id}: {e}")
        return None

    def scout_single_player(self, raw_player: Dict[str, Any], platform: str) -> PlayerScoutingData:
        """Enriches a single player from local liveclientdata with Riot Web API stats."""
        raw_name = raw_player.get("summonerName", "") or raw_player.get("riotId", "")
        # In current League clients, riotId is often 'GameName#TAG' or in summonerName
        if "#" in raw_name:
            game_name, tag_line = raw_name.split("#", 1)
        elif raw_player.get("rawRiotId"):
            parts = raw_player["rawRiotId"].split("#", 1)
            game_name = parts[0]
            tag_line = parts[1] if len(parts) > 1 else ""
        else:
            game_name = raw_name
            tag_line = ""

        champ_name = raw_player.get("championName", "Unknown")
        team_str = raw_player.get("team", "ORDER")
        team_id = 100 if team_str == "ORDER" else 200
        assigned_pos = raw_player.get("position", "")

        player = PlayerScoutingData(
            game_name=game_name,
            tag_line=tag_line,
            champion_name=champ_name,
            team_id=team_id,
            assigned_position=assigned_pos,
            level=raw_player.get("level", 1),
        )

        # 1. Fetch LeagueOfGraphs / Porofessor Insights
        log_data = self.log_client.fetch_player_insights(platform, game_name, tag_line, champ_name)
        if log_data.get("server_rank"):
            player.server_rank = log_data["server_rank"]
        if log_data.get("champion_server_rank"):
            player.champion_server_rank = log_data["champion_server_rank"]
        if log_data.get("badges"):
            player.badges.extend(log_data["badges"])

        if not self.config.riot_api_key or not tag_line:
            player.badges = AnalyticsEngine.compute_player_badges(player)
            return player

        # 2. Resolve PUUID via Riot API
        puuid = self.resolve_puuid(game_name, tag_line, platform)
        if not puuid:
            player.badges = AnalyticsEngine.compute_player_badges(player)
            return player

        # 3. Get Rank & LP
        tier, rank, lp, wins, losses = self.fetch_ranked_stats(puuid, platform)
        player.tier = tier
        player.rank = rank
        player.league_points = lp
        player.ranked_wins = wins
        player.ranked_losses = losses

        # 4. Get Recent Match History & Champ Stats
        recent, c_games, c_wins, avg_k, avg_d, avg_a = self.fetch_recent_matches(
            puuid, platform, champ_name, count=5
        )
        player.recent_matches = recent
        player.champion_games = c_games
        player.champion_wins = c_wins
        if avg_k and avg_d and avg_a:
            player.champion_kills_str = avg_k
            player.champion_deaths_str = avg_d
            player.champion_assists_str = avg_a

        # 5. Get Official Champion Mastery (Level & Points)
        m_level, m_points = self.fetch_champion_mastery(puuid, platform, champ_name)
        if m_level > 0:
            player.champion_mastery_level = m_level
        if m_points > 0:
            player.champion_mastery_points = m_points

        # 6. Compute tactical badges
        player.badges = AnalyticsEngine.compute_player_badges(player)
        return player

    def scout_all_players(self, raw_players: List[Dict[str, Any]], platform: str) -> List[PlayerScoutingData]:
        """Parallel scouts all 10 players using local LCU client or Riot Web API."""
        # 1. Try Local LCU Client first (Fastest, 0 API key required, 100% accurate)
        try:
            lcu = LCUClient()
            if lcu.is_available():
                scouted = lcu.scout_all_via_lcu(raw_players)
                if scouted and len(scouted) > 0:
                    return scouted
        except Exception as e:
            print(f"[RiotAPI] LCU scouting fallback: {e}")

        # 2. Fallback to Web API / heuristics
        results: List[PlayerScoutingData] = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_player = {
                executor.submit(self.scout_single_player, p, platform): p
                for p in raw_players
            }
            for future in as_completed(future_to_player):
                try:
                    data = future.result()
                    results.append(data)
                except Exception as e:
                    print(f"[RiotAPI] Error in parallel scout: {e}")

        # Sort results: Team 100 (Blue) first, then Team 200 (Red)
        results.sort(key=lambda p: (p.team_id, p.game_name))
        return results
