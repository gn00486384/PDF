import io
import zipfile

import fitz  # PyMuPDF
from PIL import Image
import streamlit as st


st.set_page_config(page_title="PDF 轉 JPG", layout="wide")
st.title("📄 PDF 轉 JPG 工具")

# 側邊欄設置
st.sidebar.header("⚙️ 轉換設置")
# 將預設品質設為100、清晰度倍率設為4
jpg_quality = st.sidebar.slider("JPG 品質", 50, 100, 100)
zoom = st.sidebar.slider("清晰度倍率", 1.0, 4.0, 4.0, 0.1)

st.sidebar.divider()
st.sidebar.write("**提示：**")
st.sidebar.write("- 更高品質 = 更大檔案")
st.sidebar.write("- 更高倍率 = 更清晰但處理更慢")

# 文件上傳
uploaded_files = st.file_uploader(
    "上傳 PDF 檔案",
    type=["pdf"],
    accept_multiple_files=True
)

def pdf_to_jpg_bytes(pdf_bytes, zoom=4.0, jpg_quality=95):
    """將 PDF 轉換為 JPG 圖像字節"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        results = []

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # 轉換為 PIL Image
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # 創建 BytesIO 對象
            img_bytes = io.BytesIO()

            # 根據品質設定優化壓縮參數
            if jpg_quality >= 95:
                # 高品質設定：無損壓縮
                img.save(img_bytes, format="JPEG", quality=jpg_quality,
                        optimize=True, subsampling=0)
            else:
                # 一般品質：標準壓縮
                img.save(img_bytes, format="JPEG", quality=jpg_quality,
                        optimize=True)

            img_bytes.seek(0)
            results.append((f"page_{page_index + 1}.jpg", img_bytes.getvalue()))

        doc.close()
        return results
    except Exception as e:
        raise Exception(f"轉換失敗: {str(e)}")

if uploaded_files:
    st.divider()
    
    # 創建進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    zip_buffer = io.BytesIO()
    total_files = len(uploaded_files)
    processed_files = 0

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_index, uploaded_file in enumerate(uploaded_files):
                status_text.info(f"正在處理: {uploaded_file.name}")
                
                pdf_bytes = uploaded_file.read()
                jpg_files = pdf_to_jpg_bytes(
                    pdf_bytes,
                    zoom=zoom,
                    jpg_quality=jpg_quality
                )

                base_name = uploaded_file.name.rsplit(".", 1)[0]
                for file_name, img_bytes in jpg_files:
                    zip_file.writestr(f"{base_name}/{file_name}", img_bytes)
                
                processed_files += 1
                progress = processed_files / total_files
                progress_bar.progress(progress)

        zip_buffer.seek(0)
        status_text.success("✅ 轉換完成！")
        
        st.divider()
        st.download_button(
            label="📥 下載全部 JPG（ZIP）",
            data=zip_buffer,
            file_name="pdf_to_jpg.zip",
            mime="application/zip"
        )
    except Exception as e:
        status_text.error(f"❌ 轉換出錯: {str(e)}")