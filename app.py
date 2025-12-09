import streamlit as st
import edge_tts
import asyncio
import os
import tempfile

# 1. CẤU HÌNH TRANG (Giao diện Rộng giống web mẫu)
st.set_page_config(page_title="Siêu AI Đọc Giọng Nói", page_icon="🎧", layout="wide")

st.title("🎧 Edge-TTS Pro: Chuyên Trị Văn Bản Dài")
st.markdown("Phiên bản nâng cấp: Hỗ trợ chỉnh **Cao độ**, **Âm lượng** và **Tự động chia nhỏ file**.")

# Khởi tạo session state
if 'text_content' not in st.session_state:
    st.session_state['text_content'] = ""

# --- GIAO DIỆN 2 CỘT ---
col_trai, col_phai = st.columns([1, 1], gap="medium")

# === CỘT TRÁI: NHẬP LIỆU ===
with col_trai:
    st.subheader("1. Nhập văn bản hoặc Upload")
    
    # Upload file
    uploaded_file = st.file_uploader("Upload file truyện (.txt)", type="txt")
    if uploaded_file is not None:
        if st.button("📥 Nạp nội dung từ File"):
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                st.session_state['text_content'] = string_data
                st.success(f"Đã nạp file thành công! ({len(string_data)} ký tự)")
            except:
                st.error("Lỗi font chữ! Hãy lưu file .txt với định dạng UTF-8.")

    # Khung soạn thảo
    text_input = st.text_area(
        "Nội dung cần đọc:", 
        value=st.session_state['text_content'], 
        height=450,
        placeholder="Nhập văn bản vào đây..."
    )
    
    # Cập nhật ngược lại session
    if text_input != st.session_state['text_content']:
        st.session_state['text_content'] = text_input
        
    st.caption(f"Độ dài hiện tại: {len(text_input)} ký tự.")

# === CỘT PHẢI: CÀI ĐẶT & XỬ LÝ ===
with col_phai:
    st.subheader("2. Cấu hình giọng đọc")
    
    # Khung cài đặt nằm trong container cho đẹp
    with st.container(border=True):
        # Chọn giọng
        voice_options = {
            "🇻🇳 VN - Hoài My (Nữ - Truyện cảm xúc)": "vi-VN-HoaiMyNeural",
            "🇻🇳 VN - Nam Minh (Nam - Trầm ấm)": "vi-VN-NamMinhNeural",
            "🇺🇸 US - Aria (Nữ)": "en-US-AriaNeural",
            "🇺🇸 US - Guy (Nam)": "en-US-GuyNeural",
            "🇨🇳 CN - Xiaoxiao (Nữ)": "zh-CN-XiaoxiaoNeural"
        }
        voice_key = st.selectbox("Chọn giọng đọc:", list(voice_options.keys()))
        selected_voice = voice_options[voice_key]
        
        st.divider()
        
        # 3 Thanh trượt điều chỉnh (Rate, Pitch, Volume)
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            rate = st.slider("Tốc độ", -50, 50, 0, step=5, help="Nhanh hay chậm")
        with col_p2:
            pitch = st.slider("Cao độ", -50, 50, 0, step=5, help="Giọng trầm hay bổng")
        with col_p3:
            volume = st.slider("Âm lượng", -50, 50, 0, step=5, help="To hay nhỏ")

        # Định dạng tham số cho đúng chuẩn edge-tts
        rate_str = f"{rate:+d}%"
        pitch_str = f"{pitch:+d}Hz"
        volume_str = f"{volume:+d}%"

        st.info(f"Cấu hình: Tốc độ {rate_str} | Cao độ {pitch_str} | Âm lượng {volume_str}")

    st.write("") # Khoảng cách
    
    # Nút xử lý chính
    if st.button("🚀 BẮT ĐẦU CHUYỂN ĐỔI (Xử lý thông minh)", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("⚠️ Chưa có nội dung!")
        else:
            status_box = st.status("Đang xử lý...", expanded=True)
            
            # LOGIC XỬ LÝ CHIA NHỎ VĂN BẢN
            # Edge-TTS không đọc được quá 5000 ký tự một lúc, nên phải chia nhỏ
            chunk_size = 4000 # Cắt mỗi đoạn 4000 ký tự cho an toàn
            chunks = [text_input[i:i+chunk_size] for i in range(0, len(text_input), chunk_size)]
            
            total_chunks = len(chunks)
            status_box.write(f"Văn bản dài {len(text_input)} ký tự -> Chia thành {total_chunks} phần nhỏ.")
            
            # Hàm chạy TTS
            async def run_tts(text_chunk, index):
                output_filename = f"part_{index+1}.mp3"
                communicate = edge_tts.Communicate(
                    text_chunk, 
                    selected_voice, 
                    rate=rate_str, 
                    pitch=pitch_str, 
                    volume=volume_str
                )
                await communicate.save(output_filename)
                return output_filename

            try:
                files_created = []
                progress_bar = status_box.progress(0)
                
                for i, chunk in enumerate(chunks):
                    status_box.write(f"▶️ Đang tạo phần {i+1}/{total_chunks}...")
                    file_name = asyncio.run(run_tts(chunk, i))
                    files_created.append(file_name)
                    progress_bar.progress((i + 1) / total_chunks)
                
                status_box.update(label="✅ Đã xong! Hãy tải xuống bên dưới.", state="complete", expanded=False)
                st.balloons()

                # HIỂN THỊ KẾT QUẢ
                st.success("Kết quả của bạn đây:")
                
                for idx, f_name in enumerate(files_created):
                    with open(f_name, "rb") as file:
                        btn = st.download_button(
                            label=f"📥 Tải Phần {idx+1} (.mp3)",
                            data=file,
                            file_name=f"audio_part_{idx+1}.mp3",
                            mime="audio/mp3"
                        )
                        st.audio(f_name, format="audio/mp3")
                    
                    # Dọn dẹp file sau khi load lên web xong (Optional)
                    # os.remove(f_name) 

            except Exception as e:
                status_box.update(label="❌ Có lỗi xảy ra", state="error")
                st.error(f"Chi tiết lỗi: {e}")
