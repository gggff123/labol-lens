import requests
import streamlit as st
import time
import os
from urllib.parse import quote

st.title("🔍 Image Gen Search (BYOP)")
st.write("Paste an image URL → AI describes it → generates a new one")

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
    st.success("Using saved login ✅")

image_url = st.text_input("🔗 Paste image URL", placeholder="https://example.com/image.jpg")
btn = st.button("Generate")

# -----------------------
# MAIN LOGIC
# -----------------------
if image_url and btn and token:
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Image → Text
    with st.spinner("🧠 Describing image..."):
        res = requests.get(
            "https://gen.pollinations.ai/text/describe this image in detail",
            params={
                "model": "gemini-fast",
                "image": image_url,
            },
            headers=auth_headers
        )

    # Check for auth or API error before proceeding
    if res.status_code != 200:
        st.error(f"❌ Description failed ({res.status_code}): {res.text}")
        st.stop()

    description = res.text
    st.write("🧠 Description:", description)

    # Step 2: Text → Image
    with st.spinner("🎨 Generating image..."):
        img_res = requests.get(
            f"https://gen.pollinations.ai/image/{quote(description)}",
            params={
                "model": "flux",
                "width": 1024,
                "height": 1024,
                "seed": 0,
            },
            headers=auth_headers
        )

    # Check response is actually an image before rendering
    content_type = img_res.headers.get("Content-Type", "")
    if img_res.status_code != 200 or "image" not in content_type:
        st.error(f"❌ Image generation failed ({img_res.status_code}): {img_res.text}")
        st.stop()

    st.image(img_res.content)
