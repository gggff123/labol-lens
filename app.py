import streamlit as st
st.title('Labol Lens')
Text_input=st.file_uploader('upload image',['.png','.jpg','.webp','.jpeg'])
btn=st.button('generate')
import requests
import random
key=st.text_input('Enter your api key : ')
genre=['Horror','Peacefull','Sci-Fi','Cartoon','Film']
random_genre=random.choice(genre)
if key is None:
    st.error('NO API KEY PROVIDED')
if btn:
    if Text_input is not None:
        files = {"file": Text_input.getvalue()}

        res = requests.post(
            f"https://media.pollinations.ai/upload?key={key}",
            files={"file": ("image.jpg", Text_input.getvalue())}
        )

        a=res.json()
        img_url=a['url']
    else:
        st.warning("Please upload an image first")
    #generate variations
    img=f'https://gen.pollinations.ai/image/{random_genre}?model=qwen-image&width=1024&height=1024&seed=0&enhance=false&image={img_url}&key={key}'
    img_gen=requests.get(img)
    st.image(img_gen.content)
    st.toast('Generated succesfully!')
