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
MODEL_ID = "gemini-1.5-pro" # Using Pro for the 6-paragraph depth

HISTORY_FILE = "album_history.json"
auth = OAuth1(SMUG_KEY, SMUG_SECRET, SMUG_TOKEN, SMUG_TOKEN_SECRET)

# ==========================================
# 2. PRIORITY MAP
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
    "Bariloche 2026 Family Trip: Modern Exploration of the Argentine Lake District": "tQ8NRr"
}

def smug_api(url, method="GET", data=None):
    headers = {"Accept": "application/json", "User-Agent": "SamuelAndAudreyMediaBot/1.0"}
    if method == "GET":
        resp = requests.get(url, auth=auth, headers=headers)
    else:
        resp = requests.patch(url, auth=auth, headers=headers, json=data)
    
    try:
        return resp.json()
    except:
        print_now(f"  ⚠️ Non-JSON response from {url}")
        return {}

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
    
    album_url = f"https://www.smugmug.com/api/v2/album/{album_key}!images?count=500"
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
    
    print_now(f"📸 Sampling {len(sample)} images...")
    
    image_parts = []
    for img in sample:
        # Using ArchivedUri (direct download link) as used in your migration script
        img_url = img.get('ArchivedUri')
        if img_url:
            img_bytes = requests.get(img_url).content
            image_parts.append(types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'))

    print_now(f"🧠 Asking Gemini to write the Ledger...")
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=[SYSTEM_PROMPT] + image_parts)
        raw_text = response.text.strip()
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        clean_json = raw_text[start_idx:end_idx+1]
        result = json.loads(clean_json)
        
        social_links = (
            "\n\nExplore more of our work:\n"
            "🎥 YouTube: <a href='https://youtube.com/@samuelandaudrey'>@samuelandaudrey</a> & <a href='https://youtube.com/@samuelyaudrey'>@samuelyaudrey</a>\n"
            "🎒 Travel Guides: <a href='https://thatbackpacker.com'>thatbackpacker.com</a> & <a href='https://nomadicsamuel.com'>nomadicsamuel.com</a>\n"
            "🇦🇷 Local Guides: <a href='https://cheargentinatravel.com'>cheargentinatravel.com</a>\n"
            "🌎 Personal Sites: <a href='https://samueljeffery.net'>samueljeffery.net</a>, <a href='https://audreybergner.com'>audreybergner.com</a> & <a href='https://samuelandaudrey.com'>samuelandaudrey.com</a>\n"
            "📊 <a href='https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23'>Project 23 Master Database</a>"
        )

        update_url = f"https://www.smugmug.com/api/v2/album/{album_key}"
        payload = {
            "Name": result['title'],
            "Description": result['description'] + social_links,
            "Keywords": result['tags']
        }
        
        resp = smug_api(update_url, method="PATCH", data=payload)
        if resp.get('Code') == 200 or 'Response' in resp:
            print_now(f"✅ ALBUM UPDATED: {result['title']}")
            return True
        return False
            
    except Exception as e:
        print_now(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    
    with open(HISTORY_FILE, 'r') as f:
        try: history = json.load(f)
        except: history = []

    for name, key in PRIORITY_MAP.items():
        if key in history:
            print_now(f"⏩ {name} already processed.")
            continue
            
        if process_album(name, key):
            history.append(key)
            with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=2)
            time.sleep(5)
