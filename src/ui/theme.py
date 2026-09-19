"""
Pitch black theme styling and high-contrast tokens for Glaive.
Container: #000000 (Pure Pitch Black).
Player Cards: #0d1117 (Pitch Black with subtle lighter tint for contrast).
"""

MAIN_STYLESHEET = """
QWidget#GlaiveOverlay {
    background-color: transparent;
}

QDialog {
    background-color: #000000;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.18);
}

QFrame#MainContainer {
    background-color: #000000;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 0px;
}

QFrame#PlayerCard {
    background-color: #0d1117;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 0px;
    padding: 0px;
}

QFrame#PlayerCard:hover {
    background-color: #141922;
    border: 1px solid rgba(56, 189, 248, 0.45);
}

QLabel#PlayerName {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 700;
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
    color: #f1f5f9;
    font-size: 11px;
    font-weight: 700;
}

QLabel#StatValue {
    color: #f8fafc;
    font-size: 11px;
    font-weight: 600;
}

QLabel#StatLabel {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 500;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #f8fafc;
    border-radius: 0px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.35);
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.22);
}

QPushButton#IconButton {
    background-color: transparent;
    border: none;
    color: #94a3b8;
    padding: 4px;
    border-radius: 0px;
}

QPushButton#IconButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

/* Inputs & Form */
QLineEdit, QComboBox {
    background-color: #0d1117;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0px;
    color: #f8fafc;
    padding: 6px 10px;
    font-size: 11px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid rgba(56, 189, 248, 0.7);
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #0d1117;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f8fafc;
    selection-background-color: rgba(56, 189, 248, 0.2);
}
"""
