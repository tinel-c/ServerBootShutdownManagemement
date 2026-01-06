import os
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Configuration
W, H = 1600, 1100
BG_COLOR = (252, 253, 254)  # Very light slate
ACCENT_BLUE = (37, 99, 235)   # Blue 600
ACCENT_GREEN = (16, 185, 129)  # Emerald 500
ACCENT_RED = (239, 68, 68)     # Red 500
ACCENT_PURPLE = (139, 92, 246) # Violet 500
ACCENT_ORANGE = (245, 158, 11) # Amber 500
TEXT_DARK = (15, 23, 42)       # Slate 900
TEXT_MUTED = (100, 116, 139)   # Slate 500

# Logo URLs
LOGOS = {
    'dell': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dell_logo_2016.svg/200px-Dell_logo_2016.svg.png',
    'hp': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/HP_logo_2012.svg/200px-HP_logo_2012.svg.png',
    'nodered': 'https://nodered.org/favicon.ico',
    'python': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/200px-Python-logo-notext.svg.png',
    'mosquitto': 'https://mosquitto.org/images/mosquitto-text-side.png',
    'healthchecks': 'https://healthchecks.io/static/img/logo.png',
    'proxmox': 'https://www.proxmox.com/images/proxmox/proxmox-logo-color-stacked.png',
    'ubuntu': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Logo-ubuntu_cof-orange-hex.svg/200px-Logo-ubuntu_cof-orange-hex.svg.png'
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def download_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def draw_shadow(draw, box, radius=25, offset=(4, 4), color=(0, 0, 0, 30)):
    x1, y1, x2, y2 = box
    shadow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_box = (x1 + offset[0], y1 + offset[1], x2 + offset[0], y2 + offset[1])
    shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=color)
    return shadow_img.filter(ImageFilter.GaussianBlur(8))

def draw_bezier(draw, p0, p1, p2, color, width=3, dashed=False, head=True):
    """Draws a quadratic bezier curve."""
    points = []
    for i in range(51):
        t = i / 50.0
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    
    if dashed:
        for i in range(0, len(points)-1, 2):
            draw.line([points[i], points[i+1]], fill=color, width=width)
    else:
        draw.line(points, fill=color, width=width)
    
    if head:
        # Draw arrow head at end
        angle = math.atan2(points[-1][1] - points[-2][1], points[-1][0] - points[-2][0])
        head_len = 15
        head_angle = math.pi / 6
        end = points[-1]
        hp1 = (end[0] - head_len * math.cos(angle - head_angle), end[1] - head_len * math.sin(angle - head_angle))
        hp2 = (end[0] - head_len * math.cos(angle + head_angle), end[1] - head_len * math.sin(angle + head_angle))
        draw.polygon([end, hp1, hp2], fill=color)

def create_diagram():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 48)
        font_h1 = ImageFont.truetype("arialbd.ttf", 28)
        font_h2 = ImageFont.truetype("arialbd.ttf", 22)
        font_reg = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = font_h1 = font_h2 = font_reg = font_small = ImageFont.load_default()

    # 1. Download Logos
    logo_imgs = {name: download_image(url) for name, url in LOGOS.items()}

    # 2. Define Positions
    user_box = (W//2 - 150, 120, W//2 + 150, 220)
    hc_box = (W - 350, 110, W - 100, 240)
    auto_box = (150, 350, 1450, 750)
    dell_box = (150, 850, 750, 1020)
    hp_box = (850, 850, 1450, 1020)

    # 3. Draw Shadows
    shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for box in [user_box, hc_box, auto_box, dell_box, hp_box]:
        shadow_layer = Image.alpha_composite(shadow_layer, draw_shadow(draw, box))
    img.paste(shadow_layer, (0, 0), shadow_layer)

    # 4. Draw Components
    # Title
    draw.text((W//2, 60), "System Architecture & Interaction Flow", fill=TEXT_DARK, font=font_title, anchor="mm")

    # User
    draw.rounded_rectangle(user_box, radius=20, fill="white", outline=ACCENT_BLUE, width=3)
    draw.text((W//2, 170), "END USER", fill=TEXT_DARK, font=font_h1, anchor="mm")
    draw.text((W//2, 200), "Web Dashboard", fill=TEXT_MUTED, font=font_reg, anchor="mm")

    # Healthchecks.io
    draw.rounded_rectangle(hc_box, radius=20, fill="white", outline=ACCENT_BLUE, width=3)
    if logo_imgs['healthchecks']:
        logo = logo_imgs['healthchecks'].copy()
        logo.thumbnail((150, 60))
        img.paste(logo, (hc_box[0] + 50, hc_box[1] + 20), logo)
    draw.text((hc_box[0] + 125, hc_box[1] + 105), "Healthchecks.io", fill=ACCENT_BLUE, font=font_h2, anchor="mm")

    # Automation Server
    draw.rounded_rectangle(auto_box, radius=35, fill=(248, 250, 252), outline=ACCENT_BLUE, width=4)
    draw.text((W//2, 390), "AUTOMATION SERVER (Ubuntu VM)", fill=(30, 58, 138), font=font_h1, anchor="mm")
    if logo_imgs['ubuntu']:
        logo = logo_imgs['ubuntu'].copy()
        logo.thumbnail((60, 60))
        img.paste(logo, (180, 370), logo)

    # Inner Components
    # Node-RED
    nr_box = (220, 450, 520, 600)
    draw.rounded_rectangle(nr_box, radius=15, fill=(254, 242, 242), outline=ACCENT_RED, width=2)
    draw.text((370, 560), "Node-RED", fill="#991b1b", font=font_h2, anchor="mm")
    if logo_imgs['nodered']:
        logo = logo_imgs['nodered'].copy()
        logo.thumbnail((60, 60))
        img.paste(logo, (340, 470), logo)

    # Mosquitto
    mq_box = (1080, 450, 1380, 600)
    draw.rounded_rectangle(mq_box, radius=15, fill=(240, 253, 244), outline=ACCENT_GREEN, width=2)
    draw.text((1230, 560), "Mosquitto MQTT", fill="#065f46", font=font_h2, anchor="mm")
    if logo_imgs['mosquitto']:
        logo = logo_imgs['mosquitto'].copy()
        logo.thumbnail((180, 60))
        img.paste(logo, (1140, 470), logo)

    # Python Scripts
    py_box = (550, 630, 1050, 720)
    draw.rounded_rectangle(py_box, radius=15, fill=(245, 243, 255), outline=ACCENT_PURPLE, width=2)
    draw.text((800, 675), "Python Management Scripts", fill="#5b21b6", font=font_h2, anchor="mm")
    if logo_imgs['python']:
        logo = logo_imgs['python'].copy()
        logo.thumbnail((50, 50))
        img.paste(logo, (570, 650), logo)

    # Managed Servers
    # Dell
    draw.rounded_rectangle(dell_box, radius=25, fill=(240, 253, 244), outline=ACCENT_GREEN, width=3)
    draw.text((480, 890), "Dell PowerEdge T310", fill="#065f46", font=font_h1, anchor="mm")
    if logo_imgs['dell']:
        logo = logo_imgs['dell'].copy()
        logo.thumbnail((100, 100))
        img.paste(logo, (180, 870), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((120, 45))
        img.paste(logo, (420, 950), logo)

    # HP
    draw.rounded_rectangle(hp_box, radius=25, fill=(255, 251, 235), outline=ACCENT_ORANGE, width=3)
    draw.text((1180, 890), "HP ProLiant DL360p", fill="#92400e", font=font_h1, anchor="mm")
    if logo_imgs['hp']:
        logo = logo_imgs['hp'].copy()
        logo.thumbnail((100, 100))
        img.paste(logo, (880, 870), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((120, 45))
        img.paste(logo, (1120, 950), logo)

    # 5. Draw Refined Flows (Bezier)
    # User -> Node-RED (HTTP)
    draw_bezier(draw, (W//2, 220), (W//2, 300), (370, 450), color=ACCENT_BLUE)
    draw.text((W//2 + 20, 280), "HTTP Dashboard", fill=ACCENT_BLUE, font=font_reg)

    # Node-RED <-> Mosquitto (MQTT)
    draw_bezier(draw, (520, 500), (800, 500), (1080, 500), color=ACCENT_BLUE, head=True)
    draw_bezier(draw, (1080, 550), (800, 550), (520, 550), color=ACCENT_BLUE, head=True)
    draw.text((800, 525), "MQTT Commands & Status", fill=ACCENT_BLUE, font=font_reg, anchor="mm")

    # Scripts <-> Mosquitto
    draw_bezier(draw, (1230, 600), (1230, 675), (1050, 675), color=ACCENT_PURPLE)
    draw.text((1150, 650), "Pub/Sub", fill=ACCENT_PURPLE, font=font_small)

    # Control Flows (Purple)
    draw_bezier(draw, (650, 720), (650, 780), (450, 850), color=ACCENT_PURPLE)
    draw_bezier(draw, (950, 720), (950, 780), (1150, 850), color=ACCENT_PURPLE)
    draw.text((W//2, 780), "WoL / IPMI / iLO / Proxmox API", fill=ACCENT_PURPLE, font=font_reg, anchor="mm")

    # Telemetry (Green Dashed) - Curved along edges
    draw_bezier(draw, (150, 935), (50, 935), (50, 525), color=ACCENT_GREEN, dashed=True, head=False)
    draw_bezier(draw, (50, 525), (50, 525), (220, 525), color=ACCENT_GREEN, dashed=True, head=True)
    
    draw_bezier(draw, (1450, 935), (1550, 935), (1550, 525), color=ACCENT_GREEN, dashed=True, head=False)
    draw_bezier(draw, (1550, 525), (1550, 525), (1380, 525), color=ACCENT_GREEN, dashed=True, head=True)
    draw.text((100, 650), "MQTT Status", fill=ACCENT_GREEN, font=font_reg, anchor="mm")

    # Health Pings (Green Dashed)
    draw_bezier(draw, (600, 850), (800, 400), (hc_box[0], 175), color=ACCENT_GREEN, dashed=True)
    draw_bezier(draw, (1300, 850), (1500, 400), (hc_box[0] + 250, 175), color=ACCENT_GREEN, dashed=True)
    draw.text((1000, 300), "HTTPS Pings", fill=ACCENT_GREEN, font=font_reg)

    # Health API Pull (Blue Dashed)
    draw_bezier(draw, (hc_box[0], 200), (800, 200), (800, 630), color=ACCENT_BLUE, dashed=True)
    draw.text((950, 220), "API v3 Status Pull", fill=ACCENT_BLUE, font=font_reg)

    # Legend
    draw.text((50, H - 40), "Architecture v2.1 • Refined Flow Tracing • Modular Dashboard • Proxmox Graceful Shutdown", fill=TEXT_MUTED, font=font_small)

    img.save("docs/architecture_diagram.png", "PNG", optimize=True)
    print("Successfully created docs/architecture_diagram.png")

if __name__ == "__main__":
    create_diagram()

