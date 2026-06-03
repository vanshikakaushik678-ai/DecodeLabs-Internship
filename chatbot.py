import streamlit as st
from google import genai
import uuid
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import hashlib

# =========================
# AI CONFIG
# =========================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# ✅ FIXED MODEL (WORKING FROM YOUR LIST)
MODEL = "models/gemini-2.0-flash"

# =========================
# PASSWORD HASH (SECURITY FIX 🔐)
# =========================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# =========================
# FAILSAFE AI ENGINE (SAFE VERSION 🔥)
# =========================
def safe_ai(client, model, user_input):

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_input
        )
        return response.text

    except Exception as e:

        error = str(e).lower()

        if "quota" in error or "429" in error or "resource_exhausted" in error:

            text = user_input.lower()

            if "hello" in text or "hi" in text:
                return "👋 Hello! I am your offline AI assistant (Gemini limit reached)."

            elif "your name" in text:
                return "🤖 I am SaaS Failsafe AI (Offline Mode)."

            elif "what is ai" in text:
                return "AI means Artificial Intelligence — machines that simulate human thinking."

            elif "python" in text:
                return "Python is a programming language used for AI, automation and web apps."

            elif "time" in text:
                return f"⏰ Current time is {datetime.now().strftime('%H:%M:%S')}"

            elif any(op in text for op in ["+", "-", "*", "/"]):
                try:
                    return "🧮 Math feature disabled for security reasons."
                except:
                    return "❌ Invalid math expression"

            else:
                return (
                    "⚠️ AI quota finished right now.\n\n"
                    "But I am running in OFFLINE MODE 🤖\n"
                    "Ask simple questions."
                )

        return "⚠️ Something went wrong, but AI is still running safely."

# =========================
# LOCAL DB FILE (SAAS STORAGE)
# =========================
DB_FILE = "saas_db.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "current_chat" not in st.session_state:
    st.session_state.current_chat = str(uuid.uuid4())

# =========================
# LOGIN SYSTEM (SECURE VERSION 🔐)
# =========================
def login():
    st.title("🔐 AI SaaS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login / Signup"):
        db = load_db()

        hashed_pw = hash_password(password)

        if username not in db:
            db[username] = {
                "password": hashed_pw,
                "chats": {}
            }
            save_db(db)

        if db[username]["password"] == hashed_pw:
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Wrong password ❌")

# =========================
# LOAD USER DATA
# =========================
def get_user_data():
    db = load_db()
    user = st.session_state.user
    return db[user]

def update_user_data(data):
    db = load_db()
    user = st.session_state.user
    db[user] = data
    save_db(db)

# =========================
# APP START
# =========================
if st.session_state.user is None:
    login()
    st.stop()

user = st.session_state.user
user_data = get_user_data()

if not user_data["chats"]:
    chat_id = str(uuid.uuid4())
    user_data["chats"][chat_id] = []
    update_user_data(user_data)

if st.session_state.current_chat not in user_data["chats"]:
    st.session_state.current_chat = list(user_data["chats"].keys())[0]

# =========================
# SIDEBAR
# =========================
st.sidebar.title(f"👤 {user}")

if st.sidebar.button("➕ New Chat"):
    new_id = str(uuid.uuid4())
    user_data["chats"][new_id] = []
    st.session_state.current_chat = new_id
    update_user_data(user_data)
    st.rerun()

st.sidebar.markdown("---")

for chat_id in user_data["chats"].keys():

    col1, col2 = st.sidebar.columns([0.8, 0.2])

    if col1.button(chat_id[:6], key=chat_id):
        st.session_state.current_chat = chat_id
        st.rerun()

    if col2.button("🗑", key=f"del_{chat_id}"):
        del user_data["chats"][chat_id]
        update_user_data(user_data)
        st.rerun()

if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()

# =========================
# MAIN UI
# =========================
st.title("🤖 SaaS ChatGPT Clone (Production MVP)")

chat_id = st.session_state.current_chat
messages = user_data["chats"][chat_id]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask anything...")

if user_input:

    messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking 🤖..."):
            reply = safe_ai(client, MODEL, user_input)
            st.markdown(reply)

    messages.append({"role": "assistant", "content": reply})

    user_data["chats"][chat_id] = messages
    update_user_data(user_data)