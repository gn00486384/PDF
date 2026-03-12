import io
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
import streamlit as st


st.set_page_config(page_title="PDF 轉 JPG", layout="wide")
st.title("📄 PDF 轉 JPG 工具")

# 側邊欄設置
st.sidebar.header("⚙️ 轉換設置")
jpg_quality = st.sidebar.slider("JPG 品質", 50, 100, 100)
zoom = st.sidebar.slider("清晰度倍率", 1.0, 4.0, 4.0, 0.1)

download_mode = st.sidebar.radio(
    "下載方式",
    ["ZIP 壓縮檔", "單張 JPG"]
)

st.sidebar.divider()
st.sidebar.write("**提示：**")
st.sidebar.write("- 更高品質 = 更大檔案")
st.sidebar.write("- 更高倍率 = 更清晰但處理更慢")
st.sidebar.write("- 單張 JPG 模式會顯示每一頁的個別下載按鈕")

# 文件上傳
uploaded_files = st.file_uploader(
    "上傳 PDF 檔案",
    type=["pdf"],
    accept_multiple_files=True
)


def pdf_to_jpg_bytes(pdf_bytes, original_name, zoom=4.0, jpg_quality=95):
    """將 PDF 轉換為 JPG 圖像位元組，檔名使用原始 PDF 名稱"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        results = []

        pdf_stem = Path(original_name).stem

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img_buffer = io.BytesIO()

            if jpg_quality >= 95:
                img.save(
                    img_buffer,
                    format="JPEG",
                    quality=jpg_quality,
                    optimize=True,
                    subsampling=0
                )
            else:
                img.save(
                    img_buffer,
                    format="JPEG",
                    quality=jpg_quality,
                    optimize=True
                )

            img_buffer.seek(0)

            # 單頁與多頁命名
            if len(doc) == 1:
                jpg_name = f"{pdf_stem}.jpg"
            else:
                jpg_name = f"{pdf_stem}_{page_index + 1}.jpg"

            results.append((jpg_name, img_buffer.getvalue()))

        doc.close()
        return results

    except Exception as e:
        raise Exception(f"轉換失敗: {str(e)}")


if uploaded_files:
    st.divider()

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(uploaded_files)
    processed_files = 0

    all_jpg_files = []

    try:
        for uploaded_file in uploaded_files:
            status_text.info(f"正在處理: {uploaded_file.name}")

            pdf_bytes = uploaded_file.read()
            jpg_files = pdf_to_jpg_bytes(
                pdf_bytes=pdf_bytes,
                original_name=uploaded_file.name,
                zoom=zoom,
                jpg_quality=jpg_quality
            )

            all_jpg_files.extend(jpg_files)

            processed_files += 1
            progress_bar.progress(processed_files / total_files)

        status_text.success("✅ 轉換完成！")
        st.divider()

        if download_mode == "ZIP 壓縮檔":
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for jpg_name, img_bytes in all_jpg_files:
                    zip_file.writestr(jpg_name, img_bytes)

            zip_buffer.seek(0)

            st.download_button(
                label="📥 下載 ZIP",
                data=zip_buffer,
                file_name="pdf_to_jpg.zip",
                mime="application/zip"
            )

        else:
            st.subheader("🖼️ 單張 JPG 下載")

            for jpg_name, img_bytes in all_jpg_files:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(jpg_name)

                with col2:
                    st.download_button(
                        label="下載",
                        data=img_bytes,
                        file_name=jpg_name,
                        mime="image/jpeg",
                        key=f"download_{jpg_name}"
                    )

    except Exception as e:
        status_text.error(f"❌ 轉換出錯: {str(e)}")
