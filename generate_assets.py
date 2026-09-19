import os
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
    # Central Sword/Glaive Tip & Body
    center_x = 256
    
    # Blade Tip & Spine
    blade_poly_left = [
        (center_x, 90),     # Tip
        (center_x - 48, 230), # Left guard edge
        (center_x - 22, 330), # Left lower blade
        (center_x - 14, 390), # Left hilt
        (center_x, 390),      # Hilt center
        (center_x, 90),       # Tip
    ]
    draw.polygon(blade_poly_left, fill=(240, 245, 250, 255))

    blade_poly_right = [
        (center_x, 90),     # Tip
        (center_x + 48, 230), # Right guard edge
        (center_x + 22, 330), # Right lower blade
        (center_x + 14, 390), # Right hilt
        (center_x, 390),      # Hilt center
        (center_x, 90),       # Tip
    ]
    draw.polygon(blade_poly_right, fill=(180, 195, 210, 255))

    # Crossguard Wings
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

    # Handle & Pommel
    draw.rounded_rectangle(
        [(center_x - 10, 385), (center_x + 10, 440)],
        radius=4,
        fill=(140, 155, 170, 255)
    )
    draw.ellipse(
        [(center_x - 18, 435), (center_x + 18, 465)],
        fill=(245, 250, 255, 255)
    )

    # Center Blade Fuller Accent Line
    draw.line([(center_x, 110), (center_x, 380)], fill=(13, 17, 23, 200), width=4)

    # Save PNG
    png_path = "assets/icon.png"
    img.save(png_path, format="PNG")
    print(f"Generated {png_path}")

    # Save Multi-resolution ICO
    ico_path = "assets/icon.ico"
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Generated {ico_path}")

if __name__ == "__main__":
    generate_glaive_icon()
