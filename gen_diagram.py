import os
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Configuration
W, H = 1600, 1200
BG_COLOR = (248, 250, 252)  # Slate 50
ACCENT_BLUE = (37, 99, 235)  # Blue 600
ACCENT_GREEN = (16, 185, 129)  # Green 500
ACCENT_RED = (220, 38, 38)    # Red 600
ACCENT_PURPLE = (139, 92, 246) # Purple 500
ACCENT_ORANGE = (234, 88, 12)  # Orange 600
ACCENT_SLATE = (71, 85, 105)  # Slate 600

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
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def draw_shadow(box, radius=20, offset=(6, 6), color=(0, 0, 0, 35)):
    x1, y1, x2, y2 = box
    shadow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_box = (x1 + offset[0], y1 + offset[1], x2 + offset[0], y2 + offset[1])
    shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=color)
    return shadow_img.filter(ImageFilter.GaussianBlur(12))

def get_bezier_point(p0, p1, p2, t):
    # Quadratic Bezier
    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
    return (x, y)

def draw_curved_arrow(draw, p0, p1, p2, color, width=4, dashed=False):
    points = [get_bezier_point(p0, p1, p2, t/50) for t in range(51)]
    if dashed:
        for i in range(0, len(points)-1, 2):
            draw.line([points[i], points[min(i+1, len(points)-1)]], fill=color, width=width)
    else:
        draw.line(points, fill=color, width=width)
    
    # Arrow head at end
    end = points[-1]
    prev = points[-2]
    angle = math.atan2(end[1]-prev[1], end[0]-prev[0])
    head_len = 18
    head_angle = math.pi / 6
    pa = (end[0] - head_len * math.cos(angle - head_angle), end[1] - head_len * math.sin(angle - head_angle))
    pb = (end[0] - head_len * math.cos(angle + head_angle), end[1] - head_len * math.sin(angle + head_angle))
    draw.polygon([end, pa, pb], fill=color)

def create_diagram():
    img = Image.new('RGB', (W, H), BG_COLOR)
    # Layer for drawing components
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 52)
        font_h1 = ImageFont.truetype("arialbd.ttf", 28)
        font_h2 = ImageFont.truetype("arialbd.ttf", 22)
        font_reg = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = font_h1 = font_h2 = font_reg = font_small = ImageFont.load_default()

    # Download Logos
    logo_imgs = {name: download_image(url) for name, url in LOGOS.items()}

    # Coordinates
    user_box = (200, 120, 550, 240)
    hc_box = (1050, 120, 1400, 240)
    auto_box = (150, 350, 1450, 780)
    nr_box = (200, 480, 500, 620)
    mq_box = (1100, 480, 1400, 620)
    py_box = (550, 650, 1050, 750)
    dell_box = (150, 900, 750, 1120)
    hp_box = (850, 900, 1450, 1120)

    # Shadow layer
    shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for box, r in [(user_box, 20), (hc_box, 20), (auto_box, 40), (nr_box, 20), (mq_box, 20), (py_box, 20), (dell_box, 30), (hp_box, 30)]:
        shadow_layer = Image.alpha_composite(shadow_layer, draw_shadow(box, radius=r))
    img.paste(shadow_layer, (0, 0), shadow_layer)

    # Draw Components
    # User
    draw.rounded_rectangle(user_box, radius=20, fill="white", outline=ACCENT_BLUE, width=3)
    draw.text((375, 160), "END USER", fill=(15, 23, 42), font=font_h1, anchor="mm")
    draw.text((375, 200), "Web Dashboard Access", fill=ACCENT_SLATE, font=font_reg, anchor="mm")

    # Healthchecks.io
    draw.rounded_rectangle(hc_box, radius=20, fill="white", outline=ACCENT_GREEN, width=3)
    if logo_imgs['healthchecks']:
        logo = logo_imgs['healthchecks'].copy()
        logo.thumbnail((180, 60))
        img.paste(logo, (1135, 140), logo)
    draw.text((1225, 210), "Healthchecks.io", fill=ACCENT_GREEN, font=font_h2, anchor="mm")

    # Automation Server
    draw.rounded_rectangle(auto_box, radius=40, fill=(241, 245, 249), outline=ACCENT_BLUE, width=4)
    draw.text((800, 400), "AUTOMATION SERVER (Ubuntu VM)", fill=(30, 58, 138), font=font_h1, anchor="mm")
    if logo_imgs['ubuntu']:
        logo = logo_imgs['ubuntu'].copy()
        logo.thumbnail((60, 60))
        img.paste(logo, (180, 370), logo)

    # Node-RED
    draw.rounded_rectangle(nr_box, radius=20, fill=(254, 226, 226), outline=ACCENT_RED, width=2)
    draw.text((350, 580), "Node-RED", fill=(153, 27, 27), font=font_h2, anchor="mm")
    if logo_imgs['nodered']:
        logo = logo_imgs['nodered'].copy()
        logo.thumbnail((70, 70))
        img.paste(logo, (315, 495), logo)

    # Mosquitto
    draw.rounded_rectangle(mq_box, radius=20, fill=(220, 252, 231), outline=ACCENT_GREEN, width=2)
    draw.text((1250, 580), "Mosquitto MQTT", fill=(21, 128, 61), font=font_h2, anchor="mm")
    if logo_imgs['mosquitto']:
        logo = logo_imgs['mosquitto'].copy()
        logo.thumbnail((220, 70))
        img.paste(logo, (1140, 495), logo)

    # Python Scripts
    draw.rounded_rectangle(py_box, radius=20, fill=(237, 233, 254), outline=ACCENT_PURPLE, width=2)
    draw.text((800, 700), "Python Management Scripts", fill=(88, 28, 135), font=font_h2, anchor="mm")
    if logo_imgs['python']:
        logo = logo_imgs['python'].copy()
        logo.thumbnail((60, 60))
        img.paste(logo, (570, 670), logo)

    # Infrastructure
    # Dell
    draw.rounded_rectangle(dell_box, radius=30, fill=(240, 253, 244), outline=ACCENT_GREEN, width=3)
    draw.text((450, 940), "Dell PowerEdge T310", fill=(6, 78, 59), font=font_h1, anchor="mm")
    if logo_imgs['dell']:
        logo = logo_imgs['dell'].copy()
        logo.thumbnail((100, 100))
        img.paste(logo, (180, 950), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((140, 50))
        img.paste(logo, (380, 1040), logo)

    # HP
    draw.rounded_rectangle(hp_box, radius=30, fill=(255, 250, 245), outline=ACCENT_ORANGE, width=3)
    draw.text((1150, 940), "HP ProLiant DL360p", fill=(124, 45, 18), font=font_h1, anchor="mm")
    if logo_imgs['hp']:
        logo = logo_imgs['hp'].copy()
        logo.thumbnail((100, 100))
        img.paste(logo, (880, 950), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((140, 50))
        img.paste(logo, (1080, 1040), logo)

    # FLOWS - CURVED ARROWS
    # 1. User -> Node-RED
    draw_curved_arrow(draw, (375, 240), (375, 350), (350, 480), ACCENT_BLUE)
    draw.text((390, 300), "Web/HTTP", fill=ACCENT_BLUE, font=font_reg)

    # 2. Node-RED <-> Mosquitto
    draw_curved_arrow(draw, (500, 520), (800, 450), (1100, 520), ACCENT_BLUE)
    draw_curved_arrow(draw, (1100, 580), (800, 650), (500, 580), ACCENT_BLUE)
    draw.text((800, 550), "MQTT Commands & Status", fill=ACCENT_BLUE, font=font_reg, anchor="mm")

    # 3. Mosquitto <-> Scripts
    draw_curved_arrow(draw, (1250, 620), (1250, 700), (1050, 700), ACCENT_PURPLE)
    draw.text((1150, 720), "Pub/Sub", fill=ACCENT_PURPLE, font=font_reg)

    # 4. Scripts -> Dell
    draw_curved_arrow(draw, (650, 750), (650, 850), (450, 900), ACCENT_PURPLE)
    # 5. Scripts -> HP
    draw_curved_arrow(draw, (950, 750), (950, 850), (1150, 900), ACCENT_PURPLE)
    draw.text((800, 840), "WoL / IPMI / iLO / Proxmox API", fill=ACCENT_PURPLE, font=font_reg, anchor="mm")

    # 6. Servers -> Healthchecks (Dashed)
    draw_curved_arrow(draw, (750, 950), (1000, 950), (1225, 240), ACCENT_GREEN, dashed=True)
    draw_curved_arrow(draw, (1450, 950), (1550, 950), (1400, 200), ACCENT_GREEN, dashed=True)
    draw.text((1400, 600), "HTTPS Pings", fill=ACCENT_GREEN, font=font_reg, anchor="mm")

    # 7. Scripts -> Healthchecks (Dashed)
    draw_curved_arrow(draw, (800, 650), (800, 550), (1050, 200), ACCENT_BLUE, dashed=True)
    draw.text((850, 300), "API v3 Pull", fill=ACCENT_BLUE, font=font_reg)

    # Save
    draw.text((W//2, 50), "System Architecture & Interaction Flow", fill=(30, 41, 59), font=font_title, anchor="mm")
    img.save("docs/architecture_diagram.png", "PNG")
    print("Successfully updated docs/architecture_diagram.png with beautiful curved flows")

if __name__ == "__main__":
    create_diagram()
