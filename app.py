import streamlit as st
from PIL import Image
import qrcode
import io
from PIL import ImageEnhance
from PIL import ImageSequence

def color_replace(image, color):
    pixels = image.load()
    size = image.size[0]
    for width in range(size):
        for height in range(size):
            r, g, b, a = pixels[width, height]
            if (r, g, b, a) == (0,0,0,255):
                pixels[width,height] = color
            else:
                pixels[width,height] = (r,g,b,color[3])

def produce(txt, img, ver=5, err_crt=qrcode.constants.ERROR_CORRECT_H, bri=1.0, cont=1.0,
            colourful=False, rgba=(0,0,0,255), pixelate=False):
    if isinstance(img, Image.Image):
        pass
    elif isinstance(img, str):
        img = Image.open(img)
    else:
        return []
    frames = [produce_impl(txt, frame.copy(), ver, err_crt, bri, cont, colourful, rgba, pixelate) for frame in ImageSequence.Iterator(img)]
    return frames

def produce_impl(txt,img,ver=5,err_crt=qrcode.constants.ERROR_CORRECT_H,bri=1.0,cont=1.0,
                 colourful=False,rgba=(0,0,0,255),pixelate=False):
    """Produce QR code

    :txt: QR text
    :img: Image object
    :ver: QR version
    :err_crt: QR error correct
    :bri: Brightness enhance
    :cont: Contrast enhance
    :colourful: If colourful mode
    :rgba: color to replace black
    :pixelate: pixelate
    :returns: Produced image

    """
    qr = qrcode.QRCode(version=ver,error_correction=err_crt,box_size=3)
    qr.add_data(txt)
    qr.make(fit=True)
    img_qr = qr.make_image().convert('RGBA')
    if colourful and (rgba != (0,0,0,255)):
        color_replace(img_qr,rgba)
    img_img = img.convert('RGBA')

    img_img_size = min(img_img.size)
    img_size = img_qr.size[0] - 24

    img_enh = img_img.crop((0,0,img_img_size,img_img_size))
    enh = ImageEnhance.Contrast(img_enh)
    img_enh = enh.enhance(cont)
    enh = ImageEnhance.Brightness(img_enh)
    img_enh = enh.enhance(bri)
    if not colourful:
        if pixelate:
            img_enh = img_enh.convert('1').convert('RGBA')
        else:
            img_enh = img_enh.convert('L').convert('RGBA')
    img_frame = img_qr
    img_enh = img_enh.resize((img_size*10,img_size*10), Image.NEAREST)
    img_enh_l = img_enh.convert("L").resize((img_size,img_size), Image.NEAREST)
    img_frame_l = img_frame.convert("L")

    for x in range(0,img_size):
        for y in range(0,img_size):
            if x < 24 and (y < 24 or y > img_size-25):
                continue
            if x > img_size-25 and (y < 24):
                continue
            if (x%3 ==1 and  y%3 == 1):
                if (img_frame_l.getpixel((x+12,y+12)) > 70 and img_enh_l.getpixel((x,y)) < 185)\
                        or (img_frame_l.getpixel((x+12,y+12)) < 185 and img_enh_l.getpixel((x,y)) > 70):
                    continue
            img_frame.putpixel((x+12,y+12),(0,0,0,0))
    pos = qrcode.util.pattern_position(qr.version)
    img_qr2 = qr.make_image().convert("RGBA")
    if colourful and (rgba != (0,0,0,0)):
        color_replace(img_qr2,rgba)
    for i in pos:
        for j in pos:
            if (i == 6 and j == pos[-1]) or (j == 6 and i == pos[-1])\
                or (i == 6 and j == 6):
                continue
            else:
                rect = (3*(i-2)+12,3*(j-2)+12,3*(i+3)+12,3*(j+3)+12)
                img_tmp = img_qr2.crop(rect)
                img_frame.paste(img_tmp,rect)

    img_res = Image.new("RGBA",(img_frame.size[0]*10,img_frame.size[1]*10),(255,255,255,255))
    img_res.paste(img_enh,(120,120),img_enh)
    img_frame = img_frame.resize((img_frame.size[0]*10,img_frame.size[1]*10), Image.NEAREST)
    img_res.paste(img_frame,(0,0),img_frame)
    img_res = img_res.convert('RGB')
    if pixelate:
        return img_res.resize(img_qr.size, Image.NEAREST).resize((img_img_size,img_img_size), Image.NEAREST)
    return img_res



def main():
    st.title("QRコード生成アプリ")

    # 入力フィールド
    txt = st.text_input("QRコードに埋め込むURLを入力してください:")
    uploaded_file = st.file_uploader("QRコードに埋め込む画像を選択してください", type=["jpg", "png", "jpeg"])
    
    # オプション設定
    col1, col2 = st.columns(2)
    with col1:
        ver = st.slider("QRコードバージョン", 1, 40, 5)
        bri = st.slider("明るさ", 0.1, 2.0, 1.0)
    with col2:
        cont = st.slider("コントラスト", 0.1, 2.0, 1.0)
        colourful = st.checkbox("カラフルモード", True)

    if colourful:
        rgba = st.color_picker("QRコードの色を選択", "#000000")
        rgba = tuple(int(rgba.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    else:
        rgba = (0, 0, 0, 255)

    pixelate = st.checkbox("ピクセル化", False)

    if st.button("QRコード生成"):
        if txt and uploaded_file:
            img = Image.open(uploaded_file)
            frames = produce(txt, img, ver, qrcode.constants.ERROR_CORRECT_H, bri, cont, colourful, rgba, pixelate)
            
            if len(frames) == 1:
                st.image(frames[0], caption="生成されたQRコード", use_column_width=True)
                
                # ダウンロードボタンの追加
                buf = io.BytesIO()
                frames[0].save(buf, format="PNG")
                btn = st.download_button(
                    label="QRコードをダウンロード",
                    data=buf.getvalue(),
                    file_name="qr_output.png",
                    mime="image/png"
                )
            else:
                st.warning("アニメーション画像はサポートされていません。")
        else:
            st.error("URLと画像の両方を入力してください。")

if __name__ == "__main__":
    main()
