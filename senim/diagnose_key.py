"""One-file diagnostic for 'OPENROUTER_API_KEY' problems on Windows/Mac/Linux.

Run it with:  python diagnose_key.py
(from inside the senim/ folder — the one with requirements.txt in it)

Makes ONE free request to https://openrouter.ai/api/v1/key (does not spend any credits)
to check whether the key that .env loads is actually valid.
"""
import sys

try:
    from senim.config import settings
except ModuleNotFoundError:
    print("ERROR: could not import 'senim'.")
    print("You are probably in the wrong folder. cd to the folder that directly")
    print("contains requirements.txt and a 'senim' subfolder, then run this again.")
    sys.exit(1)

key = settings.openrouter_api_key
print("1) Key loaded from .env:")
print("   repr:", repr(key))
print("   length:", len(key))
if not key:
    print("\n=> EMPTY. Your .env file is not being read. Check:")
    print("   - the file is named exactly '.env' (not '.env.txt')")
    print("   - it sits in the same folder as this script")
    sys.exit(1)
if key != key.strip():
    print("\n=> The key has extra spaces/newlines around it — edit .env and remove them.")
    sys.exit(1)

print("\n2) Asking OpenRouter whether this key is valid (free check, no cost)...")
try:
    import httpx
except ModuleNotFoundError:
    print("ERROR: httpx is not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    r = httpx.get("https://openrouter.ai/api/v1/key",
                   headers={"Authorization": f"Bearer {key}"}, timeout=20)
except httpx.HTTPError as e:
    print(f"=> Could not reach openrouter.ai at all: {e}")
    print("   This points to your network/proxy/antivirus blocking the connection.")
    sys.exit(1)

print("   HTTP status:", r.status_code)
print("   Response:", r.text[:300])

if r.status_code == 200:
    print("\n=> KEY IS VALID. If SENIM still fails, the problem is elsewhere — send me this whole output.")
else:
    print("\n=> OpenRouter rejected this key. Get a fresh one at https://openrouter.ai/keys")
    print("   and paste ONLY the key (no quotes, no spaces) into OPENROUTER_API_KEY= in .env.")
