import sqlite3
import json
import time
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, status
from pydantic import BaseModel
import passlib.hash as _hash

# --- CONFIGURACIÓN Y CONSTANTES ---
SECRET_KEY = "[ENCRYPTION_KEY]"
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30
DB_PATH = "lbsb_server.db"

app = FastAPI(title="ChacalitosTCG - Auth & Sync API")

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_data TEXT DEFAULT '{}',
            last_synced REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- MODELOS DE DATOS ---
class UserAuth(BaseModel):
    username: str
    password: str

class ProfileSyncPayload(BaseModel):
    profile_data: dict

# --- HELPER DE AUTENTICACIÓN ---
def create_access_token(user_id: int, username: str) -> str:
    expires = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "username": username, "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

# --- ENDPOINTS ---

@app.post("/api/register")
def register(user: UserAuth):
    username_clean = user.username.strip().lower()
    if len(username_clean) < 3 or len(user.password) < 4:
        raise HTTPException(status_code=400, detail="Usuario o contraseña demasiado cortos")

    hashed_pw = _hash.bcrypt.hash(user.password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, last_synced) VALUES (?, ?, ?)",
            (username_clean, hashed_pw, time.time())
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    conn.close()
    token = create_access_token(user_id, username_clean)
    return {"status": "success", "token": token, "user_id": user_id, "username": username_clean}


@app.post("/api/login")
def login(user: UserAuth):
    username_clean = user.username.strip().lower()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username_clean,))
    row = cursor.fetchone()
    conn.close()

    if not row or not _hash.bcrypt.verify(user.password, row[1]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    user_id = row[0]
    token = create_access_token(user_id, username_clean)
    return {"status": "success", "token": token, "user_id": user_id, "username": username_clean}


@app.get("/api/sync")
def pull_profile(user_id: int = Depends(get_current_user_id)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_data, last_synced FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    raw_json, last_synced = row
    profile_dict = json.loads(raw_json) if raw_json else {}
    return {"profile_data": profile_dict, "last_synced": last_synced}


@app.post("/api/sync")
def push_profile(payload: ProfileSyncPayload, user_id: int = Depends(get_current_user_id)):
    now = time.time()
    json_str = json.dumps(payload.profile_data, ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET profile_data = ?, last_synced = ? WHERE id = ?",
        (json_str, now, user_id)
    )
    conn.commit()
    conn.close()

    return {"status": "synced", "last_synced": now}