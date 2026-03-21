import os, time, requests, json, tempfile, sys
import flickrapi
from google import genai 
from google.genai import types
from requests_oauthlib import OAuth1

# Force logs to show up immediately in GitHub Actions
def print_now(text):
    print(text)
    sys.stdout.flush()

# ==========================================
# 1. CREDENTIALS
# ==========================================
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
FLICKR_KEY = os.environ.get('FLICKR_API_KEY')
FLICKR_SECRET = os.environ.get('FLICKR_API_SECRET')
FLICKR_ACCESS_TOKEN = os.environ.get('FLICKR_ACCESS_TOKEN')
FLICKR_ACCESS_SECRET = os.environ.get('FLICKR_ACCESS_SECRET')

SMUG_KEY = os.environ.get('SMUGMUG_API_KEY')
SMUG_SECRET = os.environ.get('SMUGMUG_API_SECRET')
SMUG_ACCESS_TOKEN = os.environ.get('SMUGMUG_ACCESS_TOKEN')
SMUG_ACCESS_SECRET = os.environ.get('SMUGMUG_ACCESS_TOKEN_SECRET')

NICKNAME = "samuelandaudrey"
PROJECT_NAME = "Project 23"
AUTHOR = "Samuel Jeffery"
PARTNER = "Audrey Bergner"
TEAM = "Samuel Jeffery, Audrey Bergner, and Daniel Bergner"
HISTORY_FILE = "migration_history.json"

# ==========================================
# 2. AUTHORITY WEBSITES
# ==========================================
# Standard format for SmugMug (Plain text auto-links)
SITES_PLAIN = (
    "\n\nExplore more of our work:\n"
    "🇦🇷 Local Guides: https://cheargentinatravel.com & https://nomadicsamuel.com\n"
    "🌎 Personal Sites: https://samueljeffery.net, https://audreybergner.com & https://samuelandaudrey.com\n"
    "📊 Project 23 Master Database: https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23"
)

# HTML format for Flickr (Makes them clickable)
SITES_HTML = (
    "\n\nExplore more of our work:\n"
    "🇦🇷 Local Guides: <a href='https://cheargentinatravel.com'>cheargentinatravel.com</a> & <a href='https://nomadicsamuel.com'>nomadicsamuel.com</a>\n"
    "🌎 Personal Sites: <a href='https://samueljeffery.net'>samueljeffery.net</a>, <a href='https://audreybergner.com'>audreybergner.com</a> & <a href='https://samuelandaudrey.com'>samuelandaudrey.com</a>\n"
    "📊 <a href='https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23'>Project 23 Master Database</a>"
)

# Links for JSON-LD sameAs array (Crucial for Entity Building)
SCHEMA_LINKS = [
    "https://cheargentinatravel.com", 
    "https://nomadicsamuel.com",
    "https://samueljeffery.net", 
    "https://audreybergner.com", 
    "https://samuelandaudrey.com",
    "https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23"
]

# ==========================================
# 3. THE 100% INTEGRATED LISTS
# ==========================================

# PHASE 1: VIP MAP (Direct Teleport using Secret Keys)
PRIORITY_MAP = {
    "Iguazu Falls: A Visual Guide to the Powerful Cascades of Argentina": "LsQ6nZ",
    "Salta & The Argentine Northwest: Colonial Heritage & Andean Culture": "HwGKwD",
    "Norte Argentino: A Visual Guide to the Argentine Northwest & Iruya": "m8QGsB",
    "Faces of Argentina": "XhwZfT",
    "The Chalet: Alpine Restoration & Boutique Design in Córdoba": "Dkghrb",
    "Salta & The Argentine Northwest": "Fh34V9",
    "Buenos Aires: The Paris of the South": "6hZGsS",
    "Villa Berna: Secluded Alpine Charm": "wdFKS7",
    "La Cumbrecita: Pedestrian Alpine Village": "4ZLgK5",
    "Península Valdés: UNESCO Wildlife": "KJ9CCC",
    "Trelew: Welsh Heritage": "mCQXhJ",
    "Puerto Madryn: Wildlife Gateway": "X9NkvD",
    "Gaiman: Welsh Heritage & Tea Houses": "2Qwjgt",
    "Dolavon: Welsh Heritage & Flour Mills": "fv2nJF",
    "Villa General Belgrano: German Heritage": "m9qXTZ",
    "Feria Masticar Mar del Plata": "McTftj",
    "Mar del Plata: Atlantic Architecture": "ZZXqw7",
    "Bodegas López: Historic Wine Cellars": "2Jxpmt",
    "Fiesta Nacional del Asado": "D8Bnbp",
    "Cholila: Gaucho Culture": "CfwJ6x",
    "Finca Adalgisa: Luxury Vineyard": "VvgHNr",
    "Los Alerces National Park": "BGVcJc",
    "Piedra Parada: Volcanic Monoliths": "TtbZTP",
    "Buenos Aires Family Gathering": "p2WqcZ",
    "Fiesta Gaucha & Laberinto Patagonia": "J7PtTt",
    "Villa La Angostura: Boutique Alpine": "qRsrKV",
    "Seven Lakes Route": "5mH8s2",
    "San Martín de los Andes": "2MVmBD",
    "Bariloche: Alpine Architecture": "nk8zVf",
    "Colonia Suiza: Historic Alpine": "5HNbSd",
    "Tren Patagónico": "W6CHP4",
    "Las Grutas: Warm Water Beaches": "DgMmcS",
    "Bodegas Luminis: Malbec Wine": "7rwRbt",
    "Mendoza: Historic Plazas": "dCmQmP",
    "Alta Montaña Mendoza": "tswP9r",
    "Río de la Plata: Sailing": "ZpkT5n",
    "Buenos Aires: Architecture & Landmarks": "xdPXcq",
    "Villa Alpina: Gateway to Champaquí": "BJDPWJ",
    "Ushuaia Trekking": "6BGzf9",
    "Tafí del Valle & Quilmes Ruins": "pk5Pd2",
    "Tucumán: Historic Independence": "JxLDph",
    "Cafayate: Torrontés Vineyards": "z8Rqg8",
    "Chicoana: Gaucho Traditions": "6DgRWw",
    "Salta: Colonial Heritage": "ssJKWS",
    "Purmamarca & Salinas Grandes": "KghTCN",
    "Tilcara: Ancient Pucará Ruins": "bT5xNp",
    "Bariloche: Gateway to Lake District": "PV7Pbg",
    "Nahuel Huapi: Glacial Lakes": "XPPbt3",
    "Humahuaca: 14-Colored Mountain": "zhc7rV",
    "Sierras Chicas: Gaucho Horse Trek": "x5ZkWd",
    "Córdoba City: Jesuit Heritage": "b9BwFS",
    "Comodoro Rivadavia": "tczXXh",
    "Rada Tilly": "xFQWXr",
    "Ushuaia: End of the World": "NQ8nMp",
    "Tolhuin: Lago Fagnano": "WDTNWj",
    "Lago Gutiérrez: Hiking & Lakes": "ZJXR95",
    "Estancia Arroyo Verde": "m2XKfP",
    "Estancia Tecka: Fly Fishing": "gzsk7v",
    "Esquel: La Trochita": "L3XbKS",
    "Trevelin: Welsh Culture": "KL9kF3",
    "El Hoyo: Patagonian Vineyards": "bmZLz2",
    "Lago Puelo National Park": "FSdpS6",
    "El Bolsón: Mountain Paradise": "nXcGt6",
    "Estancia Nibepo Aike": "XTscwd",
    "El Calafate & Perito Moreno": "bph6Wz",
    "El Chaltén Trekking": "xdgbn9",
    "San Antonio de Areco": "5s3TL5",
    "Historic Buenos Aires Exploration": "7SKZQD",
    "San Telmo: Oldest Neighborhood": "4VBvqX",
    "Puerto Madero Barrio": "8jkVcc"
}

# ==========================================
# 4. INITIALIZATION
# ==========================================
print_now("🚀 Starting Hybrid Engine (VIP-Surgical Mode w/ SEO Links)...")

client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-3.1-flash-lite-preview"
flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='etree')

from flickrapi.auth import FlickrAccessToken
token_obj = FlickrAccessToken(token=FLICKR_ACCESS_TOKEN, token_secret=FLICKR_ACCESS_SECRET, access_level='write')
flickr.token_cache.token = token_obj
flickr.flickr_oauth.token = token_obj

smug_auth = OAuth1(SMUG_KEY, SMUG_SECRET, SMUG_ACCESS_TOKEN, SMUG_ACCESS_SECRET)
headers = {"Accept": "application/json"}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_history_atomic(img_id):
    history = load_history()
    if img_id not in history:
        history.append(img_id)
        with open(HISTORY_FILE, 'w') as f: 
            json.dump(history, f, indent=2)
        print_now(f"  💾 [History Saved]: {img_id}")

def get_or_create_flickr_album(album_name, primary_photo_id=None):
    try:
        sets = flickr.photosets.getList()
        for s in sets.find('photosets').findall('photoset'):
            if s.find('title').text == album_name:
                return s.get('id')
        if primary_photo_id:
            new_set = flickr.photosets.create(title=album_name, primary_photo_id=primary_photo_id)
            return new_set.find('photoset').get('id')
    except: pass
    return None

# ==========================================
# 5. CORE IMAGE PROCESSING FUNCTION
# ==========================================
def process_album_images(images, official_album_name, global_count, processed_history):
    album_id = get_or_create_flickr_album(official_album_name)
    
    for img in images:
        if global_count >= 40: 
            return global_count
            
        img_id = img.get('ImageKey')
        if img_id in processed_history: 
            continue
        
        img_uri = img.get('Uri')
        img_url = img.get('ArchivedUri')
        if not img_url: 
            continue
        
        print_now(f"  ⬇️ Downloading ({global_count + 1}/40): {img_id}")
        img_bytes = requests.get(img_url).content
        
       # --- MASTER NARRATIVE & SCHEMA PROMPT ---
        prompt = (
            f"Act as a professional travel documentary photographer and regional expert for '{PROJECT_NAME}'. "
            f"Analyze this photo from {official_album_name}, Argentina, shot by {AUTHOR} and {PARTNER}. "
            f"\n\nIDENTITY HINTS FOR RECOGNITION (Use these to identify the subjects):\n"
            f"- {AUTHOR} (Samuel): Fair skin, reddish/strawberry-blonde hair, green/hazel eyes. Look varies by era: older photos often feature a clean-cut look with short hair, while other eras show long, curly/wavy shoulder-length hair paired with a thick red beard. Lean to average build.\n"
            f"- {PARTNER} (Audrey): Lean/athletic build, medium-length bronde/dirty-blonde hair (frequently worn down/out in older photos, or tied back/under a hat). Large green eyes, full smile, and a distinct small mole on her left cheek.\n"
            f"- Daniel Bergner: Older man (late 60s/70s), short white hair, distinct white mustache, wears glasses, stocky/broad build.\n\n"
            f"STYLE GUARDRAIL: Do NOT mention specific moles, hair colors, eye colors or other physical characteristic in the description. Describe the PEOPLE through their actions, emotions, and connection to the landscape instead.\n\n"
            f"STRICT INSTRUCTIONS for the 'title' field:\n"
            f"1. You MUST provide a descriptive title between 10 and 15 words. This is a hard constraint.\n"
            f"2. Capture specific visual elements (textures, lighting, landmarks) and the Argentine cultural setting.\n"
            f"3. Example: 'Rustic Stone Architecture and Traditional Welsh Tea House in the Village of Gaiman Chubut'.\n\n"
            f"STRICT INSTRUCTIONS for the 'description' field:\n"
            f"1. START immediately with a vivid, sensory description of the subject and location. NO AI INTROS or greetings.\n"
            f"2. Focus on the atmosphere, technical photography (lighting, depth of field), and cultural context.\n"
            f"3. Use a mix of complex and compound sentences to ensure the narrative feels professional and authoritative.\n"
            f"4. DO NOT mention who is NOT in the photo. Only identify members of {TEAM} if they are physically visible in the image.\n"
            f"5. At the very end of the English description, add this exact sentence: 'This image is a collaborative production by {AUTHOR} and {PARTNER} for {PROJECT_NAME}.'\n"
            f"6. Provide ~10-12 high-quality sentences in English, then a '---' separator, then the exact Spanish translation.\n\n"
            f"STRICT INSTRUCTIONS for the 'json_ld' field:\n"
            f"You MUST return a valid schema where '@type' is 'ImageObject'. "
            f"The 'creator' field MUST be an array containing TWO Person objects: one for 'Samuel Jeffery' and one for 'Audrey Bergner'. "
            f"Include 'sameAs': {json.dumps(SCHEMA_LINKS)} for both Person objects.\n\n"
            f"Return JSON: 'title', 'description', 'tags' (50), 'json_ld'."
        )
        
        ai_data = None
        max_retries = 10
        
        for attempt in range(max_retries):
            try:
                ai_resp = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'), prompt]
                )
                ai_data = json.loads(ai_resp.text.replace('```json', '').replace('```', '').strip())
                break 
            except Exception as e:
                if "503" in str(e) or "high demand" in str(e):
                    wait_time = min((attempt + 1) * 20, 60) 
                    print_now(f"  ⚠️ Gemini overloaded. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print_now(f"  ❌ Fatal AI Error: {e}")
                    break 
        
        if not ai_data:
            print_now(f"  ⏭️ Giving up on photo {img_id} after {max_retries} attempts.")
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            temp.write(img_bytes)
            temp_path = temp.name

        # --- DUAL-FORMAT FOOTERS ---
        flickr_desc = f"{ai_data['description']}{SITES_HTML}\n\nPhoto by {AUTHOR} & {PARTNER} | {PROJECT_NAME}\n\n<script type=\"application/ld+json\">{json.dumps(ai_data['json_ld'])}</script>"
        smug_caption = f"{ai_data['description']}{SITES_PLAIN}\n\nPhoto by {AUTHOR} & {PARTNER}"
        
        try:
            print_now(f"  📤 Uploading to Flickr: {ai_data['title'][:40]}...")
            up_resp = flickr.upload(filename=temp_path, title=ai_data['title'], description=flickr_desc, tags=" ".join([f'"{t}"' for t in ai_data['tags']]), is_public=1)
            photo_id = up_resp.find('photoid').text
            
            if not album_id:
                album_id = get_or_create_flickr_album(official_album_name, primary_photo_id=photo_id)
            elif photo_id:
                flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
            
            print_now(f"  🔄 Updating SmugMug...")
            smug_payload = {
                "Title": ai_data['title'], 
                "Caption": smug_caption, 
                "Keywords": ",".join(ai_data['tags'])
            }
            
            patch_resp = requests.patch(f"https://api.smugmug.com{img_uri}", headers={"Accept": "application/json", "Content-Type": "application/json"}, auth=smug_auth, json=smug_payload)
            
            if patch_resp.status_code in [200, 201]:
                print_now(f"  🏆 SUCCESS!")
                save_history_atomic(img_id) 
                global_count += 1
            else:
                print_now(f"  ⚠️ SmugMug Update Failed: {patch_resp.status_code}")

            time.sleep(45) 
        except Exception as e:
            print_now(f"  ❌ Failed: {e}")
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path): 
                os.remove(temp_path)
                
    return global_count

# ==========================================
# 6. EXECUTION ENGINE (VIP-ONLY DEPTH-FIRST)
# ==========================================
def run_migration():
    processed_history = load_history()
    global_count = 0
    print_now("✅ Initialization Complete. Running Priority List Only.")

    # --- VIP TELEPORT ONLY ---
    for custom_name, album_key in PRIORITY_MAP.items():
        if global_count >= 40: break

        print_now(f"⚡ Checking VIP Album: {custom_name} (Key: {album_key})")
        img_api = f"https://api.smugmug.com/api/v2/album/{album_key}!images?count=10000"
        img_resp = requests.get(img_api, headers=headers, auth=smug_auth).json()
        images = img_resp.get('Response', {}).get('AlbumImage', [])
        
        # Filter for only what hasn't been done yet
        unprocessed = [i for i in images if i.get('ImageKey') not in processed_history]
        
        if not unprocessed:
            print_now(f"  ✅ {custom_name} is 100% complete. Moving to next VIP target...")
            continue

        # Process as many as we can in THIS album up to the 40 limit
        print_now(f"  📂 Found {len(unprocessed)} photos remaining in {custom_name}. Processing...")
        global_count = process_album_images(unprocessed, custom_name, global_count, processed_history)
        
        # CRITICAL: Hard stop if we hit 40 to maintain depth focus
        if global_count >= 40:
            print_now(f"🛑 Hit 40-photo limit while working on {custom_name}. Stopping to maintain focus.")
            return 

    if global_count >= 40:
        print_now("🛑 Global limit of 40 photos reached. Ending session.")
    else:
        print_now("🏁 All albums in the PRIORITY_MAP have been 100% migrated.")

if __name__ == "__main__":
    run_migration()
