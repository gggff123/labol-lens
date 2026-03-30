import requests
import streamlit as st
import time
import os

st.title("🔍 Image Gen Search (BYOP)")
st.write("Upload an image → AI describes it → generates a new one")

APP_KEY = "pk_yourkey"  # optional but recommended
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

im_inp = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
btn = st.button("Generate")

# -----------------------
# MAIN LOGIC
# -----------------------
if im_inp and btn and token:

    # Convert image to bytes
    files = {"file": im_inp.getvalue()}

    # Step 1: Image → Text
    res = requests.post(
        "https://gen.pollinations.ai/text/describe?model=polly",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )

    description = res.text
    st.write("🧠 Description:", description)

    # Step 2: Text → Image
    img_res = requests.get(
        f"https://gen.pollinations.ai/image/{description}",
        params={
            "model": "flux",
            "width": 1024,
            "height": 1024,
            "seed": 0
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Display image correctly
    st.image(img_res.content)
