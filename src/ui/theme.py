"""
Opaque, high-contrast dark theme styling and tokens for Glaive.
Matches Porofessor's exact color balance, crisp borders, and zero transparency distortion.
"""

MAIN_STYLESHEET = """
QWidget#GlaiveOverlay {
    background-color: transparent;
}

QDialog {
    background-color: #0c1017;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QFrame#MainContainer {
    background-color: #0c1017;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0px;
}

QFrame#HeaderFrame {
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    background-color: #111722;
    border-radius: 0px;
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
    font-weight: 600;
}

QFrame#PlayerCard {
    background-color: #151d27;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 0px;
    padding: 0px;
}

QFrame#PlayerCard:hover {
    background-color: #1c2634;
    border: 1px solid rgba(56, 189, 248, 0.5);
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
    background-color: #151d27;
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
    background-color: #151d27;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f8fafc;
    selection-background-color: rgba(56, 189, 248, 0.2);
}
"""
