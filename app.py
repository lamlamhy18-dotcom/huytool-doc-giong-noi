import streamlit as st
import edge_tts
import asyncio
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="App Đọc Giọng Nói (Đã Fix)", page_icon="✅", layout="wide")
st.title("✅ Công cụ Chuyển Văn Bản -> Giọng Nói")

if 'text_content' not in st.session_state:
    st.session_state['text_content'] = ""

# --- 2. GIAO DIỆN ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Nhập văn bản")
    text_input = st.text_area(
        "Nội dung:", 
        value=st.session_state['text_content'], 
        height=350,
        placeholder="Nhập tiếng Việt vào đây..."
    )

with col2:
    st.subheader("2. Tùy chỉnh")
    with st.container(border=True):
        # Chọn giọng
        VOICES = {
            "🇻🇳 VN - Hoài My (Nữ - Truyện)": "vi-VN-HoaiMyNeural",
            "🇻🇳 VN - Nam Minh (Nam - Tin tức)": "vi-VN-NamMinhNeural",
            "🇺🇸 US - Aria (Tiếng Anh)": "en-US-AriaNeural",
        }
        voice = st.selectbox("Giọng đọc:", list(VOICES.keys()))
        selected_voice = VOICES[voice]
        
        st.write("---")
        # Thanh trượt (Để mặc định là 0)
        rate = st.slider("Tốc độ", -50, 50, 0)
        pitch = st.slider("Cao độ", -50, 50, 0)
        volume = st.slider("Âm lượng", -50, 50, 0)
        
        st.caption("Mẹo: Nếu không cần thiết, cứ để tất cả là 0.")

    # --- NÚT XỬ LÝ ---
    st.write("")
    if st.button("🚀 CHUYỂN ĐỔI NGAY", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("⚠️ Chưa nhập chữ nào cả!")
        else:
            status = st.status("Đang kết nối server...", expanded=True)
            output_file = "result.mp3"
            
            async def run_safe_tts():
                # --- LOGIC THÔNG MINH (QUAN TRỌNG) ---
                # Chỉ gửi tham số nếu nó KHÁC 0. Nếu bằng 0 thì bỏ qua.
                args = {'text': text_input, 'voice': selected_voice}
                
                if rate != 0: args['rate'] = f"{rate:+d}%"
                if pitch != 0: args['pitch'] = f"{pitch:+d}Hz"
                if volume != 0: args['volume'] = f"{volume:+d}%"
                
                status.write(f"Đang xử lý với tham số: {args}")
                
                communicate = edge_tts.Communicate(**args)
                await communicate.save(output_file)

            try:
                asyncio.run(run_safe_tts())
                status.update(label="✅ Thành công!", state="complete", expanded=False)
                
                # Hiện kết quả
                with open(output_file, 'rb') as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format='audio/mp3')
                    st.download_button("📥 Tải File MP3", audio_bytes, "audio.mp3", "audio/mp3")
                
                os.remove(output_file)
                
            except Exception as e:
                status.update(label="❌ Lỗi!", state="error")
                st.error(f"Chi tiết lỗi: {e}")
                
