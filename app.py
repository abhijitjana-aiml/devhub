import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = APP_DIR / "instance"
DATA_DIR = APP_DIR / "data"
USERS_FILE = INSTANCE_DIR / "users.json"
CREDS_FILE = DATA_DIR / "credentials.enc"
KEY_FILE = INSTANCE_DIR / "secret.key"

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
# Secret key for session signing
if not (INSTANCE_DIR / "flask_secret.txt").exists():
    (INSTANCE_DIR / "flask_secret.txt").write_text(os.urandom(24).hex())
app.secret_key = (INSTANCE_DIR / "flask_secret.txt").read_text()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Simple User class
class User(UserMixin):
    def __init__(self, id_, username, pw_hash):
        self.id = id_
        self.username = username
        self.pw_hash = pw_hash

def load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text())

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2))

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    for uid, u in users.items():
        if uid == user_id:
            return User(uid, u["username"], u["pw_hash"])
    return None

def ensure_key():
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    return Fernet(KEY_FILE.read_bytes())

def encrypt_data(obj):
    f = ensure_key()
    plaintext = json.dumps(obj).encode()
    return f.encrypt(plaintext)

def decrypt_data(token):
    if not CREDS_FILE.exists():
        return []
    f = ensure_key()
    try:
        plaintext = f.decrypt(CREDS_FILE.read_bytes())
        return json.loads(plaintext)
    except Exception:
        return []

@app.route("/")
@login_required
def index():
    return render_template("dashboard.html", user=current_user.username)

@app.route("/projects")
@login_required
def projects():
    # simple example, you can extend to read from DB or markdown
    projects = [
        {"name":"HDD Cleaner", "github":"https://github.com/YOUR_USER/hdd_cleaner", "notes":"File cleanup + clustering"},
        {"name":"DevHub", "github":"https://github.com/YOUR_USER/devhub", "notes":"This dashboard"}
    ]
    return render_template("projects.html", projects=projects)

@app.route("/apps")
@login_required
def apps():
    apps = [
        {"name":"Nextcloud", "url":"http://100.x.x.x:8080", "notes":"Nextcloud on server"},
    ]
    return render_template("apps.html", apps=apps)

@app.route("/creds", methods=["GET","POST"])
@login_required
def creds():
    if request.method == "POST":
        name = request.form.get("name")
        user = request.form.get("username")
        pwd = request.form.get("password")
        url = request.form.get("url")
        entries = decrypt_data([])
        entries.append({"name":name,"username":user,"password":pwd,"url":url})
        ENC = encrypt_data(entries)
        CREDS_FILE.write_bytes(ENC)
        flash("Credential added (encrypted).", "success")
        return redirect(url_for("creds"))
    entries = decrypt_data([])  # returns list of dicts
    # do NOT show password in plaintext. we will render masked values.
    for e in entries:
        e["password_masked"] = "●●●●●●"
    return render_template("creds.html", entries=entries)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        for uid, u in users.items():
            if u["username"] == username:
                if check_password_hash(u["pw_hash"], password):
                    user = User(uid, u["username"], u["pw_hash"])
                    login_user(user)
                    return redirect(url_for("index"))
                else:
                    flash("Invalid credentials", "danger")
                    break
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Simple CLI helper endpoints for dev (disabled in production)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
