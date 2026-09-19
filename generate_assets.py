import os
import shutil
import requests
from PIL import Image, ImageDraw

def generate_glaive_icon():
    os.makedirs("assets", exist_ok=True)
    
    size = (512, 512)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Rounded Octagon / Squircle
    bg_color = (13, 17, 23, 255)       # Obsidian slate
    border_color = (255, 255, 255, 60) # Subtle white border
    
    draw.rounded_rectangle(
        [(24, 24), (488, 488)],
        radius=110,
        fill=bg_color,
        outline=border_color,
        width=8
    )

    # 2. Inner subtle glow ring
    draw.rounded_rectangle(
        [(48, 48), (464, 464)],
        radius=88,
        fill=None,
        outline=(255, 255, 255, 20),
        width=3
    )

    # 3. Stylized Glaive Blade (Monochrome Pure White & Silver)
    center_x = 256
    
    blade_poly_left = [
        (center_x, 90),
        (center_x - 48, 230),
        (center_x - 22, 330),
        (center_x - 14, 390),
        (center_x, 390),
        (center_x, 90),
    ]
    draw.polygon(blade_poly_left, fill=(240, 245, 250, 255))

    blade_poly_right = [
        (center_x, 90),
        (center_x + 48, 230),
        (center_x + 22, 330),
        (center_x + 14, 390),
        (center_x, 390),
        (center_x, 90),
    ]
    draw.polygon(blade_poly_right, fill=(180, 195, 210, 255))

    guard_left = [
        (center_x - 14, 350),
        (center_x - 100, 320),
        (center_x - 90, 355),
        (center_x - 14, 375),
    ]
    draw.polygon(guard_left, fill=(240, 245, 250, 255))

    guard_right = [
        (center_x + 14, 350),
        (center_x + 100, 320),
        (center_x + 90, 355),
        (center_x + 14, 375),
    ]
    draw.polygon(guard_right, fill=(180, 195, 210, 255))

    draw.rounded_rectangle(
        [(center_x - 10, 385), (center_x + 10, 440)],
        radius=4,
        fill=(140, 155, 170, 255)
    )
    draw.ellipse(
        [(center_x - 18, 435), (center_x + 18, 465)],
        fill=(245, 250, 255, 255)
    )

    draw.line([(center_x, 110), (center_x, 380)], fill=(13, 17, 23, 200), width=4)

    png_path = "assets/icon.png"
    img.save(png_path, format="PNG")
    print(f"Generated {png_path}")

    ico_path = "assets/icon.ico"
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Generated {ico_path}")


def ensure_role_assets():
    roles_dir = os.path.join("assets", "roles")
    os.makedirs(roles_dir, exist_ok=True)
    
    role_urls = {
        "top.png": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-parties/global/default/icon-position-top.png",
        "jungle.png": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-parties/global/default/icon-position-jungle.png",
        "mid.png": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-parties/global/default/icon-position-middle.png",
        "bot.png": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-parties/global/default/icon-position-bottom.png",
        "support.png": "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-parties/global/default/icon-position-utility.png",
    }
    
    for filename, url in role_urls.items():
        dst_path = os.path.join(roles_dir, filename)
        if not os.path.exists(dst_path) or os.path.getsize(dst_path) < 100:
            try:
                resp = requests.get(url, timeout=6)
                if resp.status_code == 200:
                    with open(dst_path, "wb") as f:
                        f.write(resp.content)
                    print(f"Downloaded role asset: {filename}")
            except Exception as e:
                print(f"Failed downloading {filename}: {e}")

    # Aliases
    aliases = {
        "top.png": ["top.png"],
        "jungle.png": ["jungler.png", "jgl.png"],
        "mid.png": ["middle.png"],
        "bot.png": ["bottom.png", "ad_carry.png", "adc.png"],
        "support.png": ["utility.png", "sup.png"],
    }
    for src, dst_list in aliases.items():
        src_path = os.path.join(roles_dir, src)
        if os.path.exists(src_path):
            for dst in dst_list:
                if src != dst:
                    dst_path = os.path.join(roles_dir, dst)
                    if not os.path.exists(dst_path):
                        shutil.copyfile(src_path, dst_path)


def ensure_ranked_assets():
    ranked_dir = os.path.join("assets", "ranked")
    os.makedirs(ranked_dir, exist_ok=True)
    base = "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/"
    tiers = ["iron", "bronze", "silver", "gold", "platinum", "emerald", "diamond", "master", "grandmaster", "challenger", "unranked"]

    for tier in tiers:
        dst_path = os.path.join(ranked_dir, f"{tier}.png")
        if not os.path.exists(dst_path) or os.path.getsize(dst_path) < 5000:
            try:
                url = f"{base}{tier}.png"
                resp = requests.get(url, timeout=6)
                if resp.status_code == 200:
                    with open(dst_path, "wb") as f:
                        f.write(resp.content)
                    print(f"Downloaded official ranked crest: {tier}.png")
            except Exception as e:
                print(f"Failed downloading {tier}: {e}")


def ensure_mastery_assets():
    mastery_dir = os.path.join("assets", "mastery")
    os.makedirs(mastery_dir, exist_ok=True)
    base = "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/"

    # Mastery levels 1 to 10
    for lvl in range(1, 11):
        dst_path = os.path.join(mastery_dir, f"mastery_{lvl}.png")
        if not os.path.exists(dst_path) or os.path.getsize(dst_path) < 1000:
            try:
                url = f"{base}mastery-{lvl}.png"
                resp = requests.get(url, timeout=6)
                if resp.status_code == 200:
                    with open(dst_path, "wb") as f:
                        f.write(resp.content)
                    print(f"Downloaded official mastery crest: mastery_{lvl}.png")
            except Exception as e:
                print(f"Failed downloading mastery_{lvl}: {e}")

    # Mastery 0
    m0_path = os.path.join(mastery_dir, "mastery_0.png")
    if not os.path.exists(m0_path) or os.path.getsize(m0_path) < 1000:
        try:
            url0 = "https://raw.communitydragon.org/latest/game/assets/ux/mastery/legendarychampionmastery/masterycrest_level0.png"
            resp = requests.get(url0, timeout=6)
            if resp.status_code == 200:
                with open(m0_path, "wb") as f:
                    f.write(resp.content)
                print("Downloaded official mastery crest: mastery_0.png")
        except Exception as e:
            print(f"Failed downloading mastery_0: {e}")


if __name__ == "__main__":
    generate_glaive_icon()
    ensure_role_assets()
    ensure_ranked_assets()
    ensure_mastery_assets()
