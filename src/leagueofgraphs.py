import re
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from src.analytics import PlayerScoutingData, Badge


class LeagueOfGraphsClient:
    """
    LeagueOfGraphs / Porofessor Data Extractor:
    - Queries public profile and ladder rank records from LeagueOfGraphs.
    - Extracts champion rankings (e.g. '#80 Urgot EUW'), server rank ('#4,608'), KDA, and tactical badges.
    """

    BASE_URL = "https://www.leagueofgraphs.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        })

    def _format_summoner_url(self, region: str, game_name: str, tag_line: str) -> str:
        # LeagueOfGraphs uses region codes like 'euw', 'na', 'kr', etc.
        reg = re.sub(r"\d+", "", region.lower())
        encoded_name = quote(game_name)
        encoded_tag = quote(tag_line) if tag_line else ""
        if encoded_tag:
            return f"{self.BASE_URL}/summoner/{reg}/{encoded_name}-{encoded_tag}"
        return f"{self.BASE_URL}/summoner/{reg}/{encoded_name}"

    def fetch_player_insights(self, region: str, game_name: str, tag_line: str, champion_name: str = "") -> Dict[str, Any]:
        """
        Attempts to fetch public rank, champion leaderboard standing, and playstyle tags from LeagueOfGraphs.
        Returns a dict of enriched fields or empty dict on failure/block.
        """
        url = self._format_summoner_url(region, game_name, tag_line)
        insights: Dict[str, Any] = {
            "server_rank": "",
            "champion_server_rank": "",
            "badges": [],
            "main_role": "",
            "kda_kills": "",
            "kda_deaths": "",
            "kda_assists": "",
        }

        try:
            resp = self.session.get(url, timeout=4)
            if resp.status_code == 200:
                html = resp.text

                # 1. Server Rank extraction (e.g., "Rank: <b>4,608</b>" or "League of Graphs Rank: 4,608")
                srv_match = re.search(r'data-ladder-rank=["\'](\d+)["\']', html)
                if not srv_match:
                    srv_match = re.search(r'Rank\s*:\s*<b>#?([\d,]+)</b>', html, re.IGNORECASE)
                if srv_match:
                    insights["server_rank"] = f"Rank: #{srv_match.group(1).replace('#', '')}"

                # 2. Champion Ladder Rank (e.g. '#80 Urgot')
                if champion_name:
                    c_pattern = rf'{re.escape(champion_name)}.*?#(?:<[^>]+>)?(\d+)'
                    c_match = re.search(c_pattern, html, re.IGNORECASE | re.DOTALL)
                    if c_match:
                        insights["champion_server_rank"] = f"Rank: #{c_match.group(1)}"

                # 3. Badges / Tags (extract Porofessor-style tag chips)
                tag_matches = re.findall(r'<div class=["\']tag(?:-[^"\']+)?["\'][^>]*>(.*?)</div>', html, re.IGNORECASE)
                for t in tag_matches:
                    clean_tag = re.sub(r'<[^>]+>', '', t).strip()
                    if clean_tag and len(clean_tag) < 30:
                        cat = "good"
                        if any(w in clean_tag.lower() for w in ["casual", "vulnerable", "death", "feed"]):
                            cat = "danger"
                        elif any(w in clean_tag.lower() for w in ["waking", "invader", "roam", "first"]):
                            cat = "warning"
                        elif "pro" in clean_tag.lower():
                            cat = "pro"
                        insights["badges"].append(Badge(label=clean_tag, category=cat))

        except Exception:
            pass

        return insights
