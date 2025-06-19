import streamlit as st
import speech_recognition as sr
import tempfile
import os
import io
import time
from datetime import datetime

# استيراد المكتبات الثقيلة فقط عند الحاجة
@st.cache_resource
def load_heavy_libraries():
    """تحميل المكتبات الثقيلة مرة واحدة فقط"""
    try:
        from moviepy.editor import VideoFileClip
        from pydub import AudioSegment
        from pydub.utils import make_chunks
        return VideoFileClip, AudioSegment, make_chunks
    except ImportError as e:
        st.error(f"خطأ في تحميل المكتبات: {str(e)}")
        st.info("تأكد من تثبيت جميع المتطلبات باستخدام: pip install -r requirements.txt")
        return None, None, None

# إعداد الصفحة مع تحسينات للسرعة
st.set_page_config(
    page_title="Video Transcription",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إخفاء الكود الإضافي من Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# العنوان والوصف
st.title("🎬 أداة تحويل الفيديو إلى نص")
st.markdown("**قم برفع فيديو وسيتم استخراج النص منه تلقائياً**")

# دالة سريعة لاستخراج الصوت
@st.cache_data
def extract_audio_from_video(video_path, _progress_callback=None):
    """استخراج الصوت من الفيديو بطريقة محسنة"""
    VideoFileClip, _, _ = load_heavy_libraries()
    if not VideoFileClip:
        return None
        
    try:
        if _progress_callback:
            _progress_callback("جاري تحميل الفيديو...")
            
        video = VideoFileClip(video_path)
        
        if _progress_callback:
            _progress_callback("جاري استخراج الصوت...")
            
        audio = video.audio
        
        # إنشاء ملف مؤقت للصوت
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
            audio_path = temp_audio.name
        
        # تنظيف الذاكرة
        video.close()
        audio.close()
        
        return audio_path
    except Exception as e:
        st.error(f"خطأ في استخراج الصوت: {str(e)}")
        return None

# دالة محسنة لتقسيم الصوت
def split_audio_optimized(audio_path, chunk_length_ms=20000):
    """تقسيم الصوت بطريقة محسنة"""
    _, AudioSegment, make_chunks = load_heavy_libraries()
    if not AudioSegment:
        return None
        
    try:
        audio = AudioSegment.from_wav(audio_path)
        # تحسين جودة الصوت للتعرف الأفضل
        audio = audio.set_frame_rate(16000).set_channels(1)
        chunks = make_chunks(audio, chunk_length_ms)
        return chunks
    except Exception as e:
        st.error(f"خطأ في تقسيم الصوت: {str(e)}")
        return None

# دالة محسنة للتعرف على الكلام
def transcribe_audio_chunk_fast(audio_chunk, language='ar-EG', timeout=10):
    """تحويل جزء من الصوت إلى نص بطريقة سريعة"""
    recognizer = sr.Recognizer()
    
    # تحسين إعدادات التعرف
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5
    
    try:
        # تحويل AudioSegment إلى bytes
        wav_io = io.BytesIO()
        audio_chunk.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # التعرف على الكلام مع timeout
        with sr.AudioFile(wav_io) as source:
            # تقليل الضوضاء
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)
            
        # استخدام Google Speech Recognition مع timeout
        text = recognizer.recognize_google(
            audio_data, 
            language=language,
            show_all=False
        )
        return text
        
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "[خطأ في الاتصال]"
    except Exception:
        return ""

# الواجهة الرئيسية
def main():
    # إعدادات سريعة في الشريط الجانبي
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        
        # اختيار اللغة
        languages = {
            "🇪🇬 العربية": "ar-EG",
            "🇺🇸 English": "en-US",
            "🇫🇷 Français": "fr-FR",
            "🇩🇪 Deutsch": "de-DE",
            "🇪🇸 Español": "es-ES"
        }
        
        selected_lang = st.selectbox("اللغة:", list(languages.keys()))
        language_code = languages[selected_lang]
        
        # مدة الجزء
        chunk_duration = st.select_slider(
            "مدة الجزء (ثانية):",
            options=[15, 20, 25, 30, 35, 40],
            value=20
        )
        
        # معلومات مفيدة
        st.info("💡 **نصائح للحصول على أفضل النتائج:**\n"
                "- استخدم فيديو بصوت واضح\n"
                "- تجنب الضوضاء الخلفية\n"
                "- اختر اللغة الصحيحة")
    
    # قسم رفع الملف
    st.header("📁 رفع الفيديو")
    
    # استخدام columns لتحسين التخطيط
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "اختر ملف فيديو (حتى 100MB)",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            help="يدعم: MP4, AVI, MOV, MKV, WebM"
        )
    
    with col2:
        if uploaded_file:
            file_size = uploaded_file.size / (1024*1024)
            st.metric("حجم الملف", f"{file_size:.1f} MB")
            st.metric("النوع", uploaded_file.type.split('/')[-1].upper())
    
    # معالجة الفيديو
    if uploaded_file is not None:
        # التحقق من حجم الملف
        max_size = 100 * 1024 * 1024  # 100MB
        if uploaded_file.size > max_size:
            st.error("⚠️ حجم الملف كبير جداً! الحد الأقصى 100MB")
            return
        
        # زر المعالجة
        if st.button("🚀 بدء استخراج النص", type="primary", use_container_width=True):
            process_video_fast(uploaded_file, language_code, chunk_duration)

def process_video_fast(video_file, language='ar-EG', chunk_duration=20):
    """معالجة الفيديو بطريقة سريعة ومحسنة"""
    
    # إنشاء placeholder للحالة
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    # حفظ الفيديو مؤقتاً
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    try:
        # إنشاء callback للتقدم
        def update_progress(message):
            status_placeholder.info(f"⏳ {message}")
        
        # استخراج الصوت
        audio_path = extract_audio_from_video(video_path, update_progress)
        
        if not audio_path:
            st.error("❌ فشل في استخراج الصوت")
            return
        
        # تقسيم الصوت
        status_placeholder.info("⏳ جاري تقسيم الصوت...")
        chunks = split_audio_optimized(audio_path, chunk_duration * 1000)
        
        if not chunks:
            st.error("❌ فشل في تقسيم الصوت")
            return
        
        # معالجة الأجزاء
        transcript_parts = []
        total_chunks = len(chunks)
        
        # شريط التقدم
        progress_bar = progress_placeholder.progress(0)
        
        for i, chunk in enumerate(chunks):
            # تحديث الحالة
            minutes, seconds = divmod(i * chunk_duration, 60)
            status_placeholder.info(f"⏳ معالجة الدقيقة {minutes:02d}:{seconds:02d} ({i+1}/{total_chunks})")
            
            # التعرف على الكلام
            text = transcribe_audio_chunk_fast(chunk, language)
            
            if text.strip():  # إضافة النص فقط إذا كان غير فارغ
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                transcript_parts.append(f"{timestamp} {text}")
            
            # تحديث التقدم
            progress_bar.progress((i + 1) / total_chunks)
            
            # استراحة قصيرة
            time.sleep(0.1)
        
        # النتيجة النهائية
        if transcript_parts:
            full_transcript = "\n\n".join(transcript_parts)
            
            # عرض النتيجة
            status_placeholder.success("✅ تم الانتهاء بنجاح!")
            progress_placeholder.empty()
            
            st.header("📝 النص المستخرج")
            
            # إحصائيات سريعة
            word_count = len(full_transcript.split())
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("عدد الكلمات", word_count)
            with col2:
                st.metric("عدد الأجزاء", len(transcript_parts))
            with col3:
                estimated_duration = len(chunks) * chunk_duration
                st.metric("المدة المقدرة", f"{estimated_duration//60}:{estimated_duration%60:02d}")
            
            # عرض النص
            st.text_area("النتيجة:", full_transcript, height=300)
            
            # أزرار التحميل
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 تحميل كملف نصي",
                    data=full_transcript,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # تحويل إلى SRT للترجمة
                srt_content = convert_to_srt(transcript_parts, chunk_duration)
                st.download_button(
                    label="📥 تحميل كملف ترجمة (SRT)",
                    data=srt_content,
                    file_name=f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            status_placeholder.warning("⚠️ لم يتم العثور على نص في الفيديو")
            progress_placeholder.empty()
    
    except Exception as e:
        st.error(f"❌ خطأ في المعالجة: {str(e)}")
    
    finally:
        # تنظيف الملفات المؤقتة
        try:
            os.unlink(video_path)
            if 'audio_path' in locals() and audio_path:
                os.unlink(audio_path)
        except:
            pass

def convert_to_srt(transcript_parts, chunk_duration):
    """تحويل النص إلى صيغة SRT للترجمة"""
    srt_content = []
    
    for i, part in enumerate(transcript_parts):
        # استخراج النص بدون timestamp
        text = part.split('] ', 1)[1] if '] ' in part else part
        
        # حساب الأوقات
        start_seconds = i * chunk_duration
        end_seconds = (i + 1) * chunk_duration
        
        # تحويل إلى صيغة SRT
        start_time = f"{start_seconds//3600:02d}:{(start_seconds%3600)//60:02d}:{start_seconds%60:02d},000"
        end_time = f"{end_seconds//3600:02d}:{(end_seconds%3600)//60:02d}:{end_seconds%60:02d},000"
        
        srt_content.append(f"{i+1}\n{start_time} --> {end_time}\n{text}\n")
    
    return "\n".join(srt_content)

if __name__ == "__main__":
    main()
