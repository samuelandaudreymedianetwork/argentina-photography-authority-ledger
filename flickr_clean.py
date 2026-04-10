import os, json, re, time, sys
import flickrapi

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

# Your specific Flickr NSID for Samuel and Audrey
USER_ID = "53072213@N05" 

SESSION_LIMIT = 150
HISTORY_FILE = "scrub_history.json"
SCHEMA_PATTERN = re.compile(r'(<script type="application/ld\+json">)?\s*(\{"@context":\s*"https://schema\.org".*?\})\s*(</script>)?', re.DOTALL)

# ==========================================
# 2. AUTHENTICATION
# ==========================================
flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='parsed-json')
flickr.token_cache.token = flickrapi.auth.FlickrAccessToken(
    token=FLICKR_TOKEN, 
    token_secret=FLICKR_TOKEN_SECRET, 
    access_level='write'
)

def run_session():
    if not os.path.exists(HISTORY_FILE):
        print_now(f"🆕 Creating new history file: {HISTORY_FILE}")
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)
    
    with open(HISTORY_FILE, 'r') as f:
        try:
            history = json.load(f)
        except:
            history = []

    print_now(f"📡 Pinging Flickr for photostream (User: {USER_ID})...")
    processed_count = 0
    page_number = 1
    
    while processed_count < SESSION_LIMIT:
        # Using the actual USER_ID instead of "me" to avoid the 'Unknown User' error
        resp = flickr.people.getPhotos(user_id=USER_ID, per_page=500, page=page_number)
        
        if resp['stat'] != 'ok':
            print_now(f"❌ Flickr API Error: {resp.get('message')}")
            break

        photos = resp['photos']['photo']
        if not photos: 
            print_now("🏁 No more photos found.")
            break

        for p in photos:
            if processed_count >= SESSION_LIMIT: break
            fid = p['id']
            if fid in history: continue

            try:
                info = flickr.photos.getInfo(photo_id=fid)
                desc = info['photo']['description']['_content']
                title = info['photo']['title']['_content']

                if '{"@context": "https://schema.org"' in desc:
                    clean_desc = SCHEMA_PATTERN.sub('', desc).strip()
                    flickr.photos.setMeta(photo_id=fid, title=title, description=clean_desc)
                    print_now(f"✅ CLEANED: {fid}")
                else:
                    print_now(f"⏩ VERIFIED: {fid}")

                history.append(fid)
                processed_count += 1
                time.sleep(1.2)

            except Exception as e:
                print_now(f"❌ Error on {fid}: {e}")

        page_number += 1

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    print_now(f"🏁 Session complete. Total verified/cleaned: {len(history)}")

if __name__ == "__main__":
    run_session()
