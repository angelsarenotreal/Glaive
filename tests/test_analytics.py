import unittest
from src.analytics import PlayerScoutingData, RecentMatchSummary, AnalyticsEngine
from src.mock_data import get_mock_match_data
from src.ui.overlay_window import sort_players_by_role

class TestAnalyticsEngine(unittest.TestCase):

    def test_mock_data_generation(self):
        players = get_mock_match_data()
        self.assertEqual(len(players), 10)
        blue_team = [p for p in players if p.team_id == 100]
        red_team = [p for p in players if p.team_id == 200]
        self.assertEqual(len(blue_team), 5)
        self.assertEqual(len(red_team), 5)

    def test_role_sorting_order(self):
        # Create un-ordered players (Support, Mid, Top, Jungle, ADC)
        p_sup = PlayerScoutingData(game_name="P1", tag_line="1", champion_name="Nami", assigned_position="UTILITY", team_id=100)
        p_mid = PlayerScoutingData(game_name="P2", tag_line="2", champion_name="Veigar", assigned_position="MIDDLE", team_id=100)
        p_top = PlayerScoutingData(game_name="P3", tag_line="3", champion_name="Urgot", assigned_position="TOP", team_id=100)
        p_jgl = PlayerScoutingData(game_name="P4", tag_line="4", champion_name="Viego", assigned_position="JUNGLE", team_id=100)
        p_adc = PlayerScoutingData(game_name="P5", tag_line="5", champion_name="Ziggs", assigned_position="BOTTOM", team_id=100)

        unordered = [p_sup, p_mid, p_top, p_jgl, p_adc]
        ordered = sort_players_by_role(unordered)

        expected_order = ["Urgot", "Viego", "Veigar", "Ziggs", "Nami"]
        actual_order = [p.champion_name for p in ordered]
        self.assertEqual(actual_order, expected_order)

    def test_otp_badge_computation(self):
        player = PlayerScoutingData(
            game_name="OtpYasuo",
            tag_line="EUW",
            champion_name="Yasuo",
            team_id=100,
            champion_games=30,
            champion_wins=21, # 70% winrate
            ranked_wins=50,
            ranked_losses=30
        )
        badges = AnalyticsEngine.compute_player_badges(player)
        badge_labels = [b.label for b in badges]
        self.assertTrue(any("OTP" in l for l in badge_labels))

    def test_win_streak_computation(self):
        player = PlayerScoutingData(
            game_name="Streaker",
            tag_line="EUW",
            champion_name="Aatrox",
            team_id=100,
            recent_matches=[
                RecentMatchSummary("Aatrox", 5, 1, 5, True),
                RecentMatchSummary("Aatrox", 6, 2, 8, True),
                RecentMatchSummary("Aatrox", 9, 3, 2, True),
                RecentMatchSummary("Aatrox", 8, 4, 1, True),
            ]
        )
        badges = AnalyticsEngine.compute_player_badges(player)
        badge_labels = [b.label for b in badges]
        self.assertTrue(any("4W Streak" in l for l in badge_labels))

    def test_first_time_champion_badge(self):
        player = PlayerScoutingData(
            game_name="NoobChamp",
            tag_line="EUW",
            champion_name="Briar",
            team_id=200,
            champion_games=0,
            champion_wins=0,
            ranked_wins=40,
            ranked_losses=40
        )
        badges = AnalyticsEngine.compute_player_badges(player)
        badge_labels = [b.label for b in badges]
        self.assertTrue(any("First Time" in l for l in badge_labels))

if __name__ == "__main__":
    unittest.main()
