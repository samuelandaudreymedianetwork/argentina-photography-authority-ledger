import os, json, re, time, sys
import flickrapi

# Force logs to show immediately in GitHub Actions
def print_now(text):
    print(text)
    sys.stdout.flush()

# ==========================================
# 1. CREDENTIALS & CONFIG
# ==========================================
FLICKR_KEY = "06aa8cc8653cdd5cbc6c8a7a3d621058"
FLICKR_SECRET = "c1b8cf911586f6f0"
FLICKR_TOKEN = "72157720965124247-f3ab3bc8c4250322"
FLICKR_TOKEN_SECRET = "d20d2c984ea2603f"

SESSION_LIMIT = 150
HISTORY_FILE = "scrub_history.json"

# Surgical regex to find and remove the JSON-LD block
SCHEMA_PATTERN = re.compile(
    r'(<script type="application/ld\+json">)?\s*(\{"@context":\s*"https://schema\.org".*?\})\s*(</script>)?', 
    re.DOTALL
)

# ==========================================
# 2. AUTHENTICATION
# ==========================================
flickr = flickrapi.FlickrAPI(
    FLICKR_KEY, FLICKR_SECRET,
    token=FLICKR_TOKEN, 
    token_secret=FLICKR_TOKEN_SECRET,
    format='parsed-json'
)

def run_session():
    # Load or create history file to track progress across 14,000 photos
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    with open(HISTORY_FILE, 'r') as f: history = json.load(f)

    print_now("📡 Pinging Flickr for photostream...")
    
    processed_count = 0
    page_number = 1
    
    # Logic: Loop through photostream pages until 150 new photos are processed
    while processed_count < SESSION_LIMIT:
        print_now(f"🔍 Scanning Photostream Page {page_number}...")
        resp = flickr.people.getPhotos(user_id="me", per_page=500, page=page_number)
        photos = resp['photos']['photo']
        
        if not photos:
            print_now("🏁 Reached the end of the photostream.")
            break

        for p in photos:
            if processed_count >= SESSION_LIMIT: break
            
            fid = p['id']
            if fid in history:
                continue

            try:
                # Fetch full description for the photo
                info = flickr.photos.getInfo(photo_id=fid)
                desc = info['photo']['description']['_content']
                title = info['photo']['title']['_content']

                # Strip schema if found, leave the rest of the description untouched
                if '{"@context": "https://schema.org"' in desc:
                    clean_desc = SCHEMA_PATTERN.sub('', desc).strip()
                    flickr.photos.setMeta(photo_id=fid, title=title, description=clean_desc)
                    print_now(f"✅ CLEANED: {fid}")
                else:
                    print_now(f"⏩ VERIFIED: {fid}")

                history.append(fid)
                processed_count += 1
                time.sleep(1.2) # Polite API throttle

            except Exception as e:
                print_now(f"❌ Error on {fid}: {e}")

        page_number += 1

    # Save the updated history so the next 2-hour session starts where we left off
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    print_now(f"🏁 Session complete. Total historic photos verified/cleaned: {len(history)}")

if __name__ == "__main__":
    run_session()
