import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# FUNGSI STEGANOGRAFI LSB
def encode_message(img, message):
    message += "<END>"  # penanda akhir pesan
    binary_msg = ''.join(format(ord(c), '08b') for c in message)

    # Pastikan gambar RGB
    img = img.convert("RGB")
    img_arr = np.array(img, dtype=np.uint8)
    flat = img_arr.flatten()

    if len(binary_msg) > len(flat):
        raise ValueError("Pesan terlalu panjang untuk gambar ini!")

    for i in range(len(binary_msg)):
        # LSB safe: pastikan tetap uint8
        flat[i] = np.uint8((flat[i] & 0b11111110) | int(binary_msg[i]))

    encoded = flat.reshape(img_arr.shape)
    return Image.fromarray(encoded, 'RGB')

def decode_message(img):
    img = img.convert("RGB")
    img_arr = np.array(img, dtype=np.uint8)
    flat = img_arr.flatten()

    bits = [str(pixel & 1) for pixel in flat]
    chars = []

    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(''.join(byte), 2))
        chars.append(char)
        if ''.join(chars).endswith("<END>"):
            return ''.join(chars).replace("<END>", "")

    return ""


# FUNGSI WATERMARK
def apply_watermark(image, text, font_size, color, position):
    img = image.copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Hitung ukuran teks dengan textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Tentukan posisi watermark
    if position == "Top-Left":
        pos = (10, 10)
    elif position == "Top-Right":
        pos = (img.width - text_w - 10, 10)
    elif position == "Bottom-Left":
        pos = (10, img.height - text_h - 10)
    else:  # Bottom-Right
        pos = (img.width - text_w - 10, img.height - text_h - 10)

    draw.text(pos, text, fill=color, font=font)
    return img


# STREAMLIT MINI APP
st.set_page_config(page_title="Mini Apps - Stego & Watermark", layout="wide")

st.title("🖼️ MINI APPS — Steganografi & Watermark")

tab1, tab2 = st.tabs(["🔐 Steganografi", "💧 Watermark"])


# TAB 1 — STEGANOGRAFI
with tab1:
    st.subheader("🔐 Steganografi — LSB Encoding")

    upload_stego = st.file_uploader("Upload gambar untuk disisipi pesan:", type=["png", "jpg", "jpeg"])

    if upload_stego:
        img = Image.open(upload_stego).convert("RGB")
        st.image(img, caption="Gambar Original", use_container_width=True)

        secret = st.text_input("Masukkan Pesan Rahasia:")

        if st.button("🔒 Embed Pesan"):
            if secret.strip() == "":
                st.error("Pesan tidak boleh kosong!")
            else:
                try:
                    encoded_img = encode_message(img, secret)
                    st.success("Pesan berhasil disisipkan!")
                    st.image(encoded_img, caption="Gambar Berisi Pesan", use_container_width=True)

                    buf = io.BytesIO()
                    encoded_img.save(buf, format="PNG")

                    st.download_button(
                        label="⬇️ Download Gambar Berpesan",
                        data=buf.getvalue(),
                        file_name="stego_image.png",
                        mime="image/png"
                    )

                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.subheader("🔍 Extract Pesan dari Gambar")

    uploaded_decode = st.file_uploader("Upload gambar yang mengandung pesan:", type=["png", "jpg", "jpeg"], key="decode")

    if uploaded_decode:
        img2 = Image.open(uploaded_decode).convert("RGB")

        if st.button("🔎 Extract Pesan"):
            message = decode_message(img2)
            if message:
                st.success("Pesan ditemukan!")
                st.text_area("Pesan Rahasia:", message)
            else:
                st.warning("Tidak ditemukan pesan atau gambar tidak mengandung data steganografi.")


# TAB 2 — WATERMARK
with tab2:
    st.subheader("💧 Watermark Image")

    wm_file = st.file_uploader("Upload Gambar:", type=["png", "jpg", "jpeg"])

    if wm_file:
        img = Image.open(wm_file).convert("RGB")
        st.image(img, caption="Gambar Original", use_container_width=True)

        text = st.text_input("Teks Watermark")
        size = st.slider("Ukuran Font", 10, 150, 40)
        color = st.color_picker("Warna", "#FFFFFF")
        pos = st.selectbox("Posisi Watermark", ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"])

        if st.button("💧 Tambahkan Watermark"):
            if text.strip() == "":
                st.error("Teks watermark tidak boleh kosong!")
            else:
                wm_img = apply_watermark(img, text, size, color, pos)
                st.success("Watermark berhasil diterapkan!")
                st.image(wm_img, caption="Hasil Watermark", use_container_width=True)

                buf = io.BytesIO()
                wm_img.save(buf, format="PNG")

                st.download_button(
                    label="⬇️ Download Gambar Watermark",
                    data=buf.getvalue(),
                    file_name="watermarked.png",
                    mime="image/png"
                )
