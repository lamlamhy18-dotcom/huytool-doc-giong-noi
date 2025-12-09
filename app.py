import streamlit as st
import edge_tts
import asyncio
import os

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Edge-TTS Pro", page_icon="🎧", layout="wide")

st.title("🎧 Công cụ Đọc Giọng Nói (Chuẩn HuggingFace)")
st.markdown("Hỗ trợ: **Chỉnh giọng**, **Cao độ**, **Tốc độ** và **Tải file văn bản**.")

# Khởi tạo bộ nhớ
if 'text_content' not in st.session_state:
    st.session_state['text_content'] = ""

# --- 2. GIAO DIỆN 2 CỘT ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Nhập văn bản")
    
    # Upload file
    uploaded_file = st.file_uploader("Hoặc tải lên file .txt", type="txt")
    if uploaded_file:
        if st.button("📥 Dùng nội dung trong file"):
            try:
                st.session_state['text_content'] = uploaded_file.getvalue().decode("utf-8")
                st.success("Đã nạp file!")
            except:
                st.error("Lỗi file! Hãy dùng file .txt chuẩn UTF-8.")

    # Khung nhập liệu
    text_input = st.text_area(
        "Nội dung:", 
        value=st.session_state['text_content'], 
        height=400,
        placeholder="Nhập văn bản tiếng Việt có dấu vào đây..."
    )
    # Cập nhật session
    if text_input != st.session_state['text_content']:
        st.session_state['text_content'] = text_input

with col2:
    st.subheader("2. Cấu hình & Kết quả")
    
    with st.container(border=True):
        # Chọn giọng
        VOICES = {
            "🇻🇳 VN - Hoài My (Nữ - Truyện)": "vi-VN-HoaiMyNeural",
            "🇻🇳 VN - Nam Minh (Nam - Tin tức)": "vi-VN-NamMinhNeural",
            "🇺🇸 US - Aria (Tiếng Anh)": "en-US-AriaNeural",
            "🇨🇳 CN - Xiaoxiao (Tiếng Trung)": "zh-CN-XiaoxiaoNeural"
        }
        voice = st.selectbox("Chọn giọng đọc:", list(VOICES.keys()))
        selected_voice = VOICES[voice]
        
        st.divider()
        
        # 3 Thanh trượt (Giống web mẫu)
        st.caption("Điều chỉnh thông số:")
        rate = st.slider("Tốc độ (Rate)", -50, 50, 0, format="%d%%")
        pitch = st.slider("Cao độ (Pitch)", -50, 50, 0, format="%dHz")
        volume = st.slider("Âm lượng (Volume)", -50, 50, 0, format="%d%%")
        
        # Format chuẩn cho Edge-TTS
        # Lưu ý: Nếu giá trị là 0, ta để chuỗi "+0%" để đảm bảo đúng cú pháp
        rate_str = f"{rate:+d}%"
        pitch_str = f"{pitch:+d}Hz"
        volume_str = f"{volume:+d}%"
        
        st.code(f"Setting: {rate_str} | {pitch_str} | {volume_str}", language="text")

    st.write("")
    
    # Nút bấm xử lý
    if st.button("🚀 CHUYỂN ĐỔI NGAY", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("⚠️ Hãy nhập văn bản trước!")
        else:
            status = st.status("Đang xử lý...", expanded=True)
            output_file = "audio_output.mp3"
            
            async def run_tts():
                communicate = edge_tts.Communicate(
                    text_input, 
                    selected_voice, 
                    rate=rate_str, 
                    pitch=pitch_str, 
                    volume=volume_str
                )
                await communicate.save(output_file)

            try:
                # Chạy hàm async
                asyncio.run(run_tts())
                
                status.update(label="✅ Thành công!", state="complete", expanded=False)
                
                # Hiển thị audio
                st.success("Nghe thử và tải về:")
                with open(output_file, 'rb') as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format='audio/mp3')
                    st.download_button("📥 Tải File MP3", audio_bytes, "tts_audio.mp3", "audio/mp3")
                
                os.remove(output_file) # Xóa file tạm
                
            except Exception as e:
                status.update(label="❌ Thất bại!", state="error")
                st.error(f"Lỗi hệ thống: {e}")
                st.warning("Mẹo: Nếu lỗi, hãy thử reset Tốc độ/Cao độ về 0 hoặc kiểm tra lại văn bản.")
