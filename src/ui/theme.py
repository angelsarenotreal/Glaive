"""
Monochrome glassmorphic theme styling and tokens for Glaive.
Minimal, clean, distraction-free aesthetic.
"""

COLORS = {
    "bg_window": "rgba(10, 12, 16, 0.95)",
    "bg_card": "rgba(18, 22, 28, 0.92)",
    "bg_card_hover": "rgba(28, 34, 44, 0.96)",
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    "border_active": "rgba(255, 255, 255, 0.22)",
    
    # Text
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "text_highlight": "#ffffff",
    
    # Team Accents (Monochrome Silver/Slate theme)
    "blue_team_header": "#e2e8f0",
    "blue_team_sub": "#94a3b8",
    "red_team_header": "#f1f5f9",
    "red_team_sub": "#94a3b8",
    
    # Badges
    "badge_highlight_bg": "rgba(255, 255, 255, 0.14)",
    "badge_highlight_border": "rgba(255, 255, 255, 0.30)",
    "badge_highlight_text": "#ffffff",
    
    "badge_good_bg": "rgba(255, 255, 255, 0.08)",
    "badge_good_border": "rgba(255, 255, 255, 0.16)",
    "badge_good_text": "#e2e8f0",
    
    "badge_warning_bg": "rgba(234, 179, 8, 0.12)",
    "badge_warning_border": "rgba(234, 179, 8, 0.30)",
    "badge_warning_text": "#fef08a",
    
    "badge_danger_bg": "rgba(244, 63, 94, 0.12)",
    "badge_danger_border": "rgba(244, 63, 94, 0.30)",
    "badge_danger_text": "#fecdd3",
    
    "badge_neutral_bg": "rgba(255, 255, 255, 0.04)",
    "badge_neutral_border": "rgba(255, 255, 255, 0.08)",
    "badge_neutral_text": "#94a3b8",
}

MAIN_STYLESHEET = """
QWidget#GlaiveOverlay {
    background-color: transparent;
}

QFrame#MainContainer {
    background-color: rgba(10, 12, 16, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
}

QFrame#HeaderFrame {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(15, 18, 24, 0.6);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

QLabel#AppTitle {
    color: #ffffff;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 2px;
}

QLabel#StatusLabel {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 500;
}

QLabel#TeamHeader {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QLabel#TeamSubtext {
    font-size: 11px;
    color: #64748b;
    font-weight: 500;
}

QFrame#PlayerCard {
    background-color: rgba(18, 22, 28, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
    padding: 6px;
}

QFrame#PlayerCard:hover {
    background-color: rgba(26, 32, 42, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QLabel#PlayerName {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 600;
}

QLabel#PlayerTag {
    color: #64748b;
    font-size: 10px;
    font-weight: 500;
}

QLabel#ChampionName {
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
}

QLabel#RankText {
    color: #e2e8f0;
    font-size: 11px;
    font-weight: 600;
}

QLabel#StatValue {
    color: #f8fafc;
    font-size: 11px;
    font-weight: 600;
}

QLabel#StatLabel {
    color: #64748b;
    font-size: 10px;
    font-weight: 500;
}

/* Badges */
QLabel.BadgeHighlight {
    background-color: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.28);
    color: #ffffff;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.BadgeGood {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #e2e8f0;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.BadgeWarning {
    background-color: rgba(234, 179, 8, 0.12);
    border: 1px solid rgba(234, 179, 8, 0.3);
    color: #fef08a;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.BadgeDanger {
    background-color: rgba(244, 63, 94, 0.12);
    border: 1px solid rgba(244, 63, 94, 0.3);
    color: #fecdd3;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.BadgeNeutral {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 500;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f8fafc;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.24);
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.18);
}

QPushButton#IconButton {
    background-color: transparent;
    border: none;
    color: #94a3b8;
    padding: 4px;
    border-radius: 4px;
}

QPushButton#IconButton:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}

/* Inputs & Form */
QLineEdit, QComboBox {
    background-color: rgba(15, 18, 24, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 6px;
    color: #f8fafc;
    padding: 6px 10px;
    font-size: 11px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid rgba(255, 255, 255, 0.35);
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #12161c;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #f8fafc;
    selection-background-color: rgba(255, 255, 255, 0.12);
}
"""
