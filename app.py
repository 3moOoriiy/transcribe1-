import os
import tempfile
import streamlit as st
import whisper
import yt_dlp
from urllib.parse import urlparse, parse_qs
import re
import time
from datetime import datetime
import logging
import sys

# إعداد الـ logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد الصفحة
st.set_page_config(
    page_title="Video Transcriber (Local Whisper)", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎥 مفرغ الفيديوهات بـ Whisper المحلي 🚀")
st.markdown("أدخل رابط فيديو YouTube لتفريغه نصياً بدون الحاجة لـ OpenAI API")

def check_dependencies():
    """التحقق من توفر المكتبات المطلوبة"""
    missing = []
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    # التحقق من ffmpeg
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("ffmpeg")
    
    return missing

def display_installation_guide(missing_deps):
    """عرض دليل التثبيت للمكتبات المفقودة"""
    st.error("❌ مكتبات مطلوبة غير مثبتة:")
    
    for dep in missing_deps:
        st.code(f"pip install {dep}")
    
    if "ffmpeg" in missing_deps:
        st.markdown("""
        **لتثبيت FFmpeg:**
        - **Windows:** قم بتحميله من [ffmpeg.org](https://ffmpeg.org/download.html)
        - **macOS:** `brew install ffmpeg`
        - **Linux:** `sudo apt install ffmpeg` أو `sudo yum install ffmpeg`
        """)
    
    st.stop()

def sanitize_youtube_url(url: str) -> str:
    """استخلاص video_id وإرجاع رابط نظيف"""
    url = url.strip()
    
    # معالجة روابط youtu.be
    if "youtu.be" in url:
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # معالجة روابط shorts
    shorts_match = re.search(r'/shorts/([a-zA-Z0-9_-]+)', url)
    if shorts_match:
        video_id = shorts_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # معالجة الروابط العادية
    parsed = urlparse(url)
    if parsed.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    
    return url

def validate_youtube_url(url: str) -> bool:
    """التحقق من صحة رابط YouTube"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'https?://m\.youtube\.com/watch\?v=[\w-]+'
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

@st.cache_data(ttl=300)  # cache لمدة 5 دقائق
def get_video_info(url: str):
    """الحصول على معلومات الفيديو"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'غير متوفر'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'غير متوفر'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', '')
            }
    except Exception as e:
        logger.error(f"خطأ في استخراج معلومات الفيديو: {e}")
        return None

def download_audio_robust(url: str, output_path: str, progress_callback=None):
    """تحميل صوت محسن مع معالجة أفضل للأخطاء"""
    
    class ProgressHook:
        def __init__(self, callback):
            self.callback = callback
            
        def __call__(self, d):
            if self.callback and d['status'] == 'downloading':
                if 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    self.callback(percent)
    
    # إعداد خيارات التحميل
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": output_path.rsplit('.', 1)[0] + '.%(ext)s',
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
        "audioformat": "wav",
        "audioquality": 0,  # أفضل جودة
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "prefer_ffmpeg": True,
        "keepvideo": False,
    }
    
    if progress_callback:
        ydl_opts['progress_hooks'] = [ProgressHook(progress_callback)]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            # البحث عن الملف المحمل
            possible_extensions = ['.wav', '.m4a', '.webm', '.mp3', '.ogg']
            base_path = output_path.rsplit('.', 1)[0]
            
            for ext in possible_extensions:
                test_path = base_path + ext
                if os.path.exists(test_path) and os.path.getsize(test_path) > 0:
                    # إعادة تسمية الملف إذا لزم الأمر
                    if test_path != output_path:
                        import shutil
                        try:
                            shutil.move(test_path, output_path)
                        except Exception as e:
                            logger.warning(f"لم يتم نقل الملف: {e}")
                            # استخدام الملف كما هو
                            return test_path
                    return output_path
            
            return None
            
    except Exception as e:
        logger.error(f"خطأ في تحميل الصوت: {e}")
        return None

@st.cache_resource
def load_whisper_model(model_size: str):
    """تحميل نموذج Whisper مع cache"""
    try:
        model = whisper.load_model(model_size)
        return model
    except Exception as e:
        logger.error(f"خطأ في تحميل النموذج: {e}")
        return None

def transcribe_audio(model, audio_path: str, language: str = "auto"):
    """تفريغ الصوت مع خيارات محسنة"""
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"ملف الصوت غير موجود: {audio_path}")
    
    # إعداد خيارات التفريغ
    transcribe_options = {
        "task": "transcribe",
        "fp16": False,
        "temperature": 0.0,
        "compression_ratio_threshold": 2.4,
        "logprob_threshold": -1.0,
        "no_speech_threshold": 0.6,
    }
    
    # إضافة اللغة إذا لم تكن auto
    if language != "auto":
        transcribe_options["language"] = language
    
    # خيارات للنماذج الكبيرة
    if hasattr(model, 'is_multilingual') and model.is_multilingual:
        transcribe_options.update({
            "beam_size": 5,
            "best_of": 5,
            "patience": 1.0
        })
    
    try:
        result = model.transcribe(audio_path, **transcribe_options)
        return result
    except Exception as e:
        logger.error(f"خطأ في التفريغ: {e}")
        raise

def format_time(seconds):
    """تنسيق الوقت بصيغة SRT"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def create_srt_content(segments):
    """إنشاء محتوى ملف SRT"""
    srt_content = ""
    for i, segment in enumerate(segments):
        start_time = format_time(segment["start"])
        end_time = format_time(segment["end"])
        
        srt_content += f"{i+1}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{segment['text'].strip()}\n\n"
    
    return srt_content

# التحقق من المتطلبات
missing_deps = check_dependencies()
if missing_deps:
    display_installation_guide(missing_deps)

# واجهة المستخدم الرئيسية
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    video_url = st.text_input(
        "🔗 رابط الفيديو", 
        placeholder="https://www.youtube.com/watch?v=...",
        help="يدعم روابط YouTube العادية و Shorts و youtu.be"
    )

with col2:
    model_size = st.selectbox(
        "🤖 حجم النموذج",
        ["tiny", "base", "small", "medium", "large"],
        index=2,
        help="النماذج الأكبر أدق لكن أبطأ"
    )

with col3:
    language = st.selectbox(
        "🌍 اللغة",
        {
            "auto": "كشف تلقائي",
            "ar": "العربية",
            "en": "الإنجليزية", 
            "fr": "الفرنسية",
            "es": "الإسبانية",
            "de": "الألمانية",
            "it": "الإيطالية",
            "pt": "البرتغالية",
            "ru": "الروسية",
            "ja": "اليابانية",
            "ko": "الكورية",
            "zh": "الصينية"
        },
        index=1
    )

# معلومات النماذج
with st.expander("ℹ️ دليل اختيار النموذج"):
    model_info = {
        "tiny": {"size": "39 MB", "speed": "⚡⚡⚡", "accuracy": "⭐⭐", "best_for": "اختبار سريع"},
        "base": {"size": "74 MB", "speed": "⚡⚡", "accuracy": "⭐⭐⭐", "best_for": "فيديوهات قصيرة"},
        "small": {"size": "244 MB", "speed": "⚡", "accuracy": "⭐⭐⭐⭐", "best_for": "الاستخدام العام"},
        "medium": {"size": "769 MB", "speed": "🐌", "accuracy": "⭐⭐⭐⭐⭐", "best_for": "دقة عالية"},
        "large": {"size": "1.55 GB", "speed": "🐌🐌", "accuracy": "⭐⭐⭐⭐⭐", "best_for": "أقصى دقة"}
    }
    
    for model, info in model_info.items():
        col_model, col_size, col_speed, col_acc, col_use = st.columns(5)
        with col_model:
            st.write(f"**{model}**")
        with col_size:
            st.write(info["size"])
        with col_speed:
            st.write(info["speed"])
        with col_acc:
            st.write(info["accuracy"])
        with col_use:
            st.write(info["best_for"])

# عرض معلومات الفيديو عند إدخال الرابط
if video_url and validate_youtube_url(video_url):
    clean_url = sanitize_youtube_url(video_url)
    video_info = get_video_info(clean_url)
    
    if video_info:
        col_info, col_thumb = st.columns([2, 1])
        
        with col_info:
            st.success(f"📹 **{video_info['title'][:100]}{'...' if len(video_info['title']) > 100 else ''}**")
            
            duration_minutes = video_info['duration'] // 60
            duration_seconds = video_info['duration'] % 60
            st.info(f"⏱️ المدة: {duration_minutes:02d}:{duration_seconds:02d}")
            st.info(f"👤 القناة: {video_info['uploader']}")
            
            if video_info['view_count']:
                st.info(f"👁️ المشاهدات: {video_info['view_count']:,}")
        
        with col_thumb:
            if video_info.get('thumbnail'):
                st.image(video_info['thumbnail'], width=200)
        
        # تحذيرات للفيديوهات الطويلة
        if duration_minutes > 10 and model_size in ["large", "medium"]:
            st.error(f"⚠️ **تحذير:** الفيديو طويل ({duration_minutes} دقيقة) والنموذج كبير!")
            st.error("قد يؤدي هذا لبطء شديد أو تعليق التطبيق")
        elif duration_minutes > 15:
            st.warning(f"⚠️ الفيديو طويل جداً ({duration_minutes} دقيقة)")

# زر بدء التفريغ
if st.button("🚀 بدء التفريغ النصي", type="primary", use_container_width=True):
    if not video_url.strip():
        st.warning("⚠️ الرجاء إدخال رابط فيديو")
    elif not validate_youtube_url(video_url.strip()):
        st.error("❌ رابط YouTube غير صالح")
    else:
        clean_url = sanitize_youtube_url(video_url.strip())
        
        # المتغيرات
        temp_audio_path = None
        model = None
        
        try:
            # الخطوة 1: تحميل الصوت
            with st.spinner("⏳ جاري تحميل الصوت..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(percent):
                    progress_bar.progress(min(percent, 100) / 100)
                    status_text.text(f"تحميل الصوت: {percent:.1f}%")
                
                temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_audio.close()
                temp_audio_path = temp_audio.name
                
                audio_file = download_audio_robust(clean_url, temp_audio_path, update_progress)
                
                if not audio_file or not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                    st.error("❌ فشل في تحميل الصوت")
                    st.stop()
                
                file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
                st.success(f"✅ تم تحميل الصوت! ({file_size_mb:.1f} MB)")
                temp_audio_path = audio_file
            
            # الخطوة 2: تحميل النموذج
            with st.spinner(f"🤖 جاري تحميل نموذج {model_size}..."):
                model = load_whisper_model(model_size)
                if not model:
                    st.error("❌ فشل في تحميل النموذج")
                    st.stop()
                st.success("✅ تم تحميل النموذج!")
            
            # الخطوة 3: التفريغ النصي
            with st.spinner("📝 جاري التفريغ النصي..."):
                start_time = time.time()
                
                result = transcribe_audio(model, temp_audio_path, language)
                
                if not result or not result.get("text", "").strip():
                    st.warning("⚠️ لم يتم العثور على نص في الصوت")
                    st.stop()
                
                processing_time = time.time() - start_time
                transcript = result["text"].strip()
                
                st.success(f"✅ تم التفريغ بنجاح! (استغرق {processing_time:.1f} ثانية)")
            
            # عرض النتائج
            st.markdown("---")
            st.subheader("📄 النص المفرغ")
            
            # إحصائيات
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                st.metric("🌍 اللغة المكتشفة", result.get("language", "غير محدد"))
            with col_stat2:
                st.metric("🔤 عدد الأحرف", len(transcript))
            with col_stat3:
                st.metric("📝 عدد الكلمات", len(transcript.split()))
            with col_stat4:
                st.metric("⏱️ وقت المعالجة", f"{processing_time:.1f}s")
            
            # النص
            st.text_area("", transcript, height=300, key="transcript_output")
            
            # أزرار التحميل
            col_dl1, col_dl2 = st.columns(2)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            with col_dl1:
                st.download_button(
                    label="💾 تحميل النص (.txt)",
                    data=transcript,
                    file_name=f"transcript_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_dl2:
                if "segments" in result and result["segments"]:
                    srt_content = create_srt_content(result["segments"])
                    st.download_button(
                        label="💾 تحميل الترجمة (.srt)",
                        data=srt_content,
                        file_name=f"subtitles_{timestamp}.srt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.info("الطوابع الزمنية غير متوفرة")
            
            # عرض المقاطع الزمنية
            if "segments" in result and result["segments"]:
                with st.expander("⏱️ عرض النص مع الطوابع الزمنية"):
                    for i, segment in enumerate(result["segments"]):
                        start_min = int(segment["start"] // 60)
                        start_sec = int(segment["start"] % 60)
                        end_min = int(segment["end"] // 60)
                        end_sec = int(segment["end"] % 60)
                        
                        st.markdown(f"**[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]** {segment['text'].strip()}")
                        
                        if i < len(result["segments"]) - 1:
                            st.markdown("---")
        
        except Exception as e:
            st.error(f"❌ حدث خطأ: {str(e)}")
            logger.error(f"خطأ عام: {e}", exc_info=True)
        
        finally:
            # تنظيف الملفات المؤقتة
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass

# نصائح وإرشادات
st.markdown("---")
st.markdown("### 💡 نصائح لتحسين الأداء:")

col_tip1, col_tip2 = st.columns(2)

with col_tip1:
    st.markdown("""
    **🎯 للحصول على أفضل دقة:**
    - اختر اللغة الصحيحة
    - استخدم "medium" للمحتوى المهم
    - تأكد من جودة الصوت
    - تجنب الضوضاء الكثيرة
    """)

with col_tip2:
    st.markdown("""
    **⚡ لتجنب البطء:**
    - استخدم "small" للفيديوهات الطويلة
    - تجنب "large" إلا للضرورة القصوى
    - أغلق التطبيقات الأخرى
    - جرب فيديوهات قصيرة أولاً
    """)

# معلومات إضافية
st.info("""
🚀 **النموذج المُوصى به:** "small" - يوفر توازن ممتاز بين السرعة والدقة

🔧 **متطلبات النظام:**
- Python 3.8+
- FFmpeg مثبت
- ذاكرة RAM كافية (4GB+ للنماذج الكبيرة)
""")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "مفرغ الفيديوهات بتقنية Whisper | مفتوح المصدر ومجاني 🆓"
    "</div>", 
    unsafe_allow_html=True
)
