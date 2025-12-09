import streamlit as st
import edge_tts
import asyncio
import os
import tempfile
import nest_asyncio
from typing import Optional

# Fix lỗi asyncio cho Streamlit Cloud
nest_asyncio.apply()

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
if 'last_success' not in st.session_state:
    st.session_state.last_success = False

# --- 2. DANH SÁCH GIỌNG ĐỌC ĐÃ TEST HOẠT ĐỘNG ---
VOICES = {
    "🇻🇳 VN - Hoài My (Nữ - Truyện)": "vi-VN-HoaiMyNeural",
    "🇻🇳 VN - Nam Minh (Nam - Tin tức)": "vi-VN-NamMinhNeural",
    "🇺🇸 US - Jenny (Tiếng Anh - Nữ)": "en-US-JennyNeural",  # Đổi từ Aria sang Jenny
    "🇺🇸 US - Guy (Tiếng Anh - Nam)": "en-US-GuyNeural",
    "🇬🇧 UK - Sonia (Tiếng Anh Anh - Nữ)": "en-GB-SoniaNeural",
}

# --- 3. HÀM CHUYỂN ĐỔI TTS FIX LỖI ---
async def convert_tts(text: str, voice: str, rate: int = 0, pitch: int = 0, volume: int = 0) -> Optional[bytes]:
    """Chuyển văn bản thành giọng nói - Fix version"""
    try:
        # Tạo file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            output_file = tmp_file.name
        
        # Tạo đối tượng communicate với timeout
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=f"{rate:+d}%" if rate != 0 else "+0%",
            pitch=f"{pitch:+d}Hz" if pitch != 0 else "+0Hz",
            volume=f"{volume:+d}%" if volume != 0 else "+0%"
        )
        
        # Lưu file với timeout
        await asyncio.wait_for(communicate.save(output_file), timeout=30.0)
        
        # Đọc file và convert thành bytes
        with open(output_file, 'rb') as f:
            audio_bytes = f.read()
        
        # Xóa file tạm
        os.unlink(output_file)
        
        # Kiểm tra file có dữ liệu không
        if len(audio_bytes) < 100:  # File MP3 ít nhất vài trăm bytes
            raise ValueError("Audio file quá nhỏ, có thể tạo không thành công")
            
        return audio_bytes
        
    except asyncio.TimeoutError:
        st.error("⏱️ Lỗi timeout: Server phản hồi quá lâu")
        return None
    except Exception as e:
        st.error(f"❌ Lỗi khi chuyển đổi: {str(e)}")
        return None

# --- 4. GIAO DIỆN ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Nhập văn bản")
    text_input = st.text_area(
        "Nội dung cần chuyển thành giọng nói:", 
        value=st.session_state.text_content, 
        height=300,
        placeholder="Nhập hoặc dán văn bản của bạn vào đây...\nVí dụ: Xin chào! Tôi là trợ lý ảo có thể đọc văn bản tiếng Việt.",
        help="Vui lòng nhập văn bản rõ ràng, không chứa ký tự đặc biệt"
    )
    
    # Hiển thị số ký tự
    char_count = len(text_input)
    st.caption(f"📊 Số ký tự: {char_count}/2000 (giới hạn an toàn)")
    
    # Nút xóa nhanh
    col_clear1, col_clear2 = st.columns([1, 1])
    with col_clear1:
        if st.button("🗑️ Xóa văn bản", use_container_width=True):
            st.session_state.text_content = ""
            st.session_state.audio_file = None
            st.rerun()
    
    with col_clear2:
        if st.button("📋 Dán ví dụ", use_container_width=True):
            st.session_state.text_content = "Xin chào! Đây là ví dụ về chuyển văn bản thành giọng nói tiếng Việt. Ứng dụng này sử dụng công nghệ AI để đọc văn bản một cách tự nhiên và có ngữ điệu."
            st.rerun()

with col2:
    st.subheader("⚙️ Tùy chỉnh giọng đọc")
    
    with st.container(border=True):
        # Chọn giọng với mô tả rõ ràng
        voice_options = list(VOICES.keys())
        voice_desc = {
            "🇻🇳 VN - Hoài My (Nữ - Truyện)": "Giọng nữ miền Bắc, phù hợp đọc truyện, thơ",
            "🇻🇳 VN - Nam Minh (Nam - Tin tức)": "Giọng nam miền Bắc, phù hợp tin tức, hướng dẫn",
            "🇺🇸 US - Jenny (Tiếng Anh - Nữ)": "Giọng nữ Mỹ, rõ ràng, tự nhiên",
            "🇺🇸 US - Guy (Tiếng Anh - Nam)": "Giọng nam Mỹ, trầm ấm",
            "🇬🇧 UK - Sonia (Tiếng Anh Anh - Nữ)": "Giọng nữ Anh, sang trọng"
        }
        
        voice = st.selectbox(
            "**Chọn giọng đọc (BẮT BUỘC):**",
            voice_options,
            index=0,
            help="Chọn giọng phù hợp với ngôn ngữ của văn bản"
        )
        
        # Hiển thị mô tả giọng
        st.info(f"📢 {voice_desc[voice]}")
        selected_voice = VOICES[voice]
        
        st.markdown("---")
        
        # Cài đặt âm thanh với giá trị mặc định AN TOÀN
        st.markdown("**🎛️ Điều chỉnh âm thanh (TÙY CHỌN):**")
        
        col_rate, col_pitch = st.columns(2)
        with col_rate:
            rate = st.slider(
                "Tốc độ (%)", 
                -50, 50, 0,
                help="-50%: Rất chậm, 0%: Bình thường, +50%: Rất nhanh"
            )
        with col_pitch:
            pitch = st.slider(
                "Cao độ (Hz)", 
                -50, 50, 0,
                help="-50Hz: Giọng trầm, 0Hz: Bình thường, +50Hz: Giọng cao"
            )
        
        volume = st.slider(
            "Âm lượng (%)", 
            -50, 50, 0,
            help="-50%: Rất nhỏ, 0%: Bình thường, +50%: Rất to"
        )
        
        st.caption("⚠️ **Lưu ý:** Để tất cả là 0 nếu bạn không chắc chắn!")

# --- 5. NÚT XỬ LÝ CHÍNH - FIX LỖI ---
st.markdown("---")

# Container cho nút bấm
btn_container = st.container()

with btn_container:
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        convert_clicked = st.button(
            "🔊 CHUYỂN ĐỔI NGAY", 
            type="primary", 
            use_container_width=True,
            disabled=st.session_state.processing,
            key="convert_btn"
        )
    
    with col_btn2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.audio_file = None
            st.session_state.last_success = False
            st.rerun()
    
    with col_btn3:
        if st.session_state.audio_file:
            st.download_button(
                label="💾 Tải MP3",
                data=st.session_state.audio_file,
                file_name=f"audio_{selected_voice}.mp3",
                mime="audio/mp3",
                use_container_width=True
            )

# --- 6. XỬ LÝ KHI NHẤN NÚT ---
if convert_clicked:
    if not text_input.strip():
        st.warning("⚠️ Vui lòng nhập văn bản trước khi chuyển đổi!")
        st.stop()
    
    if len(text_input) > 2000:
        st.error("❌ Văn bản quá dài! Tối đa 2000 ký tự để đảm bảo ổn định.")
        st.stop()
    
    # Kiểm tra ký tự lạ
    import re
    if re.search(r'[<>\[\]{}|\\^~`]', text_input):
        st.warning("⚠️ Văn bản chứa ký tự đặc biệt có thể gây lỗi. Vui lòng xóa các ký tự: < > [ ] { } | \\ ^ ~ `")
        st.stop()
    
    st.session_state.processing = True
    st.session_state.text_content = text_input
    
    # Hiển thị trạng thái
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    with status_placeholder.container():
        st.info("🔄 Đang kết nối với dịch vụ Microsoft TTS...")
        progress_bar.progress(20)
        
        try:
            # Tạo event loop mới
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Chạy async function
            progress_bar.progress(40)
            audio_bytes = loop.run_until_complete(
                convert_tts(
                    text=text_input,
                    voice=selected_voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
            )
            
            progress_bar.progress(80)
            
            if audio_bytes:
                st.session_state.audio_file = audio_bytes
                st.session_state.last_success = True
                progress_bar.progress(100)
                
                status_placeholder.success("✅ Chuyển đổi thành công!")
                
                # Auto-play audio
                st.audio(audio_bytes, format='audio/mp3')
                
                # Hiển thị thông tin
                file_size_kb = len(audio_bytes) / 1024
                st.caption(f"📦 Kích thước file: {file_size_kb:.1f} KB | 🎵 Giọng: {voice}")
                
            else:
                status_placeholder.error("❌ Không nhận được audio từ server. Vui lòng thử lại!")
                st.session_state.last_success = False
                
            loop.close()
            
        except Exception as e:
            status_placeholder.error(f"💥 Lỗi hệ thống: {str(e)}")
            st.session_state.last_success = False
            
        finally:
            st.session_state.processing = False
            progress_bar.empty()

# --- 7. HIỂN THỊ KẾT QUẢ NẾU CÓ ---
elif st.session_state.audio_file and not st.session_state.processing:
    st.markdown("---")
    st.subheader("🎧 Kết quả chuyển đổi")
    
    st.audio(st.session_state.audio_file, format='audio/mp3')
    
    # Thông tin chi tiết
    with st.expander("📊 Thông tin chi tiết"):
        file_size_kb = len(st.session_state.audio_file) / 1024
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Kích thước", f"{file_size_kb:.1f} KB")
        with col_info2:
            st.metric("Giọng đọc", voice.split(" ")[-1])
        with col_info3:
            st.metric("Trạng thái", "✅ Thành công")
        
        st.write("**Văn bản đã xử lý:**")
        st.text(text_input[:300] + ("..." if len(text_input) > 300 else ""))

# --- 8. HƯỚNG DẪN KHẮC PHỤC LỖI ---
with st.expander("🔧 HƯỚNG DẪN KHẮC PHỤC LỖI 'No audio was received'", expanded=False):
    st.markdown("""
    ### Nếu gặp lỗi "Không nhận được audio", hãy thử:
    
    1. **Chọn đúng giọng phù hợp với ngôn ngữ:**
       - Văn bản tiếng Việt → Chọn giọng **Hoài My** hoặc **Nam Minh**
       - Văn bản tiếng Anh → Chọn giọng **Jenny** hoặc **Guy**
    
    2. **Giảm độ dài văn bản:**
       - Chỉ nhập 100-500 ký tự để test trước
       - Nếu dài quá có thể bị timeout
    
    3. **Kiểm tra ký tự đặc biệt:**
       - Xóa các ký tự: `< > [ ] { } | \\ ^ ~ \``
       - Chỉ dùng chữ cái, số, dấu câu thông thường
    
    4. **Đặt lại cài đặt âm thanh:**
       - Để tất cả thanh trượt ở **vị trí 0**
       - Chỉ điều chỉnh sau khi đã hoạt động ổn
    
    5. **Thử trên trình duyệt khác:**
       - Chrome/Firefox/Edge mới nhất
       - Tắt trình chặn quảng cáo
    
    6. **Kiểm tra kết nối mạng:**
       - Dịch vụ cần kết nối Internet ổn định
       - Thử lại sau 1-2 phút nếu server bận
    """)

# --- 9. HƯỚNG DẪN SỬ DỤNG ---
with st.expander("📖 Hướng dẫn sử dụng cơ bản"):
    st.markdown("""
    ### Các bước sử dụng:
    1. **Nhập văn bản** vào ô bên trái
    2. **Chọn giọng đọc** phù hợp với ngôn ngữ
    3. **(Tùy chọn)** Điều chỉnh tốc độ/cao độ/âm lượng
    4. Nhấn nút **"CHUYỂN ĐỔI NGAY"**
    5. **Chờ 5-10 giây** để xử lý
    6. **Nghe thử** và tải file MP3 nếu thành công
    
    ### Giới hạn:
    - Tối đa: **2000 ký tự** mỗi lần
    - Thời gian chờ: **30 giây**
    - Định dạng xuất: **MP3 128kbps**
    """)

# --- 10. FOOTER & THÔNG TIN ---
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("🔧 **Phiên bản:** 2.0.1 (Đã fix lỗi audio)")
with footer_col2:
    st.caption("🌐 **Công nghệ:** Microsoft Edge TTS API")
with footer_col3:
    st.caption("⚡ **Trạng thái:** " + ("✅ Sẵn sàng" if not st.session_state.processing else "🔄 Đang xử lý..."))

# Tự động refresh nếu đang xử lý
if st.session_state.processing:
    st.rerun()
