import streamlit as st
import edge_tts
import asyncio
import os

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Công cụ TTS Pro Max", page_icon="🎙️")
st.title("🎙️ Công cụ Đọc Văn Bản (TTS)")

# Khởi tạo bộ nhớ tạm để lưu văn bản
if 'text_content' not in st.session_state:
    st.session_state['text_content'] = ""

# --- 2. THANH CÀI ĐẶT (BÊN TRÁI) ---
with st.sidebar:
    st.header("⚙️ Cài đặt giọng đọc")
    
    # Chọn giọng
    voice_options = {
        "🇻🇳 Tiếng Việt (Nam - Hoài My)": "vi-VN-HoaiMyNeural",
        "🇻🇳 Tiếng Việt (Nữ - Nam Minh)": "vi-VN-NamMinhNeural",
        "🇺🇸 Tiếng Anh (US - Aria)": "en-US-AriaNeural",
        "🇨🇳 Tiếng Trung (Xiaoxiao)": "zh-CN-XiaoxiaoNeural"
    }
    voice_choice = st.selectbox("Chọn giọng:", list(voice_options.keys()))
    selected_voice = voice_options[voice_choice]
    
    # Chỉnh tốc độ
    st.write("---")
    speed = st.slider("Tốc độ đọc (%)", -50, 50, 0, 10)
    rate_str = f"+{speed}%" if speed >= 0 else f"{speed}%"
    
    st.write("---")
    st.header("📂 Upload File Text")
    uploaded_file = st.file_uploader("Chọn file kịch bản (.txt)", type="txt")
    
    if uploaded_file is not None:
        if st.button("📥 Nạp nội dung vào khung"):
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                st.session_state['text_content'] = string_data
                st.success("Đã nạp xong!")
            except Exception as e:
                st.error("Lỗi file không đúng định dạng UTF-8")

# --- 3. KHUNG NHẬP LIỆU (BÊN PHẢI) ---
st.subheader("Nội dung cần đọc:")
text_input = st.text_area(
    "Soạn thảo hoặc chỉnh sửa tại đây:", 
    value=st.session_state['text_content'], 
    height=300,
    placeholder="Nhập văn bản vào đây..."
)

# Cập nhật lại bộ nhớ nếu người dùng gõ tay
if text_input != st.session_state['text_content']:
    st.session_state['text_content'] = text_input

# --- 4. HÀM XỬ LÝ (BACKEND) ---
async def text_to_speech(text, voice, rate, output_file):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

# --- 5. NÚT BẤM VÀ KẾT QUẢ ---
st.write("---")
if st.button("🚀 BẮT ĐẦU CHUYỂN ĐỔI", type="primary"):
    if text_input.strip():
        output_file = "audio_output.mp3"
        status_box = st.empty()
        status_box.info("⏳ Đang xử lý... Vui lòng đợi...")
        
        try:
            asyncio.run(text_to_speech(text_input, selected_voice, rate_str, output_file))
            
            status_box.success("✅ Hoàn tất! Nghe và tải về bên dưới:")
            
            with open(output_file, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.download_button(
                        label="📥 Tải MP3",
                        data=audio_bytes,
                        file_name="tts_audio.mp3",
                        mime="audio/mp3"
                    )
            os.remove(output_file) # Dọn dẹp file
            
        except Exception as e:
            status_box.error(f"Lỗi: {e}")
    else:
        st.warning("⚠️ Bạn chưa nhập nội dung nào cả!")