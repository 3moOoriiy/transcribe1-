import streamlit as st
import whisper
import yt_dlp
import tempfile
import os
from pathlib import Path
import subprocess
import sys

# تثبيت المكتبات المطلوبة
def install_requirements():
    """تثبيت المكتبات المطلوبة"""
    requirements = [
        "openai-whisper",
        "yt-dlp",
        "ffmpeg-python"
    ]
    
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        except subprocess.CalledProcessError:
            st.error(f"فشل في تثبيت {req}")

# إعداد الصفحة
st.set_page_config(
    page_title="مُحوِّل الفيديو إلى نص",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 مُحوِّل الفيديو إلى نص")
st.markdown("تطبيق لتحويل الفيديوهات إلى نص باستخدام الذكاء الاصطناعي")

# إعداد Whisper
@st.cache_resource
def load_whisper_model(model_size):
    """تحميل نموذج Whisper"""
    try:
        return whisper.load_model(model_size)
    except Exception as e:
        st.error(f"خطأ في تحميل النموذج: {str(e)}")
        return None

# دالة لتحميل الفيديو من رابط
def download_video_from_url(url, output_path):
    """تحميل الفيديو من رابط يوتيوب أو مواقع أخرى"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True
    except Exception as e:
        st.error(f"خطأ في تحميل الفيديو: {str(e)}")
        return False

# دالة لاستخراج الصوت من الفيديو
def extract_audio(video_path, audio_path):
    """استخراج الصوت من الفيديو"""
    try:
        import ffmpeg
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        st.error(f"خطأ في استخراج الصوت: {str(e)}")
        return False

# دالة لعمل الترانسكريبت
def transcribe_audio(audio_path, model, language="auto"):
    """تحويل الصوت إلى نص"""
    try:
        if language == "auto":
            result = model.transcribe(audio_path)
        else:
            result = model.transcribe(audio_path, language=language)
        
        return result["text"]
    except Exception as e:
        st.error(f"خطأ في الترانسكريبت: {str(e)}")
        return None

# الواجهة الرئيسية
def main():
    # اختيار حجم النموذج
    col1, col2 = st.columns(2)
    
    with col1:
        model_size = st.selectbox(
            "اختر حجم النموذج:",
            ["tiny", "base", "small", "medium", "large"],
            index=2,
            help="النماذج الأكبر أكثر دقة لكن أبطأ"
        )
    
    with col2:
        language = st.selectbox(
            "اختر اللغة:",
            ["auto", "ar", "en", "fr", "es", "de"],
            help="auto للتحديد التلقائي"
        )
    
    # تحميل النموذج
    model = load_whisper_model(model_size)
    
    if model is None:
        st.error("فشل في تحميل النموذج. تأكد من تثبيت المكتبات المطلوبة.")
        return
    
    st.success(f"تم تحميل النموذج: {model_size}")
    
    # خيارات الإدخال
    input_method = st.radio(
        "اختر طريقة الإدخال:",
        ["رابط فيديو", "رفع ملف"],
        horizontal=True
    )
    
    if input_method == "رابط فيديو":
        url = st.text_input("أدخل رابط الفيديو (يوتيوب أو مواقع أخرى):")
        
        if st.button("ابدأ الترانسكريبت من الرابط"):
            if url:
                with st.spinner("جاري تحميل الفيديو..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        video_path = os.path.join(temp_dir, "video.%(ext)s")
                        audio_path = os.path.join(temp_dir, "audio.wav")
                        
                        # تحميل الفيديو
                        if download_video_from_url(url, video_path):
                            # البحث عن الملف المُحمل
                            downloaded_files = list(Path(temp_dir).glob("video.*"))
                            if downloaded_files:
                                actual_video_path = downloaded_files[0]
                                
                                # استخراج الصوت
                                with st.spinner("جاري استخراج الصوت..."):
                                    if extract_audio(str(actual_video_path), audio_path):
                                        # عمل الترانسكريبت
                                        with st.spinner("جاري تحويل الصوت إلى نص..."):
                                            transcript = transcribe_audio(
                                                audio_path, 
                                                model, 
                                                language if language != "auto" else None
                                            )
                                            
                                            if transcript:
                                                st.success("تم الترانسكريبت بنجاح!")
                                                st.text_area("النص المُستخرج:", transcript, height=300)
                                                
                                                # إمكانية تحميل النص
                                                st.download_button(
                                                    label="تحميل النص",
                                                    data=transcript,
                                                    file_name="transcript.txt",
                                                    mime="text/plain"
                                                )
            else:
                st.warning("يرجى إدخال رابط الفيديو")
    
    else:  # رفع ملف
        uploaded_file = st.file_uploader(
            "اختر ملف فيديو أو صوت:",
            type=['mp4', 'avi', 'mov', 'mp3', 'wav', 'm4a', 'flac']
        )
        
        if uploaded_file is not None:
            if st.button("ابدأ الترانسكريبت من الملف"):
                with st.spinner("جاري معالجة الملف..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # حفظ الملف المرفوع
                        uploaded_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(uploaded_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # تحديد نوع الملف
                        file_ext = Path(uploaded_file.name).suffix.lower()
                        
                        if file_ext in ['.mp3', '.wav', '.m4a', '.flac']:
                            # ملف صوتي
                            audio_path = uploaded_path
                        else:
                            # ملف فيديو - استخراج الصوت
                            audio_path = os.path.join(temp_dir, "audio.wav")
                            with st.spinner("جاري استخراج الصوت..."):
                                if not extract_audio(uploaded_path, audio_path):
                                    return
                        
                        # عمل الترانسكريبت
                        with st.spinner("جاري تحويل الصوت إلى نص..."):
                            transcript = transcribe_audio(
                                audio_path, 
                                model, 
                                language if language != "auto" else None
                            )
                            
                            if transcript:
                                st.success("تم الترانسكريبت بنجاح!")
                                st.text_area("النص المُستخرج:", transcript, height=300)
                                
                                # إمكانية تحميل النص
                                st.download_button(
                                    label="تحميل النص",
                                    data=transcript,
                                    file_name=f"transcript_{uploaded_file.name}.txt",
                                    mime="text/plain"
                                )

# معلومات التثبيت
with st.expander("معلومات التثبيت"):
    st.markdown("""
    ### المكتبات المطلوبة:
    ```bash
    pip install streamlit
    pip install openai-whisper
    pip install yt-dlp
    pip install ffmpeg-python
    ```
    
    ### تثبيت FFmpeg:
    - **Windows**: تحميل من https://ffmpeg.org/download.html
    - **macOS**: `brew install ffmpeg`
    - **Linux**: `sudo apt install ffmpeg`
    
    ### تشغيل التطبيق:
    ```bash
    streamlit run app.py
    ```
    """)

if __name__ == "__main__":
    main()
