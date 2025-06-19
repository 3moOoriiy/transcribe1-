import streamlit as st
import speech_recognition as sr
import tempfile
import os
import io
import time
from datetime import datetime
import subprocess

# التحقق من وجود المكتبات وتثبيتها إذا لزم الأمر
def check_and_install_dependencies():
    """التحقق من المكتبات المطلوبة وتثبيتها"""
    required_packages = {
        'moviepy': 'moviepy',
        'pydub': 'pydub',
        'SpeechRecognition': 'SpeechRecognition'
    }
    
    missing_packages = []
    
    for package_name, pip_name in required_packages.items():
        try:
            __import__(package_name.lower().replace('speechrecognition', 'speech_recognition'))
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        st.error(f"المكتبات المطلوبة غير مثبتة: {', '.join(missing_packages)}")
        st.info("يرجى تثبيت المكتبات المطلوبة باستخدام الأوامر التالية:")
        for package in missing_packages:
            st.code(f"pip install {package}")
        return False
    
    return True

# تحميل المكتبات بأمان
@st.cache_resource
def load_libraries():
    """تحميل المكتبات الضرورية مع معالجة الأخطاء"""
    try:
        from moviepy.editor import VideoFileClip
        from pydub import AudioSegment
        from pydub.utils import make_chunks
        return VideoFileClip, AudioSegment, make_chunks, True
    except ImportError as e:
        st.error(f"خطأ في تحميل المكتبات: {str(e)}")
        st.info("""
        **حل المشكلة:**
        
        1. تأكد من تثبيت جميع المكتبات:
        ```
        pip install --upgrade pip
        pip install moviepy pydub SpeechRecognition streamlit
        ```
        
        2. إذا كنت تستخدم Windows، قد تحتاج إلى:
        ```
        pip install --upgrade setuptools wheel
        ```
        
        3. أعد تشغيل التطبيق بعد التثبيت
        """)
        return None, None, None, False

# إعداد الصفحة
st.set_page_config(
    page_title="Video Transcription",
    page_icon="🎬",
    layout="wide"
)

# تنظيف واجهة streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# العنوان
st.title("🎬 أداة تحويل الفيديو إلى نص")
st.markdown("**استخراج النص من الفيديو باستخدام تقنية التعرف على الكلام**")

# التحقق من المكتبات
if not check_and_install_dependencies():
    st.stop()

# تحميل المكتبات
VideoFileClip, AudioSegment, make_chunks, libraries_loaded = load_libraries()

if not libraries_loaded:
    st.stop()

# دالة استخراج الصوت مع معالجة محسنة للأخطاء
def extract_audio_safely(video_path):
    """استخراج الصوت من الفيديو مع معالجة شاملة للأخطاء"""
    try:
        st.info("🔄 جاري تحميل الفيديو...")
        
        # تحميل الفيديو
        video = VideoFileClip(video_path)
        
        if video.audio is None:
            st.error("❌ الفيديو لا يحتوي على صوت!")
            video.close()
            return None
        
        st.info("🔊 جاري استخراج الصوت...")
        
        # استخراج الصوت
        audio = video.audio
        
        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # حفظ الصوت
        audio.write_audiofile(
            temp_path,
            verbose=False,
            logger=None,
            temp_audiofile_folder=tempfile.gettempdir()
        )
        
        # تنظيف الذاكرة
        audio.close()
        video.close()
        
        st.success("✅ تم استخراج الصوت بنجاح")
        return temp_path
        
    except Exception as e:
        st.error(f"❌ خطأ في استخراج الصوت: {str(e)}")
        if 'video' in locals():
            video.close()
        return None

# دالة تقسيم الصوت
def split_audio_safely(audio_path, chunk_duration_ms):
    """تقسيم الصوت مع معالجة الأخطاء"""
    try:
        st.info("✂️ جاري تقسيم الصوت...")
        
        # تحميل الصوت
        audio = AudioSegment.from_wav(audio_path)
        
        # تحسين جودة الصوت
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # تقسيم الصوت
        chunks = make_chunks(audio, chunk_duration_ms)
        
        st.success(f"✅ تم تقسيم الصوت إلى {len(chunks)} جزء")
        return chunks
        
    except Exception as e:
        st.error(f"❌ خطأ في تقسيم الصوت: {str(e)}")
        return None

# دالة التعرف على الكلام المحسنة
def transcribe_chunk_improved(audio_chunk, language):
    """تحويل الصوت إلى نص مع إعدادات محسنة"""
    recognizer = sr.Recognizer()
    
    # إعدادات محسنة
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    recognizer.operation_timeout = 10
    
    try:
        # تحويل إلى wav
        wav_buffer = io.BytesIO()
        audio_chunk.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        # التعرف على الكلام
        with sr.AudioFile(wav_buffer) as source:
            # تقليل الضوضاء
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        # استخدام Google API
        text = recognizer.recognize_google(
            audio_data,
            language=language,
            show_all=False
        )
        
        return text.strip()
        
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"[خطأ في الشبكة: {str(e)}]"
    except Exception as e:
        return f"[خطأ: {str(e)}]"

# الواجهة الرئيسية
def main():
    # الشريط الجانبي
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        
        # اختيار اللغة
        language_options = {
            "🇪🇬 العربية (مصر)": "ar-EG",
            "🇸🇦 العربية (السعودية)": "ar-SA",
            "🇺🇸 الإنجليزية": "en-US",
            "🇬🇧 الإنجليزية (بريطانيا)": "en-GB",
            "🇫🇷 الفرنسية": "fr-FR",
            "🇩🇪 الألمانية": "de-DE",
            "🇪🇸 الإسبانية": "es-ES"
        }
        
        selected_language = st.selectbox(
            "اختر لغة الفيديو:",
            list(language_options.keys())
        )
        language_code = language_options[selected_language]
        
        # مدة الجزء
        chunk_duration = st.select_slider(
            "مدة كل جزء:",
            options=[10, 15, 20, 30, 45, 60],
            value=20,
            format_func=lambda x: f"{x} ثانية"
        )
        
        st.markdown("---")
        st.info("""
        **💡 نصائح للحصول على أفضل النتائج:**
        
        ✅ استخدم فيديو بصوت واضح  
        ✅ تجنب الموسيقى العالية  
        ✅ اختر اللغة الصحيحة  
        ✅ تأكد من وجود اتصال إنترنت
        """)
    
    # القسم الرئيسي
    st.header("📁 رفع الفيديو")
    
    # رفع الملف
    uploaded_file = st.file_uploader(
        "اختر ملف الفيديو (الحد الأقصى: 50MB)",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'],
        help="يدعم جميع صيغ الفيديو الشائعة"
    )
    
    if uploaded_file is not None:
        # عرض معلومات الملف
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 اسم الملف", uploaded_file.name)
        with col2:
            st.metric("📊 الحجم", f"{file_size_mb:.1f} MB")
        with col3:
            st.metric("🎬 النوع", uploaded_file.type.split('/')[-1].upper())
        
        # التحقق من الحجم
        if file_size_mb > 50:
            st.error("⚠️ حجم الملف كبير جداً! الحد الأقصى المسموح 50MB")
            st.info("💡 يمكنك ضغط الفيديو باستخدام أدوات مثل HandBrake أو FFmpeg")
            return
        
        # زر البدء
        if st.button("🚀 بدء استخراج النص", type="primary", use_container_width=True):
            process_video(uploaded_file, language_code, chunk_duration)

def process_video(video_file, language, chunk_duration):
    """معالجة الفيديو الكامل"""
    
    # إنشاء حاويات للتحديث
    status_container = st.empty()
    progress_container = st.empty()
    
    # حفظ الفيديو مؤقتاً
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    try:
        # استخراج الصوت
        audio_path = extract_audio_safely(video_path)
        if not audio_path:
            return
        
        # تقسيم الصوت
        chunks = split_audio_safely(audio_path, chunk_duration * 1000)
        if not chunks:
            return
        
        # معالجة الأجزاء
        status_container.info("🎯 جاري تحويل الصوت إلى نص...")
        
        transcript_segments = []
        progress_bar = progress_container.progress(0)
        
        for i, chunk in enumerate(chunks):
            # حساب الوقت
            start_time = i * chunk_duration
            minutes, seconds = divmod(start_time, 60)
            
            # تحديث الحالة
            status_container.info(f"🔄 معالجة الجزء {i+1}/{len(chunks)} - الوقت: {minutes:02d}:{seconds:02d}")
            
            # التعرف على الكلام
            text = transcribe_chunk_improved(chunk, language)
            
            if text and not text.startswith("["):  # تجاهل الأخطاء
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                transcript_segments.append({
                    'timestamp': timestamp,
                    'text': text,
                    'start_seconds': start_time
                })
            
            # تحديث التقدم
            progress_bar.progress((i + 1) / len(chunks))
            
            # استراحة قصيرة
            time.sleep(0.2)
        
        # عرض النتائج
        if transcript_segments:
            display_results(transcript_segments, video_file.name)
        else:
            status_container.error("❌ لم يتم العثور على نص قابل للقراءة في الفيديو")
            
    except Exception as e:
        st.error(f"❌ خطأ عام في المعالجة: {str(e)}")
        
    finally:
        # تنظيف الملفات المؤقتة
        cleanup_files(video_path, locals().get('audio_path'))

def display_results(segments, filename):
    """عرض النتائج النهائية"""
    st.success("🎉 تم استخراج النص بنجاح!")
    
    # إحصائيات
    total_words = sum(len(seg['text'].split()) for seg in segments)
    total_duration = segments[-1]['start_seconds'] if segments else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 عدد الكلمات", total_words)
    with col2:
        st.metric("🎬 عدد المقاطع", len(segments))
    with col3:
        st.metric("⏱️ المدة الإجمالية", f"{total_duration//60:02d}:{total_duration%60:02d}")
    
    # النص الكامل
    st.header("📄 النص المستخرج")
    
    full_text = "\n\n".join([f"{seg['timestamp']} {seg['text']}" for seg in segments])
    st.text_area("النتيجة النهائية:", full_text, height=300)
    
    # أزرار التحميل
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "📥 تحميل النص الكامل",
            full_text,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        srt_content = create_srt_file(segments)
        st.download_button(
            "🎬 تحميل ملف الترجمة (SRT)",
            srt_content,
            file_name=f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
            mime="text/plain",
            use_container_width=True
        )

def create_srt_file(segments):
    """إنشاء ملف SRT للترجمة"""
    srt_content = []
    
    for i, segment in enumerate(segments):
        start_seconds = segment['start_seconds']
        end_seconds = start_seconds + 30  # افتراض مدة 30 ثانية لكل مقطع
        
        # تحويل إلى صيغة SRT
        start_time = f"{start_seconds//3600:02d}:{(start_seconds%3600)//60:02d}:{start_seconds%60:02d},000"
        end_time = f"{end_seconds//3600:02d}:{(end_seconds%3600)//60:02d}:{end_seconds%60:02d},000"
        
        srt_content.append(f"{i+1}\n{start_time} --> {end_time}\n{segment['text']}\n")
    
    return "\n".join(srt_content)

def cleanup_files(video_path, audio_path=None):
    """تنظيف الملفات المؤقتة"""
    try:
        if os.path.exists(video_path):
            os.unlink(video_path)
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
    except Exception:
        pass  # تجاهل أخطاء التنظيف

if __name__ == "__main__":
    main()
