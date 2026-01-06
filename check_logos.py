import requests

urls = {
    'Dell': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dell_logo_2016.svg/200px-Dell_logo_2016.svg.png',
    'HP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/HP_logo_2012.svg/200px-HP_logo_2012.svg.png',
    'Node-RED': 'https://raw.githubusercontent.com/node-red/node-red/master/resources/node-red-icon.png',
    'Python': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/200px-Python-logo-notext.svg.png',
    'Mosquitto': 'https://mosquitto.org/images/mosquitto-text-side.png',
    'Healthchecks': 'https://healthchecks.io/static/img/logo.png',
    'Proxmox': 'https://www.proxmox.com/images/proxmox/proxmox-logo-color-stacked.png',
    'Ubuntu': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Logo-ubuntu_cof-orange-hex.svg/200px-Logo-ubuntu_cof-orange-hex.svg.png'
}

headers = {"User-Agent": "Mozilla/5.0"}

for name, url in urls.items():
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"{name}: {r.status_code}")
    except Exception as e:
        print(f"{name}: Error - {e}")
