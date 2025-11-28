from pathlib import Path
import json
from cryptography.fernet import Fernet
from getpass import getpass

APP_DIR = Path(__file__).resolve().parent
KEY_FILE = APP_DIR / "instance" / "secret.key"
CREDS_FILE = APP_DIR / "data" / "credentials.enc"
KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)

if not KEY_FILE.exists():
    KEY_FILE.write_bytes(Fernet.generate_key())

f = Fernet(KEY_FILE.read_bytes())
if CREDS_FILE.exists():
    data = json.loads(f.decrypt(CREDS_FILE.read_bytes()))
else:
    data = []

name = input("Name: ")
username = input("Username: ")
password = getpass("Password: ")
url = input("URL: ")

data.append({"name":name,"username":username,"password":password,"url":url})
CREDS_FILE.write_bytes(f.encrypt(json.dumps(data).encode()))
print("Credential saved (encrypted).")
