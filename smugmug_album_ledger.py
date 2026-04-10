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
    "Llao Llao Hotel: Alpine Luxury & Family Travel in Bariloche, Patagonia": "rnmm72",
    "Buenos Aires, Argentina: A Visual Ledger of Family Visits": "B8h5q7",
    "El Bolsón: A Perfect Week With Friends + Exploring The Surrounding Area": "jrGXgp",
    "El Maitén: La Trochita Old Patagonian Express (Epic Historical Train Ride)": "NHFHzw",
    "El Chalten to El Calafate to Puerto Natales (Argentina to Chile Border Crossing)": "xdGpN7",
    "Punta Arenas To Ushuaia Transportation by Bus and Ferry (Chile to Argentina Border Crossing)": "LSv63z",
    "Best Pizza In Buenos Aires Challenge Along Avenida Corrientes": "JhtCHn",
    "Río Gallegos: Museums, Food and Dinosaurs as a Stopover in Santa Cruz, Southern Patagonia": "Lrdhvz"
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
