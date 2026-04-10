import os, time, requests, json, tempfile, sys, random
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
TEAM = "Samuel Jeffery, Audrey Bergner, Daniel Bergner, and Aurelia Jeffery"
HISTORY_FILE = "migration_history.json"

# ==========================================
# 2. AUTHORITY WEBSITES
# ==========================================
SITES_PLAIN = (
    "\n\nExplore more of our work:\n"
    "🎥 YouTube: https://youtube.com/@samuelandaudrey & https://youtube.com/@samuelyaudrey\n"
    "🎒 Travel Guides: https://thatbackpacker.com & https://nomadicsamuel.com\n"
    "🇦🇷 Local Guides: https://cheargentinatravel.com\n"
    "🌎 Personal Sites: https://samueljeffery.net, https://audreybergner.com & https://samuelandaudrey.com\n"
    "📊 Project 23 Master Database: https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23"
)

SITES_HTML = (
    "\n\nExplore more of our work:\n"
    "🎥 YouTube: <a href='https://youtube.com/@samuelandaudrey'>@samuelandaudrey</a> & <a href='https://youtube.com/@samuelyaudrey'>@samuelyaudrey</a>\n"
    "🎒 Travel Guides: <a href='https://thatbackpacker.com'>thatbackpacker.com</a> & <a href='https://nomadicsamuel.com'>nomadicsamuel.com</a>\n"
    "🇦🇷 Local Guides: <a href='https://cheargentinatravel.com'>cheargentinatravel.com</a>\n"
    "🌎 Personal Sites: <a href='https://samueljeffery.net'>samueljeffery.net</a>, <a href='https://audreybergner.com'>audreybergner.com</a> & <a href='https://samuelandaudrey.com'>samuelandaudrey.com</a>\n"
    "📊 <a href='https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23'>Project 23 Master Database</a>"
)

SCHEMA_LINKS = [
  "https://thatbackpacker.com",
    "https://nomadicsamuel.com",
    "https://cheargentinatravel.com", 
    "https://samueljeffery.net", 
    "https://audreybergner.com", 
    "https://samuelandaudrey.com",
    "https://youtube.com/@samuelandaudrey",
    "https://youtube.com/@samuelyaudrey",
    "https://nomadicsamuel.com/argentina-authority-ledger-master-database-project-23"
]

# ==========================================
# 3. THE 100% INTEGRATED LISTS
# ==========================================
PRIORITY_MAP = {
    "Buenos Aires, Argentina: A Visual Ledger of Family Visits": "B8h5q7",
    "Bariloche Family Trip (Argentine Lake District)": "tQ8NRr",
    "Cruce Andino (Lake Crossing from Bariloche to Puerto Varas)": "CpQ57N",
    "Llao Llao Hotel: Alpine Luxury & Family Travel in Bariloche, Patagonia": "rnmm72",
    "El Bolsón: A Perfect Week With Friends + Exploring The Surrounding Area": "jrGXgp",
    "El Maitén: La Trochita Old Patagonian Express (Epic Historical Train Ride)": "NHFHzw",
    "El Chalten to El Calafate to Puerto Natales (Argentina to Chile Border Crossing)": "xdGpN7",
    "Punta Arenas To Ushuaia Transportation by Bus and Ferry (Chile to Argentina Border Crossing)": "LSv63z",
    "Best Pizza In Buenos Aires Challenge Along Avenida Corrientes": "JhtCHn",
    "Río Gallegos: Museums, Food and Dinosaurs as a Stopover in Santa Cruz, Southern Patagonia": "Lrdhvz"
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
def process_album_images(images, official_album_name, global_count, processed_history, session_limit):
    album_id = get_or_create_flickr_album(official_album_name)
    
    for img in images:
        if global_count >= session_limit: 
            return global_count
            
        img_id = img.get('ImageKey')
        if img_id in processed_history: 
            continue
        
        img_uri = img.get('Uri')
        img_url = img.get('ArchivedUri')
        if not img_url: 
            continue
        
        print_now(f"  ⬇️ Downloading ({global_count + 1}/{session_limit}): {img_id}")
        img_bytes = requests.get(img_url).content
        
        prompt = (
            f"Act as a professional travel documentary photographer and regional expert for '{PROJECT_NAME}'. "
            f"Analyze this photo from {official_album_name}, Argentina, shot by {AUTHOR} and {PARTNER}. "
            f"\n\nIDENTITY HINTS FOR RECOGNITION (Use these to identify the subjects):\n"
            f"- {AUTHOR} (Samuel): Fair skin, reddish/strawberry-blonde hair, green/hazel eyes. Look varies by era: older photos often feature a clean-cut look with short hair, while other eras show long, curly/wavy shoulder-length hair paired with a thick red beard. Lean to average build.\n"
            f"- {PARTNER} (Audrey): Lean/athletic build, medium-length bronde/dirty-blonde hair (frequently worn down/out in older photos, or tied back/under a hat). Large green eyes, full smile, and a distinct small mole on her left cheek.\n"
            f"- Daniel Bergner: Older man (late 60s/70s), short white hair, distinct white mustache, wears glasses, stocky/broad build.\n"
            f"- Aurelia Jeffery: Toddler (around 18 months old), clear blue eyes. Often seen in a relaxed, open state or engaged with objects.\n\n"
            f"STYLE GUARDRAIL: Do NOT mention specific moles, hair colors, eye colors or other physical characteristic in the description. Describe the PEOPLE through their actions, emotions, and connection to the landscape instead.\n\n"
            f"STRICT INSTRUCTIONS for the 'title' field:\n"
            f"1. You MUST provide a descriptive title between 10 and 15 words. This is a hard constraint.\n"
            f"2. Format the title using this pattern: Subject + Place + Region + Distinguishing Feature.\n"
            f"3. Prefer exact place names (town + province) over broader regional naming unless the specific location is unknown.\n"
            f"4. Within that pattern, capture specific visual elements (textures, lighting, landmarks) and the Argentine cultural setting.\n"
            f"5. Example: 'Rustic Stone Architecture and Traditional Welsh Tea House in the Village of Gaiman Chubut'.\n\n"
            f"STRICT INSTRUCTIONS for the 'description' field:\n"
            f"1. The FIRST sentence MUST begin with the exact place name, province, and subject (e.g., 'Villa La Angostura, Neuquén: A white catamaran...').\n"
            f"2. Immediately follow with your vivid, sensory description of the subject and location. START immediately; NO AI INTROS or greetings.\n"
            f"3. Focus on the atmosphere, technical photography (lighting, depth of field), and cultural context.\n"
            f"4. Use a mix of complex and compound sentences to ensure the narrative feels professional and authoritative.\n"
            f"5. Include one concrete sentence near the end summarizing why this scene matters for travel, geography, culture, or regional identity (Search Intent Sentence).\n"
            f"6. DO NOT mention who is NOT in the photo. Only identify members of {TEAM} if they are physically visible in the image.\n"
            f"7. At the very end of the English description, add this exact sentence: 'This image is a collaborative production by {AUTHOR} and {PARTNER} for {PROJECT_NAME}.'\n"
            f"8. Provide ~10-12 high-quality sentences in English, then a '---' separator, then the exact Spanish translation.\n\n"
            f"STRICT INSTRUCTIONS for the 'tags' field:\n"
            f"1. Return EXACTLY 50 tags. Prioritize specific locations, regional geography, and cultural terms.\n"
            f"2. Use generic tags (e.g., 'Boat', 'Nature', 'Outdoor') ONLY if they are supported by stronger, primary geographic and subject-specific tags.\n"
            f"3. SAFETY: Avoid tags associated with nudity, voyeurism, or ambiguous terms that drift into unsafe categories.\n\n"
            f"STRICT INSTRUCTIONS for the 'json_ld' field:\n"
            f"1. You MUST return a valid schema where '@context' is 'https://schema.org' and '@type' is 'ImageObject'.\n"
            f"2. CRITICAL: DO NOT include a 'contentUrl' field at all in the JSON.\n"
            f"3. The 'creator' field MUST be an array containing TWO Person objects: one for 'Samuel Jeffery' and one for 'Audrey Bergner'.\n"
            f"4. Include 'sameAs': {json.dumps(SCHEMA_LINKS)} for both Person objects.\n\n"
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
                raw_text = ai_resp.text.strip()
                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_json = raw_text[start_idx:end_idx+1]
                    ai_data = json.loads(clean_json)
                    break
                else:
                    raise ValueError("No valid JSON structure found in AI response.") 
            except Exception as e:
                if "503" in str(e) or "high demand" in str(e):
                    wait_time = min((attempt + 1) * 20, 60) 
                    print_now(f"  ⚠️ Gemini overloaded. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print_now(f"  ❌ Fatal AI Error: {e}")
                    break 

        if ai_data and 'json_ld' in ai_data:
            ai_data['json_ld'].pop('contentUrl', None)
        
        required_keys = ['title', 'description', 'tags', 'json_ld']
        if not ai_data or not all(k in ai_data for k in required_keys):
            print_now(f"  ⚠️ Validation Failed for {img_id}. Missing core schema keys. Skipping.")
            time.sleep(10)
            continue

        core_fallback_tags = ["Argentina", "Travel Photography", "South America", "Wanderlust", "Travel", "Landscape", "Samuel Jeffery", "Audrey Bergner"]
        current_tags = ai_data.get('tags', [])
        if len(current_tags) < 50:
            needed = 50 - len(current_tags)
            padding = [t for t in core_fallback_tags if t not in current_tags][:needed]
            current_tags.extend(padding)
        elif len(current_tags) > 50:
            current_tags = current_tags[:50]
        ai_data['tags'] = current_tags

        sidecar_dir = "metadata_sidecars"
        os.makedirs(sidecar_dir, exist_ok=True)
        with open(os.path.join(sidecar_dir, f"{img_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, indent=4, ensure_ascii=False)
        print_now(f"  💾 Saved metadata sidecar for {img_id}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            temp.write(img_bytes)
            temp_path = temp.name

        flickr_desc = f"{ai_data['description']}{SITES_HTML}\n\nPhoto by {AUTHOR} & {PARTNER} | {PROJECT_NAME}"
        smug_caption = f"{ai_data['description']}{SITES_PLAIN}\n\nPhoto by {AUTHOR} & {PARTNER} | {PROJECT_NAME}"
        
        try:
            print_now(f"  📤 Uploading to Flickr: {ai_data['title'][:43]}...")
            
            # --- FLICKR RETRY LOOP ---
            for f_attempt in range(3):
                try:
                    up_resp = flickr.upload(filename=temp_path, title=ai_data['title'], description=flickr_desc, tags=" ".join([f'"{t}"' for t in ai_data['tags']]), is_public=1)
                    photo_id = up_resp.find('photoid').text
                    if not album_id:
                        album_id = get_or_create_flickr_album(official_album_name, primary_photo_id=photo_id)
                    elif photo_id:
                        flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
                    break  # Success! Break out of the retry loop.
                except Exception as f_err:
                    if f_attempt < 2:
                        print_now(f"  ⚠️ Flickr Error/Timeout. Retrying ({f_attempt+1}/3) in 10s...")
                        time.sleep(10)
                    else:
                        raise Exception(f"Flickr Upload Permanently Failed: {f_err}")
            # -------------------------
            
            print_now(f"  🔄 Updating SmugMug...")
            smug_payload = {"Title": ai_data['title'], "Caption": smug_caption, "Keywords": ",".join(ai_data['tags'])}
            smug_success = False
            for sm_attempt in range(3):
                patch_resp = requests.patch(f"https://api.smugmug.com{img_uri}", headers={"Accept": "application/json", "Content-Type": "application/json"}, auth=smug_auth, json=smug_payload)
                if patch_resp.status_code in [200, 201]:
                    smug_success = True
                    break
                elif patch_resp.status_code in [401, 503, 429]:
                    print_now(f"  ⚠️ SmugMug {patch_resp.status_code}. Retrying ({sm_attempt+1}/3) in 5s...")
                    time.sleep(5)
                else:
                    break
                    
            if smug_success:
                print_now(f"  🏆 SUCCESS!")
                save_history_atomic(img_id) 
                global_count += 1
            else:
                print_now(f"  ❌ SmugMug Update Permanently Failed after retries: {patch_resp.status_code}")

            sleep_time = random.uniform(30, 35)
            print_now(f"  ⏳ Respecting API: Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)
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
    
    # --- DYNAMIC LIMIT: 55 to 65 photos ---
    SESSION_LIMIT = random.randint(55, 65)
    print_now(f"✅ Initialization Complete. Target limit for this session: {SESSION_LIMIT} photos.")

    for custom_name, album_key in PRIORITY_MAP.items():
        if global_count >= SESSION_LIMIT: break

        print_now(f"⚡ Checking VIP Album: {custom_name} (Key: {album_key})")
        img_api = f"https://api.smugmug.com/api/v2/album/{album_key}!images?count=10000"
        img_resp = requests.get(img_api, headers=headers, auth=smug_auth).json()
        images = img_resp.get('Response', {}).get('AlbumImage', [])
        unprocessed = [i for i in images if i.get('ImageKey') not in processed_history]
        
        if not unprocessed:
            print_now(f"  ✅ {custom_name} is 100% complete. Moving to next VIP target...")
            continue

        print_now(f"  📂 Found {len(unprocessed)} photos remaining in {custom_name}. Processing...")
        # Pass the dynamic limit to the function
        global_count = process_album_images(unprocessed, custom_name, global_count, processed_history, SESSION_LIMIT)
        
        if global_count >= SESSION_LIMIT:
            print_now(f"🛑 Hit {SESSION_LIMIT}-photo limit while working on {custom_name}. Stopping to maintain focus.")
            return 

    if global_count >= SESSION_LIMIT:
        print_now(f"🛑 Global limit of {SESSION_LIMIT} photos reached. Ending session.")
    else:
        print_now("🏁 All albums in the PRIORITY_MAP have been 100% migrated.")

if __name__ == "__main__":
    run_migration()
