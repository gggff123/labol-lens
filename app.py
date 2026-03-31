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
# UPLOAD IMAGE TO POLLINATIONS
# -----------------------
def upload_image(image_bytes, filename, token):
    res = requests.post(
        "https://gen.pollinations.ai/image/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, image_bytes)}
    )
    if res.status_code == 200:
        data = res.json()
        # Returns hosted URL like https://media.pollinations.ai/c2b5a7ea1329cc6c
        return data.get("url")
    else:
        st.error(f"❌ Upload failed ({res.status_code}): {res.text}")
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
# STEP 1: RESOLVE IMAGE URL
# -----------------------
if describe_btn and token:
    auth_headers = {"Authorization": f"Bearer {token}"}
    hosted_url = None

    if uploaded_file:
        with st.spinner("⬆️ Uploading image to Pollinations..."):
            hosted_url = upload_image(uploaded_file.getvalue(), uploaded_file.name, token)
        if hosted_url:
            st.success(f"✅ Uploaded: {hosted_url}")

    elif pasted_url:
        # Use the pasted URL directly — if it's already a web URL Pollinations can fetch it
        hosted_url = pasted_url

    else:
        st.warning("⚠️ Please upload an image or paste a URL first.")
        st.stop()

    if hosted_url:
        # -----------------------
        # STEP 2: DESCRIBE
        # -----------------------
        with st.spinner("🧠 Describing image..."):
            prompt = "describe this image in detail"
            api_url = f"https://gen.pollinations.ai/text/{quote(prompt)}?model=gemini-fast&image={quote(hosted_url)}&key={APP_KEY}"
            res = requests.get(api_url, headers=auth_headers)

        if res.status_code != 200:
            st.error(f"❌ Description failed ({res.status_code}): {res.text}")
            st.stop()

        st.session_state["description"] = res.text
        st.session_state["hosted_url"] = hosted_url

# -----------------------
# SHOW DESCRIPTION + GENERATE
# -----------------------
if "description" in st.session_state:
    col1, col2 = st.columns(2)
    with col1:
        if "hosted_url" in st.session_state:
            st.image(st.session_state["hosted_url"], caption="Input Image")
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
