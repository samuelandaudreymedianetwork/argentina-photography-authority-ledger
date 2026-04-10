import os, json, re, time, sys, requests
from requests_oauthlib import OAuth1

def print_now(text):
    print(text)
    sys.stdout.flush()

# ==========================================
# 1. CREDENTIALS
# ==========================================
FLICKR_KEY = "06aa8cc8653cdd5cbc6c8a7a3d621058"
FLICKR_SECRET = "c1b8cf911586f6f0"
FLICKR_TOKEN = "72157720965124247-f3ab3bc8c4250322"
FLICKR_TOKEN_SECRET = "d20d2c984ea2603f"

SESSION_LIMIT = 150
HISTORY_FILE = "scrub_history.json"
SCHEMA_PATTERN = re.compile(r'(<script type="application/ld\+json">)?\s*(\{"@context":\s*"https://schema\.org".*?\})\s*(</script>)?', re.DOTALL)

auth = OAuth1(FLICKR_KEY, FLICKR_SECRET, FLICKR_TOKEN, FLICKR_TOKEN_SECRET)

def flickr_api_call(method, params=None):
    url = "https://www.flickr.com/services/rest"
    base_params = {"method": method, "api_key": FLICKR_KEY, "format": "json", "nojsoncallback": 1}
    if params: base_params.update(params)
    resp = requests.get(url, params=base_params, auth=auth)
    return resp.json()

def flickr_post_call(method, params=None):
    url = "https://www.flickr.com/services/rest"
    base_params = {"method": method, "api_key": FLICKR_KEY, "format": "json", "nojsoncallback": 1}
    if params: base_params.update(params)
    resp = requests.post(url, data=base_params, auth=auth)
    return resp.json()

def run_session():
    # --- AUTO-IDENTITY CHECK ---
    print_now("🔍 Verifying Identity...")
    login_test = flickr_api_call("flickr.test.login")
    
    if login_test.get('stat') != 'ok':
        print_now(f"❌ AUTH FAIL: {login_test.get('message')}")
        return

    # Automatically grab the ID from the token owner
    ACTUAL_USER_ID = login_test.get('user', {}).get('id')
    USERNAME = login_test.get('user', {}).get('username', {}).get('_content')
    print_now(f"✅ Authenticated as: {USERNAME} ({ACTUAL_USER_ID})")

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    with open(HISTORY_FILE, 'r') as f:
        try: history = json.load(f)
        except: history = []

    print_now(f"📡 Pinging photostream for {ACTUAL_USER_ID}...")
    processed_count = 0
    page_number = 1
    
    while processed_count < SESSION_LIMIT:
        data = flickr_api_call("flickr.people.getPhotos", {"user_id": ACTUAL_USER_ID, "per_page": 500, "page": page_number})
        
        if data.get('stat') != 'ok':
            print_now(f"❌ API Error: {data.get('message')}")
            break

        photos = data['photos']['photo']
        if not photos: break

        for p in photos:
            if processed_count >= SESSION_LIMIT: break
            fid = p['id']
            if fid in history: continue

            try:
                info_data = flickr_api_call("flickr.photos.getInfo", {"photo_id": fid})
                photo_info = info_data.get('photo', {})
                desc = photo_info.get('description', {}).get('_content', '')
                title = photo_info.get('title', {}).get('_content', '')

                if '{"@context": "https://schema.org"' in desc:
                    clean_desc = SCHEMA_PATTERN.sub('', desc).strip()
                    update_data = flickr_post_call("flickr.photos.setMeta", {"photo_id": fid, "title": title, "description": clean_desc})
                    if update_data.get('stat') == 'ok': 
                        print_now(f"✅ CLEANED: {fid}")
                    else:
                        print_now(f"⚠️ Failed {fid}: {update_data.get('message')}")
                else:
                    print_now(f"⏩ VERIFIED: {fid}")

                history.append(fid)
                processed_count += 1
                time.sleep(1.2)
            except Exception as e:
                print_now(f"❌ Error on {fid}: {e}")

        page_number += 1

    with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=4)
    print_now(f"🏁 Session complete. Total historic photos verified: {len(history)}")

if __name__ == "__main__":
    run_session()
