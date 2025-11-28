import json
from getpass import getpass
from pathlib import Path
from werkzeug.security import generate_password_hash

INSTANCE = Path(__file__).resolve().parent / "instance"
USERS = INSTANCE / "users.json"
INSTANCE.mkdir(parents=True, exist_ok=True)

def load_users():
    if not USERS.exists():
        return {}
    return json.loads(USERS.read_text())

def save_users(u):
    USERS.write_text(json.dumps(u, indent=2))

def main():
    users = load_users()
    uid = str(len(users)+1)
    username = input("Admin username: ").strip()
    pw = getpass("Password: ")
    pw2 = getpass("Confirm: ")
    if pw != pw2:
        print("Passwords do not match")
        return
    users[uid] = {"username": username, "pw_hash": generate_password_hash(pw)}
    save_users(users)
    print("Admin user created.")

if __name__ == "__main__":
    main()

