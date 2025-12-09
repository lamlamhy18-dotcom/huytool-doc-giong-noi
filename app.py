import streamlit as st
import edge_tts
import asyncio
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Edge-TTS Super Fix", page_icon="✅", layout="wide")
st.title("✅ Tool Đọc Giọng Nói (Đã Fix Lỗi)")

if 'text_content' not in st.session_state:
    st.session_state['text_content'] = ""

# --- 2. GIAO DIỆN ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Văn bản")
    text_input = st.text_area(
        "Nhập nội dung:", 
        value=st.session_state['text_content'], 
        height=300,
        placeholder="Nhập tiếng Việt vào đây..."
    )

with col2:
    st.subheader("2. Cài đặt")
    with st.container(border=True):
        # Chọn giọng
        VOICES = {
            "🇻🇳 VN - Hoài My (Nữ)": "vi-VN-HoaiMyNeural",
            "🇻🇳 VN - Nam Minh (Nam)": "vi-VN-NamMinhNeural",
            "🇺🇸 US - Aria (English)": "en-US-AriaNeural",
        }
        voice = st.selectbox("Giọng đọc:", list(VOICES.keys()))
        selected_voice = VOICES[voice]
        
        st.write("---")
        # Thanh trượt
        rate = st.slider("Tốc độ", -50, 50, 0)
        pitch = st.slider("Cao độ", -50, 50, 0)
        volume = st.slider("Âm lượng", -50, 50, 0)
        
        st.caption("Mẹo: Hãy để tất cả là 0 nếu muốn giọng tự nhiên nhất.")

    # --- NÚT XỬ LÝ ---
    st.write("")
    if st.button("🚀 CHUYỂN ĐỔI NGAY", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Chưa nhập chữ nào cả!")
        else:
            status = st.status("Đang kết nối server...", expanded=True)
            output_file = "test_audio.mp3"
            
            async def run_safe_tts():
                # --- LOGIC THÔNG MINH ---
                # Chỉ thêm tham số nếu khác 0 để tránh lỗi server
                args = {'text': text_input, 'voice': selected_voice}
                
                if rate != 0: args['rate'] = f"{rate:+d}%"
                if pitch != 0: args['pitch'] = f"{pitch:+d}Hz"
                if volume != 0: args['volume'] = f"{volume:+d}%"
                
                # In ra để kiểm tra (Debug)
                status.write(f"Đang gửi lệnh: {args}")
                
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
                status.update(label="❌ Lỗi rồi!", state="error")
                st.error(f"Chi tiết lỗi: {e}")
