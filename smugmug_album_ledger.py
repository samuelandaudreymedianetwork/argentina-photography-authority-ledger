import os, json, time, sys, requests
from requests_oauthlib import OAuth1
import google.generativeai as genai

# Force logs to show up immediately in GitHub Actions
def print_now(text):
    print(text)
    sys.stdout.flush()

# ==========================================
# 1. CREDENTIALS (PULLING FROM GITHUB SECRETS)
# ==========================================
SMUG_KEY = os.environ.get('SMUGMUG_API_KEY')
SMUG_SECRET = os.environ.get('SMUGMUG_API_SECRET')
SMUG_TOKEN = os.environ.get('SMUGMUG_ACCESS_TOKEN')
SMUG_TOKEN_SECRET = os.environ.get('SMUGMUG_ACCESS_TOKEN_SECRET')

# Securely grab Gemini Key from GitHub Secrets
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')

HISTORY_FILE = "album_history.json"

# ==========================================
# 2. PRIORITY MAP (YOUR LIST)
# ==========================================
PRIORITY_MAP = {
    "Buenos Aires, Argentina: A Visual Ledger of Family Visits": "B8h5q7",
    "El Chalten to El Calafate to Puerto Natales (Argentina to Chile Border Crossing)": "xdGpN7",
    "Punta Arenas To Ushuaia Transportation by Bus and Ferry (Chile to Argentina Border Crossing)": "LSv63z",
    "Best Pizza In Buenos Aires Challenge Along Avenida Corrientes": "JhtCHn",
    "Puerto Varas, Chile (Family Trip): Lake Llanquihue & Osorno Volcano": "G4L636",
    "Punta Arenas, Chile (Capital of Magallanes): Maritime History, Food and Culture": "Bw8kWp",
    "Torres del Paine National Park (Chilean Patagonia): Wildlife, Glaciers & Iconic Peaks": "kBNdZJ",
    "Puerto Natales, Chile: A Patagonian Coastal Town Guide": "B2SJCc",
    "Montevideo, Uruguay: Historic Architecture, Markets & Local Food": "X4gct7",
    "Colonia del Sacramento, Uruguay: UNESCO World Heritage & Historic Streets": "LSmDqf",
    "Buenos Aires to Uruguay: The Buquebus Ferry Border Crossing From Argentina": "v7k4Jr",
    "Río Gallegos: Museums, Food and Dinosaurs as a Stopover in Santa Cruz, Southern Patagonia": "Lrdhvz",
    "Bariloche 2026 Family Trip: Modern Exploration of the Argentine Lake District": "tQ8NRr",
    "Iguazu Falls: A Visual Guide to the Powerful Cascades of Argentina": "LsQ6nZ",
    "Salta & The Argentine Northwest: Colonial Heritage & Andean Culture": "HwGKwD",
    "Norte Argentino: A Visual Guide to the Argentine Northwest & Iruya": "m8QGsB",
    "The Chalet: Alpine Restoration & Boutique Design in Córdoba": "Dkghrb",
    "Buenos Aires: A Visual Guide to Argentina’s Capital & Architecture": "FNNC8L",
    "Buenos Aires: The Paris of the South": "6hZGsS",
    "Salta & The Argentine Northwest: Colonial Heritage & Rainbow Mountains": "Fh34V9",
    "Tucumán: Historic Independence City & Northern Gastronomy": "JxLDph",
    "Tafí del Valle & Quilmes Ruins: High Altitudes and Sacred History": "pk5Pd2",
    "Ushuaia Trekking: Tierra del Fuego National Park & Beagle Channel": "6BGzf9",
    "Villa Alpina: Gateway to Champaquí & Alpine Córdoba": "BJDPWJ",
    "Río de la Plata: Sailing & River Navigation in Buenos Aires": "ZpkT5n",
    "Alta Montaña Mendoza: Aconcagua & High Andes Landscapes": "tswP9r",
    "Mendoza: Historic Plazas, Andean Culture & Wine Capital": "dCmQmP",
    "Bodegas Luminis: Malbec Wine Tours & Mendoza Vineyards": "7rwRbt",
    "Las Grutas: Warm Water Beaches & Atlantic Coastal Caves": "DgMmcS",
    "Tren Patagónico: Crossing Patagonia by Rail from Bariloche": "W6CHP4",
    "Colonia Suiza: Historic Alpine Village & Gastronomy in Bariloche": "5HNbSd",
    "Bariloche: Alpine Architecture, Nahuel Huapi & Lake District Views": "nk8zVf",
    "San Martín de los Andes: Gateway to the Seven Lakes Route": "2MVmBD",
    "Seven Lakes Route: Argentina’s Most Iconic Scenic Road Trip": "5mH8s2",
    "Villa La Angostura: Boutique Alpine Village & Lake Nahuel Huapi": "qRsrKV",
    "Fiesta Gaucha & Laberinto Patagonia: Culture & Mazes in El Bolsón": "J7PtTt",
    "Buenos Aires Family Gathering: Porteño Life & Personal Moments": "p2WqcZ",
    "Piedra Parada: Volcanic Monoliths & Cañadón de la Buitrera": "TtbZTP",
    "Los Alerces National Park: Ancient Forests & Glacial Lakes": "BGVcJc",
    "Finca Adalgisa: Luxury Vineyard Stay & Malbec Tastings in Mendoza": "VvgHNr",
    "Cholila: Gaucho Culture, Butch Cassidy’s Ranch & Patagonian Asado": "CfwJ6x",
    "Fiesta Nacional del Asado: Argentina’s Biggest BBQ in Cholila, Patagonia": "D8Bnbp",
    "San Telmo: A Visual Journey through Buenos Aires’ Oldest Neighborhood (Barrio) in Argentina": "4VBvqX",
    "Historic Buenos Aires Exploration: Architecture, Landmarks & Palaces": "7SKZQD",
    "San Antonio de Areco: Gaucho Culture & Estancia Life": "5s3TL5",
    "El Chaltén Trekking: Hiking Mount Fitz Roy & Enjoying Patagonian Landscapes": "xdgbn9",
    "El Calafate & Perito Moreno Glacier: Patagonia's Ice Giants": "bph6Wz",
    "Estancia Nibepo Aike: Gaucho Culture & Patagonian Ranch Life": "XTscwd",
    "El Hoyo: Patagonian Vineyards, Lakes & Waterfalls": "bmZLz2",
    "Estancia Tecka: Luxury Fly Fishing & Patagonian Steppe": "gzsk7v",
    "Estancia Arroyo Verde: Luxury Fly Fishing on the Traful River": "m2XKfP",
    "Lago Gutiérrez: Hiking & Alpine Lakes in Bariloche": "ZJXR95",
    "Tolhuin: Lago Fagnano & The Heart of Tierra del Fuego": "WDTNWj",
    "Ushuaia: Adventure at the End of the World": "NQ8nMp",
    "Rada Tilly: The World's Southernmost Beach Town": "xFQWXr",
    "Comodoro Rivadavia: The Gateway to Atlantic Patagonia": "tczXXh",
    "Córdoba City: Jesuit Heritage & Colonial Architecture": "b9BwFS",
    "Sierras Chicas: Gaucho Horse Trek & Córdoba Mountain Life": "x5ZkWd",
    "Humahuaca: The 14-Colored Mountain & Andean Culture": "zhc7rV",
    "Nahuel Huapi: Glacial Lakes & Andean Wilderness": "XPPbt3",
    "Bariloche: The Gateway to the Argentine Lake District": "PV7Pbg",
    "Tilcara: Ancient Pucará Ruins & Andean Heritage": "bT5xNp",
    "Purmamarca & Salinas Grandes: The Colors of Jujuy": "KghTCN",
    "Chicoana: Gaucho Traditions & Gateway to the Lerma Valley": "6DgRWw",
    "Salta: Colonial Heritage & The Gateway to the Andean North": "ssJKWS",
    "Cafayate: Torrontés Vineyards & The Quebrada de las Conchas": "z8Rqg8",
    "Lago Puelo National Park: Alpine Lakes & The Chilean Border": "FSdpS6",
    "El Bolsón: Patagonia's Mountain Paradise & Nature Trails": "nXcGt6",
    "Trevelin: Welsh Culture & Cool-Climate Vineyards in Patagonia": "KL9kF3",
    "Esquel: La Trochita & Patagonian Autumn Adventures": "L3XbKS",
    "Puerto Madero Barrio: Modern Skyline, Costanera Sur Ecological Reserve & Historic Docks in Buenos Aires, Argentina": "8jkVcc"
}

auth = OAuth1(SMUG_KEY, SMUG_SECRET, SMUG_TOKEN, SMUG_TOKEN_SECRET)

def smug_api(url, method="GET", data=None):
    headers = {"Accept": "application/json"}
    if method == "GET":
        resp = requests.get(url, auth=auth, headers=headers)
    else:
        resp = requests.patch(url, auth=auth, headers=headers, json=data)
    return resp.json()

# ==========================================
# 3. THE VISUAL LEDGER PROTOCOL
# ==========================================
SYSTEM_PROMPT = """
You are a high-end travel publisher and SEO specialist. Analyze these photos from a single gallery.
1. Title: Create one authoritative title following: [DESTINATION] Photos | [Keyword 1], [Keyword 2] & [Keyword 3] Photography Gallery | [Province], [Region], [Country] | Samuel & Audrey
2. Description: Write 6 long, grounded paragraphs (approx 800-1000 words total). 
   - NO AI-isms (tapestry, vibrant, nestled, delve, underscores). 
   - Focus on actual experiences: the texture of the food, the specific models of transit (Don Otto, Marcopolo), the architectural styles, and the atmosphere of the destination.
3. First Sentence: Must be a punchy meta-description (150-160 chars) front-loaded with keywords for Google SERPs.
4. Tags: Provide 50 comma-separated SEO tags based on visual data.

Return strictly in this JSON format:
{"title": "...", "description": "...", "tags": "..."}
"""

def process_album(album_name, album_key):
    print_now(f"\n🚀 STARTING ALBUM: {album_name}")
    
    # 1. Fetch images from album
    album_url = f"https://www.smugmug.com/api/v2/album/{album_key}!images"
    data = smug_api(album_url)
    images = data.get('Response', {}).get('AlbumImage', [])
    
    if not images:
        print_now(f"⚠️ No images found in {album_key}")
        return False

    # 2. Sample Logic: Sample up to 50 images spread across the gallery
    if len(images) <= 50:
        sample = images
    else:
        step = max(1, len(images) // 50)
        sample = images[::step][:50]
    
    print_now(f"📸 Sampling {len(sample)} images for full-gallery analysis...")
    
    image_parts = []
    for img in sample:
        img_url = img.get('Uris', {}).get('LargestImage', {}).get('Uri')
        if img_url:
            full_img_url = f"https://www.smugmug.com{img_url}"
            img_data = requests.get(full_img_url, auth=auth).json()
            actual_url = img_data.get('Response', {}).get('LargestImage', {}).get('Url')
            
            img_bytes = requests.get(actual_url).content
            image_parts.append({"mime_type": "image/jpeg", "data": img_bytes})

    # 3. Send to Gemini
    print_now(f"🧠 Asking Gemini to write the Ledger (Paid Tier)...")
    try:
        response = model.generate_content([SYSTEM_PROMPT] + image_parts)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_json)
        
        social_links = (
            "\n\nExplore more of our work:\n"
            "🎥 YouTube: <a href='https://youtube.com/@samuelandaudrey'>@samuelandaudrey</a> & <a href='https://youtube.com/@samuelyaudrey'>@samuelyaudrey</a>\n"
            "🎒 Travel Guides: <a href='https://thatbackpacker.com'>thatbackpacker.com</a> & <a href='https://nomadicsamuel.com'>nomadicsamuel.com</a>\n"
            "🇦🇷 Local Guides: <a href='https://cheargentinatravel.com'>cheargentinatravel.com</a>\n"
            "🌎 Personal Sites: <a href='https://samueljeffery.net'>samueljeffery.net</a>, <a href='https://audreybergner.com'>audreybergner.com</a> & <a href='https://samuelandaudrey.com'>samuelandaudrey.com</a>\n"
            "📊 <a href='https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23'>Project 23 Master Database</a>"
        )

        # 4. Update SmugMug Album
        update_url = f"https://www.smugmug.com/api/v2/album/{album_key}"
        payload = {
            "Name": result['title'],
            "Description": result['description'] + social_links,
            "Keywords": result['tags']
        }
        
        resp = smug_api(update_url, method="PATCH", data=payload)
        # SmugMug usually returns 200 for successful PATCH
        if resp.get('Code') == 200 or 'Response' in resp:
            print_now(f"✅ ALBUM UPDATED: {result['title']}")
            return True
        else:
            print_now(f"❌ SmugMug Update Failed: {resp.get('Message')}")
            return False
            
    except Exception as e:
        print_now(f"❌ Error during processing: {e}")
        return False

# ==========================================
# 4. EXECUTION ENGINE
# ==========================================
if __name__ == "__main__":
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    
    with open(HISTORY_FILE, 'r') as f:
        try: history = json.load(f)
        except: history = []

    for name, key in PRIORITY_MAP.items():
        if key in history:
            print_now(f"⏩ {name} already processed. Skipping.")
            continue
            
        if process_album(name, key):
            history.append(key)
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
            time.sleep(5) # Pause between albums
