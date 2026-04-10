import os, json, time, sys, requests
from requests_oauthlib import OAuth1
from google import genai 
from google.genai import types

def print_now(text):
    print(text)
    sys.stdout.flush()

# ==========================================
# 1. CREDENTIALS (GITHUB SECRETS)
# ==========================================
SMUG_KEY = os.environ.get('SMUGMUG_API_KEY')
SMUG_SECRET = os.environ.get('SMUGMUG_API_SECRET')
SMUG_TOKEN = os.environ.get('SMUGMUG_ACCESS_TOKEN')
SMUG_TOKEN_SECRET = os.environ.get('SMUGMUG_ACCESS_TOKEN_SECRET')

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
MODEL_ID = "gemini-1.5-pro" 

HISTORY_FILE = "album_history.json"
MASTER_FILE = "ALBUM_METADATA_MASTER.json"
auth = OAuth1(SMUG_KEY, SMUG_SECRET, SMUG_TOKEN, SMUG_TOKEN_SECRET)

# ==========================================
# 2. PRIORITY MAP (ALL 71 GALLERIES)
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

def smug_api(url):
    headers = {"Accept": "application/json", "User-Agent": "SamuelAndAudreyMediaBot/1.0"}
    resp = requests.get(url, auth=auth, headers=headers, timeout=30)
    return resp.json()

# ==========================================
# 3. CORE PROCESSING (FRUGAL + FILE OUTPUT)
# ==========================================
def process_album(album_name, album_key):
    print_now(f"\n🚀 STARTING FRUGAL AUDIT: {album_name}")
    
    album_url = f"https://www.smugmug.com/api/v2/album/{album_key}!images?count=10000"
    data = smug_api(album_url)
    images = data.get('Response', {}).get('AlbumImage', [])
    
    if not images:
        print_now(f"⚠️ No images found in {album_key}")
        return False

    if len(images) <= 50:
        sample = images
    else:
        step = max(1, len(images) // 50)
        sample = images[::step][:50]
    
    image_parts = []
    for img in sample:
        img_url = img.get('ArchivedUri')
        if img_url:
            try:
                img_bytes = requests.get(img_url, timeout=20).content
                image_parts.append(types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'))
            except: continue

    SYSTEM_PROMPT = """
    You are a high-end travel publisher and SEO specialist. Analyze these photos from a single gallery.
    1. Title: Create one title: [DESTINATION] Photos | [Keyword 1], [Keyword 2] & [Keyword 3] Photography Gallery | [Province], [Region], [Country] | Samuel & Audrey
    2. Description: Write 6 long, grounded paragraphs (800-1000 words total). 
       - NO AI-isms (tapestry, vibrant, nestled, delve, underscores). 
       - Focus on experiences: food textures, transit models, architectural styles.
    3. Meta Description: First sentence must be 150-160 chars and front-loaded with keywords.
    4. Tags: Provide 50 comma-separated SEO tags.
    Return JSON: {"title": "...", "description": "...", "tags": "..."}
    """

    ai_data = None
    for attempt in range(10):
        try:
            print_now(f"🧠 Gemini Analysis (Attempt {attempt+1}/10)...")
            response = client.models.generate_content(model=MODEL_ID, contents=[SYSTEM_PROMPT] + image_parts)
            raw_text = response.text.strip()
            start_idx = raw_text.find('{')
            end_idx = raw_text.rfind('}')
            ai_data = json.loads(raw_text[start_idx:end_idx+1])
            break 
        except Exception:
            wait_time = min((attempt + 1) * 20, 120) 
            time.sleep(wait_time)

    if not ai_data: return False

    social_links = (
        "\n\n🎥 YouTube: @samuelandaudrey & @samuelyaudrey\n"
        "🎒 Travel Guides: thatbackpacker.com & nomadicsamuel.com\n"
        "🇦🇷 Local Guides: cheargentinatravel.com\n"
        "🌎 Personal Sites: samueljeffery.net, audreybergner.com & samuelandaudrey.com\n"
        "📊 Project 23 Master Database"
    )

    # Load existing Master Ledger or create new
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, 'r') as f:
            try: master_data = json.load(f)
            except: master_data = {}
    else:
        master_data = {}

    # Append new data
    master_data[album_name] = {
        "new_title": ai_data['title'],
        "description": ai_data['description'] + social_links,
        "tags": ai_data['tags'],
        "key": album_key,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(MASTER_FILE, 'w') as f:
        json.dump(master_data, f, indent=4)

    print_now(f"✅ SAVED TO LEDGER: {ai_data['title']}")
    return True

if __name__ == "__main__":
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    
    with open(HISTORY_FILE, 'r') as f:
        try: history = json.load(f)
        except: history = []

    for name, key in PRIORITY_MAP.items():
        if key in history:
            print_now(f"⏩ {name} skipped.")
            continue
            
        if process_album(name, key):
            history.append(key)
            with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=2)
            time.sleep(5)
