import streamlit as st
import edge_tts
import asyncio
import os
import tempfile

# --- 1. CẤU HÌNH ---
st.set_page_config(
    page_title="App Chuyển Văn Bản Thành Giọng Nói", 
    page_icon="🎤", 
    layout="wide"
)

st.title("🎤 Công cụ Chuyển Văn Bản Thành Giọng Nói")
st.markdown("---")

# Khởi tạo session state
if 'text_content' not in st.session_state:
    st.session_state.text_content = ""
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# --- 2. DANH SÁCH GIỌNG ĐỌC ---
VOICES = {
    "🇻🇳 VN - Hoài My (Nữ - Truyện)": "vi-VN-HoaiMyNeural",
    "🇻🇳 VN - Nam Minh (Nam - Tin tức)": "vi-VN-NamMinhNeural",
    "🇺🇸 US - Aria (Tiếng Anh - Nữ)": "en-US-AriaNeural",
    "🇺🇸 US - Guy (Tiếng Anh - Nam)": "en-US-GuyNeural",
    "🇬🇧 UK - Sonia (Tiếng Anh Anh - Nữ)": "en-GB-SoniaNeural",
}

# --- 3. GIAO DIỆN ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Nhập văn bản")
    text_input = st.text_area(
        "Nội dung cần chuyển thành giọng nói:", 
        value=st.session_state.text_content, 
        height=350,
        placeholder="Nhập hoặc dán văn bản của bạn vào đây...\nVí dụ: Xin chào! Tôi là trợ lý ảo có thể đọc văn bản.",
        help="Bạn có thể nhập tối đa 3000 ký tự"
    )
    
    # Hiển thị số ký tự
    char_count = len(text_input)
    st.caption(f"📊 Số ký tự: {char_count}/3000")
    
    # Nút xóa nhanh
    if st.button("🗑️ Xóa văn bản", use_container_width=True):
        st.session_state.text_content = ""
        st.rerun()

with col2:
    st.subheader("⚙️ Tùy chỉnh giọng đọc")
    
    with st.container(border=True):
        # Chọn giọng
        voice = st.selectbox(
            "**Chọn giọng đọc:**",
            list(VOICES.keys()),
            index=0,
            help="Chọn giọng phù hợp với nội dung của bạn"
        )
        selected_voice = VOICES[voice]
        
        # Hiển thị thông tin giọng
        if "VN" in voice:
            st.info("🎯 Giọng tiếng Việt - Đọc tự nhiên, có ngữ điệu")
        else:
            st.info("🌍 Giọng tiếng Anh - Phát âm chuẩn")
        
        st.markdown("---")
        
        # Cài đặt âm thanh
        st.markdown("**🎛️ Điều chỉnh âm thanh:**")
        
        col_rate, col_pitch = st.columns(2)
        with col_rate:
            rate = st.slider(
                "Tốc độ", 
                -50, 100, 0,
                help="Điều chỉnh tốc độ đọc: chậm hơn (-) hoặc nhanh hơn (+)"
            )
        with col_pitch:
            pitch = st.slider(
                "Cao độ", 
                -50, 50, 0,
                help="Điều chỉnh độ cao của giọng: thấp hơn (-) hoặc cao hơn (+)"
            )
        
        volume = st.slider(
            "Âm lượng", 
            -50, 50, 0,
            help="Điều chỉnh âm lượng của đầu ra"
        )
        
        st.caption("💡 **Mẹo:** Để mặc định tất cả là 0 để có chất lượng tốt nhất!")

# --- 4. NÚT XỬ LÝ CHÍNH ---
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])

with col_btn1:
    if st.button(
        "🎵 CHUYỂN ĐỔI THÀNH GIỌNG NÓI", 
        type="primary", 
        use_container_width=True,
        disabled=st.session_state.processing or not text_input.strip()
    ):
        if not text_input.strip():
            st.warning("⚠️ Vui lòng nhập văn bản trước khi chuyển đổi!")
        elif len(text_input) > 3000:
            st.error("❌ Văn bản quá dài! Tối đa 3000 ký tự.")
        else:
            st.session_state.processing = True
            st.session_state.text_content = text_input
            
            # Hiển thị trạng thái xử lý
            progress_bar = st.progress(0, text="Đang xử lý...")
            
            async def convert_text_to_speech():
                try:
                    # Tạo file tạm
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                        output_file = tmp_file.name
                    
                    # Xây dựng tham số
                    args = {
                        'text': text_input,
                        'voice': selected_voice,
                    }
                    
                    # Chỉ thêm các tham số nếu khác 0
                    if rate != 0:
                        args['rate'] = f"{rate:+d}%"
                    if pitch != 0:
                        args['pitch'] = f"{pitch:+d}Hz"
                    if volume != 0:
                        args['volume'] = f"{volume:+d}%"
                    
                    progress_bar.progress(30, text="Đang kết nối với dịch vụ...")
                    
                    # Chuyển đổi
                    communicate = edge_tts.Communicate(**args)
                    await communicate.save(output_file)
                    
                    progress_bar.progress(100, text="Hoàn thành!")
                    
                    # Lưu vào session state
                    with open(output_file, 'rb') as f:
                        st.session_state.audio_file = f.read()
                    
                    # Xóa file tạm
                    os.unlink(output_file)
                    
                    return True
                    
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
                    return False
                finally:
                    st.session_state.processing = False
            
            # Chạy async
            try:
                success = asyncio.run(convert_text_to_speech())
                if success:
                    st.success("✅ Chuyển đổi thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")
                st.session_state.processing = False

with col_btn2:
    if st.button("🔄 Làm mới", use_container_width=True):
        st.session_state.audio_file = None
        st.rerun()

with col_btn3:
    # Nút tải xuống
    if st.session_state.audio_file:
        st.download_button(
            label="📥 Tải xuống MP3",
            data=st.session_state.audio_file,
            file_name="audio_output.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

# --- 5. HIỂN THỊ KẾT QUẢ ---
if st.session_state.audio_file and not st.session_state.processing:
    st.markdown("---")
    st.subheader("🎧 Nghe thử kết quả")
    
    # Hiển thị audio player
    st.audio(st.session_state.audio_file, format='audio/mp3')
    
    # Thông tin file
    file_size = len(st.session_state.audio_file) / 1024  # KB
    st.caption(f"📏 Kích thước file: {file_size:.1f} KB")
    
    # Xem trước văn bản đã nhập
    with st.expander("📋 Xem lại văn bản đã nhập"):
        st.write(text_input[:500] + "..." if len(text_input) > 500 else text_input)

# --- 6. HƯỚNG DẪN SỬ DỤNG ---
with st.expander("ℹ️ Hướng dẫn sử dụng"):
    st.markdown("""
    ### 📖 Cách sử dụng:
    1. **Nhập văn bản** vào ô bên trái
    2. **Chọn giọng đọc** phù hợp (tiếng Việt hoặc tiếng Anh)
    3. **Điều chỉnh** tốc độ, cao độ, âm lượng nếu cần
    4. Nhấn **"CHUYỂN ĐỔI THÀNH GIỌNG NÓI"**
    5. **Nghe thử** và tải xuống file MP3
    
    ### 💡 Mẹo hay:
    - Giọng **Hoài My** phù hợp cho đọc truyện, thơ
    - Giọng **Nam Minh** phù hợp cho tin tức, bài phát biểu
    - Để mặc định các thanh trượt ở 0 để có chất lượng tốt nhất
    - Giới hạn tối đa: **3000 ký tự** mỗi lần chuyển đổi
    """)

# --- 7. FOOTER ---
st.markdown("---")
st.caption("Công cụ sử dụng Microsoft Edge TTS API | © 2024")

# Tự động làm mới nếu đang xử lý
if st.session_state.processing:
    st.rerun()
