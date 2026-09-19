import http.server
import ssl
import json
import time
import os
from pathlib import Path
from src.mock_data import get_mock_match_data

# Generate sample raw liveclient playerlist data
mock_players = get_mock_match_data()
raw_playerlist = []
for p in mock_players:
    raw_playerlist.append({
        "summonerName": f"{p.game_name}#{p.tag_line}",
        "rawRiotId": f"{p.game_name}#{p.tag_line}",
        "championName": p.champion_name,
        "team": "ORDER" if p.team_id == 100 else "CHAOS",
        "position": p.assigned_position,
        "level": p.level,
        "scores": {"kills": 0, "deaths": 0, "assists": 0, "creepScore": 0, "wardScore": 0.0},
        "summonerSpells": {
            "summonerSpellOne": {"displayName": p.spell1_name},
            "summonerSpellTwo": {"displayName": p.spell2_name}
        }
    })

class LiveClientHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if "/liveclientdata/playerlist" in self.path or "/liveclientdata/allgamedata" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(raw_playerlist).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silent

def run_simulation(duration_seconds: int = 45):
    print("=" * 60)
    print("🎮 GLAIVE LOCAL MATCH SIMULATOR")
    print("=" * 60)
    print(f"[Simulator] Emulating League of Legends Live Client on https://127.0.0.1:2999...")
    print(f"[Simulator] Active players: {len(raw_playerlist)} (5 Blue / 5 Red)")
    print(f"[Simulator] Running for {duration_seconds} seconds to trigger Glaive detection...")
    print("=" * 60)

    # Create self-signed dummy cert if needed
    cert_dir = Path(__file__).resolve().parent / "temp_cert"
    cert_dir.mkdir(exist_ok=True)
    cert_file = cert_dir / "server.pem"
    
    # Generate quick self-signed cert using cryptography or openssl if available, else plain HTTP
    use_ssl = False
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=1)
        ).add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]),
            critical=False,
        ).sign(key, hashes.SHA256())

        with open(cert_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        use_ssl = True
    except Exception:
        pass

    server_address = ("127.0.0.1", 2999)
    try:
        httpd = http.server.HTTPServer(server_address, LiveClientHandler)
        if use_ssl and cert_file.exists():
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=str(cert_file))
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

        print("[Simulator] Server listening! Watch Glaive pop up the top-center HUD notification banner...")
        
        # Run server in loop
        end_time = time.time() + duration_seconds
        httpd.timeout = 1.0
        while time.time() < end_time:
            httpd.handle_request()

        print("[Simulator] Simulation finished. Game ended.")
    except Exception as e:
        print(f"[Simulator] Error starting server on port 2999: {e}")
        print("(Note: If a real League game is already running, port 2999 will be in use by Riot).")

if __name__ == "__main__":
    import ipaddress
    run_simulation(45)
