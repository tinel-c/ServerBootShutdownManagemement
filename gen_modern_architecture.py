import os
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Configuration
W, H = 1800, 1200  # Increased size for more components
BG_COLOR = (248, 250, 252)  # Slate 50
ACCENT_BLUE = (59, 130, 246)   # Blue 500
ACCENT_GREEN = (16, 185, 129)  # Emerald 500
ACCENT_RED = (239, 68, 68)     # Red 500
ACCENT_PURPLE = (139, 92, 246) # Violet 500
ACCENT_ORANGE = (245, 158, 11) # Amber 500
ACCENT_CYAN = (6, 182, 212)    # Cyan 500
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
    'ubuntu': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Logo-ubuntu_cof-orange-hex.svg/200px-Logo-ubuntu_cof-orange-hex.svg.png',
    'windows': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Windows_logo_-_2021.svg/200px-Windows_logo_-_2021.svg.png'
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def download_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def draw_shadow(draw, box, radius=25, offset=(6, 6), color=(0, 0, 0, 20)):
    x1, y1, x2, y2 = box
    shadow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_box = (x1 + offset[0], y1 + offset[1], x2 + offset[0], y2 + offset[1])
    shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=color)
    return shadow_img.filter(ImageFilter.GaussianBlur(10))

def draw_bezier(draw, p0, p1, p2, color, width=3, dashed=False, head=True):
    """Draws a quadratic bezier curve."""
    points = []
    steps = 60
    for i in range(steps + 1):
        t = i / float(steps)
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    
    if dashed:
        for i in range(0, len(points)-1, 3):
            if i+2 < len(points):
                draw.line([points[i], points[i+2]], fill=color, width=width)
    else:
        draw.line(points, fill=color, width=width)
    
    if head:
        # Draw arrow head at end
        angle = math.atan2(points[-1][1] - points[-5][1], points[-1][0] - points[-5][0])
        head_len = 20
        head_angle = math.pi / 7
        end = points[-1]
        hp1 = (end[0] - head_len * math.cos(angle - head_angle), end[1] - head_len * math.sin(angle - head_angle))
        hp2 = (end[0] - head_len * math.cos(angle + head_angle), end[1] - head_len * math.sin(angle + head_angle))
        draw.polygon([end, hp1, hp2], fill=color)

def create_diagram():
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 48)
        font_h1 = ImageFont.truetype("arialbd.ttf", 32)
        font_h2 = ImageFont.truetype("arialbd.ttf", 24)
        font_reg = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except:
        font_title = font_h1 = font_h2 = font_reg = font_small = font_bold = ImageFont.load_default()

    # 1. Download Logos
    print("Downloading logos...")
    logo_imgs = {name: download_image(url) for name, url in LOGOS.items()}

    # 2. Define Layout Blocks
    # Top Row: External Services & User
    hc_box = (W - 400, 80, W - 100, 200)
    user_box = (400, 80, 700, 200)

    # Middle Row: Client PC (Left) -- Automation Server (Center/Right)
    client_box = (100, 350, 450, 750)
    auto_box = (550, 300, 1650, 800)

    # Bottom Row: Servers
    dell_box = (600, 900, 1050, 1100)
    hp_box = (1150, 900, 1600, 1100)

    # 3. Draw Shadows
    shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for box in [user_box, hc_box, client_box, auto_box, dell_box, hp_box]:
        shadow_layer = Image.alpha_composite(shadow_layer, draw_shadow(draw, box))
    img.paste(shadow_layer, (0, 0), shadow_layer)

    # 4. Draw Components
    
    # Title
    draw.text((80, 60), "Architecture v2.2", fill=TEXT_MUTED, font=font_h1, anchor="lm")
    draw.text((80, 110), "Decentralized Automation", fill=TEXT_DARK, font=font_title, anchor="lm")

    # User
    draw.rounded_rectangle(user_box, radius=20, fill="white", outline=ACCENT_BLUE, width=3)
    draw.text(((user_box[0]+user_box[2])//2, 140), "END USER", fill=TEXT_DARK, font=font_h2, anchor="mm")
    draw.text(((user_box[0]+user_box[2])//2, 170), "Web Dashboard / Mobile", fill=TEXT_MUTED, font=font_reg, anchor="mm")

    # Healthchecks.io
    draw.rounded_rectangle(hc_box, radius=20, fill="white", outline=ACCENT_GREEN, width=3)
    if logo_imgs['healthchecks']:
        logo = logo_imgs['healthchecks'].copy()
        logo.thumbnail((180, 70))
        img.paste(logo, (hc_box[0] + 30, hc_box[1] + 30), logo)
    draw.text((hc_box[0] + 200, hc_box[1] + 60), "External Monitoring", fill=ACCENT_GREEN, font=font_reg, anchor="mm")

    # Client PC
    draw.rounded_rectangle(client_box, radius=20, fill="#f0f9ff", outline=ACCENT_CYAN, width=3)
    draw.text(((client_box[0]+client_box[2])//2, 390), "CLIENT PC", fill=ACCENT_CYAN, font=font_h1, anchor="mm")
    if logo_imgs['windows']:
        logo = logo_imgs['windows'].copy()
        logo.thumbnail((50, 50))
        img.paste(logo, (client_box[0] + 30, 365), logo)
    
    # Client Inner: App
    app_box = (client_box[0]+30, 480, client_box[2]-30, 600)
    draw.rounded_rectangle(app_box, radius=10, fill="white", outline=TEXT_MUTED, width=1)
    draw.text(((app_box[0]+app_box[2])//2, 510), "Client Monitor App", fill=TEXT_DARK, font=font_bold, anchor="mm")
    draw.text(((app_box[0]+app_box[2])//2, 540), "(Python Script)", fill=TEXT_MUTED, font=font_small, anchor="mm")
    
    # Client Inner: Tray
    tray_box = (client_box[0]+30, 630, client_box[2]-30, 720)
    draw.rounded_rectangle(tray_box, radius=10, fill="white", outline=TEXT_MUTED, width=1)
    draw.text(((tray_box[0]+tray_box[2])//2, 660), "System Tray Icon", fill=TEXT_DARK, font=font_bold, anchor="mm")
    draw.text(((tray_box[0]+tray_box[2])//2, 690), "Status Sync (Green/Red)", fill=ACCENT_GREEN, font=font_small, anchor="mm")

    # Automation Server
    draw.rounded_rectangle(auto_box, radius=30, fill="#f8fafc", outline=ACCENT_BLUE, width=4)
    draw.text(((auto_box[0]+auto_box[2])//2, 340), "AUTOMATION SERVER", fill=(30, 58, 138), font=font_h1, anchor="mm")
    if logo_imgs['ubuntu']:
        logo = logo_imgs['ubuntu'].copy()
        logo.thumbnail((60, 60))
        img.paste(logo, (auto_box[0] + 40, 320), logo)

    # Automation Inner: Node-RED
    nr_box = (auto_box[0]+50, 420, auto_box[0]+450, 750)
    draw.rounded_rectangle(nr_box, radius=15, fill="#fef2f2", outline=ACCENT_RED, width=2)
    draw.text(((nr_box[0]+nr_box[2])//2, 450), "Node-RED", fill=ACCENT_RED, font=font_h2, anchor="mm")
    if logo_imgs['nodered']:
        logo = logo_imgs['nodered'].copy()
        logo.thumbnail((50, 50))
        img.paste(logo, (nr_box[0]+120, 435), logo)

    # Node-RED Modules
    mods = [
        ("41-client-automation", "Automation Logic"),
        ("40-client-tracking", "Client Presence"),
        ("11-dell-status", "Decentralized Status"),
        ("12-dell-health", "Health Sync")
    ]
    for i, (code, title) in enumerate(mods):
        y = 500 + i*60
        draw.rectangle((nr_box[0]+20, y, nr_box[2]-20, y+50), fill="white", outline="#fee2e2", width=1)
        draw.text((nr_box[0]+40, y+25), title, fill=TEXT_DARK, font=font_small, anchor="lm")
        draw.text((nr_box[2]-40, y+25), code, fill=TEXT_MUTED, font=font_small, anchor="rm")

    # Automation Inner: MQTT
    mq_box = (auto_box[2]-350, 450, auto_box[2]-50, 600)
    draw.rounded_rectangle(mq_box, radius=15, fill="#f0fdf4", outline=ACCENT_GREEN, width=2)
    draw.text(((mq_box[0]+mq_box[2])//2, 490), "MQTT Broker", fill=ACCENT_GREEN, font=font_h2, anchor="mm")
    if logo_imgs['mosquitto']:
        logo = logo_imgs['mosquitto'].copy()
        logo.thumbnail((120, 120))
        img.paste(logo, ((mq_box[0]+mq_box[2])//2 - 60, 510), logo)

    # Automation Inner: Scripts
    py_box = (auto_box[2]-350, 630, auto_box[2]-50, 750)
    draw.rounded_rectangle(py_box, radius=15, fill="#f5f3ff", outline=ACCENT_PURPLE, width=2)
    draw.text(((py_box[0]+py_box[2])//2, 660), "Python Scripts", fill=ACCENT_PURPLE, font=font_h2, anchor="mm") # Corrected X coordinate
    if logo_imgs['python']:
        logo = logo_imgs['python'].copy()
        logo.thumbnail((40, 40))
        img.paste(logo, ((py_box[0]+py_box[2])//2 - 20, 680), logo)
    draw.text(((py_box[0]+py_box[2])//2, 730), "IPMI / WoL / iLO", fill=TEXT_MUTED, font=font_small, anchor="mm")

    # Managed Servers
    # Dell
    draw.rounded_rectangle(dell_box, radius=20, fill="#f0fdf4", outline=ACCENT_GREEN, width=3)
    draw.text(((dell_box[0]+dell_box[2])//2, 940), "Dell T310", fill=TEXT_DARK, font=font_h2, anchor="mm")
    if logo_imgs['dell']:
        logo = logo_imgs['dell'].copy()
        logo.thumbnail((80, 80))
        img.paste(logo, (dell_box[0]+30, 920), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((100, 40))
        img.paste(logo, (dell_box[0]+30, 1020), logo)
    draw.text(((dell_box[0]+dell_box[2])//2, 1050), "Proxmox VE + VMs", fill=TEXT_MUTED, font=font_reg, anchor="mm")

    # HP
    draw.rounded_rectangle(hp_box, radius=20, fill="#fffbeb", outline=ACCENT_ORANGE, width=3)
    draw.text(((hp_box[0]+hp_box[2])//2, 940), "HP DL360p", fill=TEXT_DARK, font=font_h2, anchor="mm")
    if logo_imgs['hp']:
        logo = logo_imgs['hp'].copy()
        logo.thumbnail((80, 80))
        img.paste(logo, (hp_box[0]+30, 920), logo)
    if logo_imgs['proxmox']:
        logo = logo_imgs['proxmox'].copy()
        logo.thumbnail((100, 40))
        img.paste(logo, (hp_box[0]+30, 1020), logo)
    draw.text(((hp_box[0]+hp_box[2])//2, 1050), "Proxmox VE + VMs", fill=TEXT_MUTED, font=font_reg, anchor="mm")


    # 5. Connectors (Logic Flow)
    
    # Client -> MQTT (Presence)
    draw_bezier(draw, (app_box[2], 540), (400, 540), (mq_box[0], 525), color=ACCENT_CYAN, head=True)
    draw.text((320, 520), "Active / Heartbeat", fill=ACCENT_CYAN, font=font_small)

    # MQTT -> Client (Status)
    draw_bezier(draw, (mq_box[0], 570), (400, 680), (tray_box[2], 680), color=ACCENT_GREEN, dashed=True, head=True)
    draw.text((320, 660), "Server Status (Health)", fill=ACCENT_GREEN, font=font_small)

    # Node-RED <-> MQTT (Internal)
    draw_bezier(draw, (nr_box[2], 525), ((nr_box[2]+mq_box[0])//2, 525), (mq_box[0], 500), color=ACCENT_BLUE, head=True)
    draw_bezier(draw, (mq_box[0], 540), ((nr_box[2]+mq_box[0])//2, 540), (nr_box[2], 575), color=ACCENT_BLUE, head=True)

    # User -> Node-RED (HTTP)
    draw_bezier(draw, ((user_box[0]+user_box[2])//2, 200), (550, 250), (nr_box[0]+200, 420), color=ACCENT_BLUE, head=True)

    # Server -> HealthChecks (External)
    draw_bezier(draw, (dell_box[2], 950), (1400, 950), (hc_box[0]+50, 200), color=ACCENT_GREEN, dashed=True, head=False)
    draw.text((1500, 250), "HTTPS Pings", fill=ACCENT_GREEN, font=font_small, anchor="mm")

    # HealthChecks -> MQTT (Webhook/API)
    # Implicitly visualized by showing health sync in Node-RED
    # Let's draw HC -> Node-RED directly to show the decentralization concept conceptually
    draw_bezier(draw, (hc_box[0], 140), (nr_box[2]+200, 140), (nr_box[2]+100, 680), color=ACCENT_GREEN, dashed=True, head=True)
    draw.text((1200, 120), "Health API Pull", fill=ACCENT_GREEN, font=font_small, anchor="mm")

    # MQTT -> Scripts
    draw.line(((mq_box[0]+mq_box[2])//2, 600, (py_box[0]+py_box[2])//2, 630), fill=ACCENT_PURPLE, width=2)

    # Scripts -> Servers (Control)
    draw_bezier(draw, ((py_box[0]+py_box[2])//2, 750), (1300, 850), ((dell_box[0]+dell_box[2])//2, 900), color=ACCENT_PURPLE, head=True)
    draw.text((1050, 820), "IPMI / WoL", fill=ACCENT_PURPLE, font=font_small)

    img.save("docs/architecture_diagram.png", "PNG", optimize=True)
    print("Successfully created docs/architecture_diagram.png")

if __name__ == "__main__":
    create_diagram()
