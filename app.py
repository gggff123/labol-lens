import requests
import streamlit as st
import time
import os
import base64
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

# Two input modes
tab1, tab2 = st.tabs(["📁 Upload Image", "🔗 Paste URL"])

with tab1:
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])

with tab2:
    pasted_url = st.text_input("🔗 Paste image URL", placeholder="https://example.com/image.jpg")

describe_btn = st.button("🧠 Describe Image")

# -----------------------
# STEP 1: RESOLVE IMAGE
# -----------------------
if describe_btn and token:
    auth_headers = {"Authorization": f"Bearer {token}"}
    image_param = None
    preview_image = None

    if uploaded_file:
        # Convert to base64 data URL — no upload endpoint needed
        mime = uploaded_file.type  # e.g. image/jpeg
        b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        image_param = f"data:{mime};base64,{b64}"
        preview_image = uploaded_file.getvalue()

    elif pasted_url:
        image_param = pasted_url
        preview_image = pasted_url

    else:
        st.warning("⚠️ Please upload an image or paste a URL first.")
        st.stop()

    # -----------------------
    # STEP 2: DESCRIBE
    # -----------------------
    with st.spinner("🧠 Describing image..."):
        prompt = "describe this image in detail"
        api_url = f"https://gen.pollinations.ai/text/{quote(prompt)}?model=gemini-fast&image={quote(image_param)}&key={APP_KEY}"
        res = requests.get(api_url, headers=auth_headers)

    if res.status_code != 200:
        st.error(f"❌ Description failed ({res.status_code}): {res.text}")
        st.stop()

    st.session_state["description"] = res.text
    st.session_state["preview_image"] = preview_image

# -----------------------
# SHOW DESCRIPTION + GENERATE
# -----------------------
if "description" in st.session_state:
    col1, col2 = st.columns(2)
    with col1:
        st.image(st.session_state["preview_image"], caption="Input Image")
    with col2:
        st.write("🧠 **Description:**")
        st.write(st.session_state["description"])

    st.divider()

    if st.button("🎨 Generate Image") and token:
        auth_headers = {"Authorization": f"Bearer {token}"}

        with st.spinner("🎨 Generating image..."):
            img_res = requests.get(
                f"https://gen.pollinations.ai/image/{quote(st.session_state['description'])}",
                params={
                    "model": "flux",
                    "width": 1024,
                    "height": 1024,
                    "seed": 0,
                },
                headers=auth_headers
            )

        content_type = img_res.headers.get("Content-Type", "")
        if img_res.status_code != 200 or "image" not in content_type:
            st.error(f"❌ Image generation failed ({img_res.status_code}): {img_res.text}")
            st.stop()

        st.image(img_res.content, caption="✨ Generated Image")
