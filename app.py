import requests
import streamlit as st
import time
import os
from urllib.parse import quote

st.title("🔍 Image Gen Search (BYOP)")
st.write("Upload or paste an image URL → AI describes it → generates a new one")

APP_KEY = "pk_yourkey"
TOKEN_FILE = "token.txt"

# -----------------------
# 🔐 BYOP LOGIN
# -----------------------
def login():
    res = requests.post(
        "https://enter.pollinations.ai/api/device/code",
        json={"client_id": APP_KEY, "scope": "generate"}
    )
    data = res.json()
    device_code = data["device_code"]
    user_code = data["user_code"]
    st.info(f"Go to https://enter.pollinations.ai/device and enter code: {user_code}")
    token = None
    with st.spinner("Waiting for login..."):
        while True:
            res = requests.post(
                "https://enter.pollinations.ai/api/device/token",
                json={"device_code": device_code}
            )
            data = res.json()
            if "access_token" in data:
                token = data["access_token"]
                st.success("✅ Logged in!")
                break
            elif data.get("error") == "authorization_pending":
                time.sleep(5)
            else:
                st.error(data)
                return None
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    return token

# -----------------------
# 🔑 LOAD TOKEN
# -----------------------
def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    return None

# -----------------------
# DESCRIBE via URL (GET)
# -----------------------
def describe_from_url(url, token):
    prompt = "describe this image in detail"
    api_url = f"https://gen.pollinations.ai/text/{quote(prompt)}?model=gemini-fast&image={quote(url)}&key={APP_KEY}"
    return requests.get(api_url, headers={"Authorization": f"Bearer {token}"})

# -----------------------
# DESCRIBE via file upload (POST)
# -----------------------
def describe_from_file(image_bytes, filename, mime_type, token):
    prompt = "describe this image in detail"
    api_url = f"https://gen.pollinations.ai/text/{quote(prompt)}?model=gemini-fast&key={APP_KEY}"
    return requests.post(
        api_url,
        headers={"Authorization": f"Bearer {token}"},
        files={"image": (filename, image_bytes, mime_type)}
    )

# -----------------------
# UI
# -----------------------
token = get_token()

if not token:
    if st.button("🔑 Login with Pollinations"):
        token = login()
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success("Using saved login ✅")
    with col2:
        if st.button("🗑️ Clear API Key"):
            os.remove(TOKEN_FILE)
            st.info("API key cleared. Please log in again.")
            st.rerun()

tab1, tab2 = st.tabs(["📁 Upload Image", "🔗 Paste URL"])

with tab1:
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

with tab2:
    pasted_url = st.text_input("🔗 Paste image URL", placeholder="https://example.com/image.jpg")

describe_btn = st.button("🧠 Describe Image")

# -----------------------
# STEP 1: DESCRIBE
# -----------------------
if describe_btn and token:
    res = None

    if uploaded_file:
        with st.spinner("🧠 Describing image..."):
            res = describe_from_file(
                uploaded_file.getvalue(),
                uploaded_file.name,
                uploaded_file.type,
                token
            )
        preview = uploaded_file.getvalue()

    elif pasted_url:
        with st.spinner("🧠 Describing image..."):
            res = describe_from_url(pasted_url, token)
        preview = pasted_url

    else:
        st.warning("⚠️ Please upload an image or paste a URL first.")
        st.stop()

    if res.status_code != 200:
        st.error(f"❌ Description failed ({res.status_code}): {res.text}")
        st.stop()

    st.session_state["description"] = res.text
    st.session_state["preview"] = preview

# -----------------------
# SHOW DESCRIPTION + GENERATE
# -----------------------
if "description" in st.session_state:
    col1, col2 = st.columns(2)
    with col1:
        st.image(st.session_state["preview"], caption="Input Image")
    with col2:
        st.write("🧠 **Description:**")
        st.write(st.session_state["description"])

    st.divider()

    if st.button("🎨 Generate Image") and token:
        with st.spinner("🎨 Generating image..."):
            img_res = requests.get(
                f"https://gen.pollinations.ai/image/{quote(st.session_state['description'])}",
                params={"model": "flux", "width": 1024, "height": 1024, "seed": 0},
                headers={"Authorization": f"Bearer {token}"}
            )

        content_type = img_res.headers.get("Content-Type", "")
        if img_res.status_code != 200 or "image" not in content_type:
            st.error(f"❌ Image generation failed ({img_res.status_code}): {img_res.text}")
            st.stop()

        st.image(img_res.content, caption="✨ Generated Image")
