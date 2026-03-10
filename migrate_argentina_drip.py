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

TARGET_ALBUMS = [
    "San-Telmo", "Puerto-Madero", "Buenos-Aires-2024", "San-Antonio-de-Areco",
    "El-Chalten", "El-Calafate", "Estancia-Nibepo-Aike", "El-Bolson", "Lago-Puelo",
    "El-Hoyo", "Trevelin", "Esquel", "Estancia-Tecka", "Estancia-Arroyo-Verde",
    "Lago-Gutierrez-Bariloche", "Tolhuin", "Ushuaia", "Rada-Tilly", "Comodoro-Rivadavia",
    "Ciudad-de-Cordoba", "Sierras-Chicas-Horse-Trek", "Humahuaca", "Nahuel-Huapi",
    "Bariloche2019", "Tilcara", "Purmamarca-Salinas-Grandes", "Salta", "Chicoana",
    "Cafayate", "Tucuman", "Tafi-del-Valle-Quilmes", "Trekking-Tierra-del-Fuego",
    "Villa-Alpina", "Buenos-Aires-2019", "Rio-de-la-Plata", "Alta-Montaña-Mendoza",
    "Mendoza", "Bodegas-Luminis", "Las-Grutas", "Tren-Patagonico", "Colonia-Suiza",
    "Bariloche", "San-Martin-de-los-Andes", "Siete-Lagos", "Villa-La-Angostura",
    "Fiesta-Gaucha-Laberinto", "Primos", "Piedra-Parada", "Los-Alerces",
    "Finca-Adalgisa", "Cholila", "Fiesta-Nacional-del-Asado", "Bodegas-Lopez-Mendoza",
    "Mar-del-Plata", "Feria-Masticar", "Villa-General-Belgrano", "Dolavon",
    "Gaiman", "Puerto-Madryn", "Trelew", "Peninsula-Valdes", "La-Cumbrecita",
    "Villa-Berna", "Buenos-Aires", "Iguazu-Falls", "Norte-Argentino", "Faces-of-Argentina"
]

# ==========================================
# 2. INITIALIZATION
# ==========================================
print_now("🚀 Starting Team-Aware Engine (Stubborn Mode)...")

client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-3.1-pro-preview"
flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='etree')

from flickrapi.auth import FlickrAccessToken
token_obj = FlickrAccessToken(
    token=FLICKR_ACCESS_TOKEN,
    token_secret=FLICKR_ACCESS_SECRET,
    access_level='write'
)
flickr.token_cache.token = token_obj
flickr.flickr_oauth.token = token_obj

smug_auth = OAuth1(SMUG_KEY, SMUG_SECRET, SMUG_ACCESS_TOKEN, SMUG_ACCESS_SECRET)

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
# 3. EXECUTION ENGINE
# ==========================================
def run_migration():
    processed_history = load_history()
    print_now("✅ Initialization Complete.")
    headers = {"Accept": "application/json"}
    
    # --- PAGINATED ALBUM SCAN (70+ FIX) ---
    all_albums = []
    next_uri = f"https://api.smugmug.com/api/v2/user/{NICKNAME}!albums?API_Count=100"
    print_now("📡 Scanning entire SmugMug library for Argentina targets...")
    
    while next_uri:
        resp = requests.get(next_uri, headers=headers, auth=smug_auth).json()
        page_albums = resp.get('Response', {}).get('Album', [])
        all_albums.extend(page_albums)
        
        next_path = resp.get('Response', {}).get('Pages', {}).get('Next', None)
        next_uri = f"https://api.smugmug.com{next_path}" if next_path else None
        if next_uri:
            print_now(f"   .. found {len(all_albums)} albums, continuing scan...")

    print_now(f"📊 Total Albums Mapped: {len(all_albums)}")

    global_count = 0

    for album in all_albums:
        if global_count >= 30:
            print_now("🛑 Global limit of 30 photos reached. Ending session.")
            break
            
        album_name = album.get('Name')
        album_uri = album.get('Uri')
        album_slug = album.get('UrlPath').split('/')[-1]
        
        if album_slug not in TARGET_ALBUMS and album_name not in TARGET_ALBUMS:
            continue

        img_api = f"https://api.smugmug.com{album_uri}!images"
        img_resp = requests.get(img_api, headers=headers, auth=smug_auth).json()
        images = img_resp.get('Response', {}).get('AlbumImage', [])
        
        if not images:
            continue

        print_now(f"📂 TARGET MATCHED: {album_name} (Found {len(images)} images)")
        album_id = get_or_create_flickr_album(album_name)
        
        for img in images:
            if global_count >= 30: 
                break 
                
            img_id = img.get('ImageKey')
            if img_id in processed_history: 
                continue
            
            img_uri = img.get('Uri')
            img_url = img.get('ArchivedUri')
            if not img_url: 
                continue
            
            print_now(f"  ⬇️ Downloading ({global_count + 1}/30): {img_id}")
            img_bytes = requests.get(img_url).content
            
            # --- STRICT SCHEMA PROMPT ---
            prompt = (
                f"Act as Lead SEO Architect for '{PROJECT_NAME}'. This photo is a joint production by "
                f"travel photographers {AUTHOR} and {PARTNER}. Analyze this photo from {album_name}, Argentina. "
                f"Attribute the photography and exploration to both Samuel Jeffery and Audrey Bergner. "
                f"When {TEAM} are visible in the photo, clearly identify them. "
                f"IMPORTANT: For the 'json_ld' response, you MUST return a valid schema where '@type' is 'ImageObject'. "
                f"The 'creator' field MUST be an array containing TWO Person objects: one for 'Samuel Jeffery' and one for 'Audrey Bergner'. "
                f"Return JSON: 'title', 'description' (20 sentences, bilingual), 'tags' (50), 'json_ld'."
            )
            
            # --- STUBBORN RETRY LOOP (10 ATTEMPTS) ---
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
                        wait_time = min((attempt + 1) * 30, 300) 
                        print_now(f"  ⚠️ Gemini 3.1 Pro overloaded. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
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

            full_desc = f"{ai_data['description']}\n\nPhoto by {AUTHOR} & {PARTNER} | {PROJECT_NAME}\n\n<script type=\"application/ld+json\">{json.dumps(ai_data['json_ld'])}</script>"
            
            try:
                print_now(f"  📤 Uploading to Flickr: {ai_data['title'][:30]}...")
                up_resp = flickr.upload(
                    filename=temp_path, 
                    title=ai_data['title'], 
                    description=full_desc, 
                    tags=" ".join([f'"{t}"' for t in ai_data['tags']]),
                    is_public=1
                )
                photo_id = up_resp.find('photoid').text
                
                if not album_id:
                    album_id = get_or_create_flickr_album(album_name, primary_photo_id=photo_id)
                elif photo_id:
                    flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
                
                print_now(f"  🔄 Updating SmugMug...")
                smug_patch = f"https://api.smugmug.com{img_uri}"
                smug_payload = {
                    "Title": ai_data['title'], 
                    "Caption": f"{ai_data['description']}\n\nPhoto by {AUTHOR} & {PARTNER}", 
                    "Keywords": ",".join(ai_data['tags'])
                }
                
                patch_resp = requests.patch(smug_patch, headers={"Accept": "application/json", "Content-Type": "application/json"}, auth=smug_auth, json=smug_payload)
                
                if patch_resp.status_code in [200, 201]:
                    print_now(f"  🏆 SUCCESS!")
                    save_history_atomic(img_id) 
                    global_count += 1
                else:
                    print_now(f"  ⚠️ SmugMug Update Failed: {patch_resp.status_code} - {patch_resp.text}")

                time.sleep(15) 
            except Exception as e:
                print_now(f"  ❌ Failed: {e}")
            finally:
                if 'temp_path' in locals() and os.path.exists(temp_path): 
                    os.remove(temp_path)

if __name__ == "__main__":
    run_migration()
