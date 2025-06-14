import streamlit as st
import tempfile
import os

# إعداد الصفحة
st.set_page_config(
    page_title="مُحوِّل الفيديو إلى نص (مبسط)",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 مُحوِّل الفيديو إلى نص (الإصدار المبسط)")
st.markdown("إصدار مبسط يتطلب تثبيت المكتبات يدوياً")

# التحقق من المكتبات
def check_dependencies():
    """التحقق من المكتبات المطلوبة"""
    missing = []
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    try:
        import ffmpeg
    except ImportError:
        missing.append("ffmpeg-python")
    
    return missing

# فحص المكتبات المفقودة
missing_deps = check_dependencies()

if missing_deps:
    st.error("⚠️ المكتبات التالية مفقودة:")
    for dep in missing_deps:
        st.code(f"pip install {dep}")
    
    st.markdown("### تعليمات التثبيت:")
    st.code("""
# ثبت المكتبات المطلوبة
pip install openai-whisper
pip install yt-dlp  
pip install ffmpeg-python

# للويندوز، قد تحتاج أيضاً إلى:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    """)
    
    st.warning("بعد تثبيت المكتبات، يرجى إعادة تشغيل التطبيق")
    st.stop()

# استيراد المكتبات بعد التحقق
import whisper
import yt_dlp
import ffmpeg

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
    st.success("✅ جميع المكتبات متوفرة!")
    
    # اختيار حجم النموذج
    col1, col2 = st.columns(2)
    
    with col1:
        model_size = st.selectbox(
            "اختر حجم النموذج:",
            ["tiny", "base", "small", "medium", "large"],
            index=1,
            help="النماذج الأكبر أكثر دقة لكن أبطأ"
        )
    
    with col2:
        language = st.selectbox(
            "اختر اللغة:",
            ["auto", "ar", "en", "fr", "es", "de"],
            help="auto للتحديد التلقائي"
        )
    
    # تحميل النموذج
    with st.spinner(f"جاري تحميل النموذج {model_size}..."):
        model = load_whisper_model(model_size)
    
    if model is None:
        st.error("فشل في تحميل النموذج")
        return
    
    st.success(f"✅ تم تحميل النموذج: {model_size}")
    
    # خيارات الإدخال
    input_method = st.radio(
        "اختر طريقة الإدخال:",
        ["رابط فيديو", "رفع ملف من الجهاز"],
        horizontal=True
    )
    
    if input_method == "رابط فيديو":
        url = st.text_input(
            "أدخل رابط الفيديو:",
            placeholder="https://www.youtube.com/watch?v=..."
        )
        
        if st.button("🚀 ابدأ الترانسكريبت من الرابط", type="primary"):
            if url:
                process_video_url(url, model, language)
            else:
                st.warning("⚠️ يرجى إدخال رابط الفيديو")
    
    else:  # رفع ملف
        uploaded_file = st.file_uploader(
            "اختر ملف فيديو أو صوت:",
            type=['mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'm4a', 'flac', 'webm'],
            help="يدعم معظم تنسيقات الفيديو والصوت"
        )
        
        if uploaded_file is not None:
            st.info(f"📁 تم اختيار الملف: {uploaded_file.name}")
            st.info(f"📊 حجم الملف: {uploaded_file.size / 1024 / 1024:.2f} MB")
            
            if st.button("🚀 ابدأ الترانسكريبت من الملف", type="primary"):
                process_uploaded_file(uploaded_file, model, language)

def process_video_url(url, model, language):
    """معالجة رابط الفيديو"""
    with st.spinner("⬇️ جاري تحميل الفيديو..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, "video.%(ext)s")
            audio_path = os.path.join(temp_dir, "audio.wav")
            
            # تحميل الفيديو
            if download_video_from_url(url, video_path):
                # البحث عن الملف المُحمل
                downloaded_files = list(os.listdir(temp_dir))
                video_files = [f for f in downloaded_files if f.startswith("video.")]
                
                if video_files:
                    actual_video_path = os.path.join(temp_dir, video_files[0])
                    
                    # استخراج الصوت
                    with st.spinner("🎵 جاري استخراج الصوت..."):
                        if extract_audio(actual_video_path, audio_path):
                            # عمل الترانسكريبت
                            with st.spinner("📝 جاري تحويل الصوت إلى نص..."):
                                transcript = transcribe_audio(
                                    audio_path, 
                                    model, 
                                    language if language != "auto" else None
                                )
                                
                                if transcript:
                                    display_results(transcript, "video_transcript")
                else:
                    st.error("❌ لم يتم العثور على الملف المُحمل")

def process_uploaded_file(uploaded_file, model, language):
    """معالجة الملف المرفوع"""
    with st.spinner("📁 جاري معالجة الملف..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            # حفظ الملف المرفوع
            uploaded_path = os.path.join(temp_dir, uploaded_file.name)
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # تحديد نوع الملف
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext in ['.mp3', '.wav', '.m4a', '.flac']:
                # ملف صوتي
                audio_path = uploaded_path
            else:
                # ملف فيديو - استخراج الصوت
                audio_path = os.path.join(temp_dir, "audio.wav")
                with st.spinner("🎵 جاري استخراج الصوت..."):
                    if not extract_audio(uploaded_path, audio_path):
                        return
            
            # عمل الترانسكريبت
            with st.spinner("📝 جاري تحويل الصوت إلى نص..."):
                transcript = transcribe_audio(
                    audio_path, 
                    model, 
                    language if language != "auto" else None
                )
                
                if transcript:
                    display_results(transcript, f"transcript_{uploaded_file.name}")

def display_results(transcript, filename_base):
    """عرض النتائج"""
    st.success("✅ تم الترانسكريبت بنجاح!")
    
    # عرض النص في منطقة قابلة للتمرير
    with st.container():
        st.subheader("📄 النص المُستخرج:")
        st.text_area(
            "النص:",
            transcript,
            height=400,
            label_visibility="collapsed"
        )
    
    # إحصائيات النص
    word_count = len(transcript.split())
    char_count = len(transcript)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("عدد الكلمات", word_count)
    with col2:
        st.metric("عدد الأحرف", char_count)
    with col3:
        st.metric("عدد الأسطر", transcript.count('\n') + 1)
    
    # أزرار التحميل
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 تحميل النص (.txt)",
            data=transcript,
            file_name=f"{filename_base}.txt",
            mime="text/plain",
            type="primary"
        )
    
    with col2:
        # تحويل إلى SRT (ترقيم بسيط)
        srt_content = create_simple_srt(transcript)
        st.download_button(
            label="📥 تحميل ترجمات (.srt)",
            data=srt_content,
            file_name=f"{filename_base}.srt",
            mime="text/plain"
        )

def create_simple_srt(transcript):
    """إنشاء ملف SRT بسيط"""
    lines = transcript.split('.')
    srt_content = ""
    
    for i, line in enumerate(lines, 1):
        if line.strip():
            start_time = f"00:00:{(i-1)*3:02d},000"
            end_time = f"00:00:{i*3:02d},000"
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{line.strip()}.\n\n"
    
    return srt_content

# معلومات إضافية
with st.sidebar:
    st.header("ℹ️ معلومات")
    
    st.markdown("""
    ### المميزات:
    - 🎬 دعم روابط يوتيوب ومواقع أخرى
    - 📁 رفع ملفات من الجهاز
    - 🗣️ دعم لغات متعددة
    - 📊 إحصائيات النص
    - 📥 تحميل بتنسيقات مختلفة
    
    ### نماذج Whisper:
    - **tiny**: سريع، دقة أقل
    - **base**: متوازن ⭐
    - **small**: دقة جيدة
    - **medium**: دقة عالية
    - **large**: أعلى دقة، أبطأ
    """)
    
    st.markdown("---")
    st.markdown("🛠️ **مطور بواسطة:** Claude AI")

if __name__ == "__main__":
    main()
