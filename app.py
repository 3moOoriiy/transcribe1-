import os
import tempfile
import streamlit as st
import whisper
import yt_dlp
from urllib.parse import urlparse, parse_qs
import re
import threading
import time
from datetime import datetime

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube (عادي أو Shorts أو youtu.be) لترانسكريبت محلي بدون OpenAI.")

# إضافة session state للتحكم في العملية
if 'transcription_running' not in st.session_state:
    st.session_state.transcription_running = False

def sanitize_youtube_url(url: str) -> str:
    """
    يستخلص video_id من الرابط ويعيد رابط نظيف من نوع watch?v=VIDEO_ID
    """
    url = url.strip()
    
    if "youtu.be" in url:
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    shorts_match = re.search(r'/shorts/([a-zA-Z0-9_-]+)', url)
    if shorts_match:
        video_id = shorts_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    parsed = urlparse(url)
    if parsed.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    
    return url

def get_video_info(url: str):
    """
    الحصول على معلومات الفيديو قبل التحميل
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'غير متوفر'),
                'duration': info.get('duration', 0),
                'language': info.get('language', 'auto'),
                'uploader': info.get('uploader', 'غير متوفر')
            }
    except Exception as e:
        st.warning(f"تعذر الحصول على معلومات الفيديو: {str(e)}")
        return None

def download_audio_optimized(url: str, output_path: str, max_duration=None):
    """
    تحميل صوت محسن مع خيارات أفضل للدقة
    """
    base_path = output_path.rsplit('.', 1)[0]
    
    # خيارات محسنة للصوت عالي الجودة
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": base_path + '.%(ext)s',
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
        "audioformat": "wav",
        "audioquality": "0",  # أفضل جودة
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",  # أفضل جودة
        }],
        "prefer_ffmpeg": True,
    }
    
    # إضافة حد زمني إذا كان الفيديو طويل جداً
    if max_duration:
        ydl_opts["postprocessor_args"] = ["-t", str(max_duration)]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            # البحث عن الملف المحمل
            for ext in ['.wav', '.m4a', '.webm', '.mp3']:
                test_path = base_path + ext
                if os.path.exists(test_path) and os.path.getsize(test_path) > 1000:  # أكبر من 1KB
                    final_path = base_path + '.wav'
                    if test_path != final_path:
                        os.rename(test_path, final_path)
                    return final_path
            
        return None
    except Exception as e:
        st.error(f"خطأ في تحميل الصوت: {str(e)}")
        return None

def validate_youtube_url(url: str) -> bool:
    """
    يتحقق من صحة رابط YouTube
    """
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'https?://m\.youtube\.com/watch\?v=[\w-]+'
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def transcribe_with_progress(model, audio_path, language, progress_placeholder):
    """
    تفريغ نصي مع عرض التقدم
    """
    try:
        # خيارات محسنة للدقة
        transcribe_options = {
            "language": language if language != "auto" else None,
            "task": "transcribe",
            "fp16": False,  # تحسين الدقة
            "temperature": 0.0,  # أقل عشوائية، أكثر دقة
            "best_of": 5,  # جرب عدة مرات واختر الأفضل
            "beam_size": 5,  # بحث أفضل
            "patience": 1.0,
            "length_penalty": 1.0,
            "suppress_tokens": [-1],  # إزالة الرموز غير المرغوبة
            "initial_prompt": None,
            "condition_on_previous_text": True,
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_captions_threshold": 0.6,
        }
        
        # إزالة الخيارات التي لا يدعمها النموذج الصغير
        if hasattr(model, 'is_multilingual') and not model.is_multilingual:
            transcribe_options.pop("best_of", None)
            transcribe_options.pop("beam_size", None)
            transcribe_options.pop("patience", None)
            transcribe_options.pop("length_penalty", None)
        
        result = model.transcribe(audio_path, **transcribe_options)
        return result
        
    except Exception as e:
        st.error(f"خطأ في التفريغ النصي: {str(e)}")
        return None

# واجهة المستخدم
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    video_url = st.text_input("رابط الفيديو (YouTube أو Shorts أو youtu.be)", 
                             placeholder="https://www.youtube.com/watch?v=...")

with col2:
    model_size = st.selectbox(
        "حجم نموذج Whisper",
        ["tiny", "base", "small", "medium", "large"],
        index=2,
        help="النماذج الأكبر أدق لكن أبطأ",
        disabled=st.session_state.transcription_running
    )

with col3:
    language = st.selectbox(
        "اللغة",
        ["auto", "ar", "en", "fr", "es", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        index=0,
        help="auto للكشف التلقائي",
        disabled=st.session_state.transcription_running
    )

# إضافة خيارات متقدمة
with st.expander("⚙️ خيارات متقدمة"):
    col_a, col_b = st.columns(2)
    with col_a:
        max_duration = st.number_input(
            "الحد الأقصى للمدة (ثواني، 0 = بلا حد)",
            min_value=0,
            max_value=3600,
            value=0,
            help="يحدد طول الفيديو المراد تفريغه"
        )
    with col_b:
        chunk_processing = st.checkbox(
            "معالجة بالأجزاء (للفيديوهات الطويلة)",
            value=True,
            help="يقسم الصوت لأجزاء صغيرة لتحسين الأداء"
        )

# معلومات النماذج
with st.expander("ℹ️ معلومات عن أحجام النماذج"):
    st.markdown("""
    | النموذج | الحجم | السرعة | الدقة | الاستخدام المناسب |
    |---------|-------|--------|-------|------------------|
    | **tiny** | ~39 MB | ⚡⚡⚡⚡⚡ | ⭐⭐ | اختبار سريع |
    | **base** | ~74 MB | ⚡⚡⚡⚡ | ⭐⭐⭐ | استخدام يومي |
    | **small** | ~244 MB | ⚡⚡⚡ | ⭐⭐⭐⭐ | **موصى به** |
    | **medium** | ~769 MB | ⚡⚡ | ⭐⭐⭐⭐⭐ | دقة عالية |
    | **large** | ~1550 MB | ⚡ | ⭐⭐⭐⭐⭐ | أقصى دقة |
    
    ⚠️ **تحذير:** النماذج الكبيرة قد تستغرق وقتاً طويلاً وتستهلك ذاكرة كبيرة
    """)

# أزرار التحكم
col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])

with col_btn1:
    start_btn = st.button(
        "🚀 بدء التفريغ النصي", 
        type="primary",
        disabled=st.session_state.transcription_running
    )

with col_btn2:
    if st.session_state.transcription_running:
        if st.button("⏹️ إيقاف"):
            st.session_state.transcription_running = False
            st.rerun()

with col_btn3:
    if st.button("🔄 مسح"):
        if 'transcript_result' in st.session_state:
            del st.session_state.transcript_result
        st.rerun()

# معالجة بدء التفريغ
if start_btn:
    if not video_url.strip():
        st.warning("⚠️ الرجاء إدخال رابط فيديو صالح.")
    elif not validate_youtube_url(video_url.strip()):
        st.error("❌ الرابط المدخل ليس رابط YouTube صالح.")
    else:
        st.session_state.transcription_running = True
        clean_url = sanitize_youtube_url(video_url.strip())
        
        # عرض معلومات الفيديو
        st.info(f"🔗 استخدام الرابط: {clean_url}")
        
        video_info = get_video_info(clean_url)
        if video_info:
            st.success(f"📹 **{video_info['title']}**")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info(f"⏱️ المدة: {video_info['duration']//60}:{video_info['duration']%60:02d}")
            with col_info2:
                st.info(f"👤 القناة: {video_info['uploader']}")
            
            # تحذير للفيديوهات الطويلة
            if video_info['duration'] > 600:  # أكثر من 10 دقائق
                st.warning(f"⚠️ الفيديو طويل ({video_info['duration']//60} دقيقة). قد يستغرق وقتاً طويلاً.")
                if model_size in ["large", "medium"]:
                    st.error("❌ ننصح باستخدام نموذج أصغر للفيديوهات الطويلة لتجنب تعليق الموقع.")
                    st.session_state.transcription_running = False
                    st.stop()
        
        # إنشاء حاويات لعرض التقدم
        progress_container = st.container()
        result_container = st.container()
        
        temp_audio = None
        
        try:
            # تحميل الصوت
            with progress_container:
                with st.spinner("⏳ جاري تحميل الصوت..."):
                    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    temp_audio.close()
                    
                    duration_limit = max_duration if max_duration > 0 else None
                    audio_path = download_audio_optimized(clean_url, temp_audio.name, duration_limit)
                    
                    if not audio_path or not os.path.exists(audio_path):
                        st.error("❌ فشل في تحميل الصوت من الفيديو.")
                        st.info("🔧 تأكد من أن FFmpeg مثبت على النظام")
                        st.session_state.transcription_running = False
                        st.stop()
                    
                    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
                    st.success(f"✅ تم تحميل الصوت بنجاح! ({file_size_mb:.1f} MB)")
            
            # تحميل النموذج
            with progress_container:
                with st.spinner(f"🤖 جاري تحميل نموذج Whisper ({model_size})..."):
                    try:
                        # تحذير للنماذج الكبيرة
                        if model_size == "large":
                            st.warning("⚠️ النموذج الكبير قد يستغرق عدة دقائق لتحميل...")
                        
                        model = whisper.load_model(model_size)
                        st.success("✅ تم تحميل النموذج بنجاح!")
                        
                    except Exception as e:
                        st.error(f"❌ خطأ في تحميل نموذج Whisper: {str(e)}")
                        st.session_state.transcription_running = False
                        st.stop()
            
            # التفريغ النصي
            with progress_container:
                progress_placeholder = st.empty()
                with st.spinner("📝 جاري التفريغ النصي... (قد يستغرق عدة دقائق)"):
                    
                    start_time = time.time()
                    result = transcribe_with_progress(
                        model, audio_path, language, progress_placeholder
                    )
                    end_time = time.time()
                    
                    if result is None:
                        st.error("❌ فشل في التفريغ النصي")
                        st.session_state.transcription_running = False
                        st.stop()
                    
                    transcript = result["text"].strip()
                    processing_time = end_time - start_time
                    
                    if not transcript:
                        st.warning("⚠️ لم يتم العثور على نص في الصوت.")
                        st.info("💡 جرب:")
                        st.info("- تأكد من وجود كلام في الفيديو")
                        st.info("- استخدم نموذج أكبر للدقة الأفضل")
                        st.info("- تحقق من اختيار اللغة الصحيحة")
                    else:
                        # حفظ النتيجة في session state
                        st.session_state.transcript_result = {
                            'text': transcript,
                            'language': result.get('language', 'غير محدد'),
                            'model': model_size,
                            'processing_time': processing_time,
                            'video_info': video_info,
                            'segments': result.get('segments', [])
                        }
                        
                        st.success(f"✅ تم التفريغ النصي بنجاح! ({processing_time:.1f} ثانية)")
                        
        except Exception as e:
            st.error(f"❌ حدث خطأ عام: {str(e)}")
            
        finally:
            # تنظيف الملفات المؤقتة
            if temp_audio and os.path.exists(temp_audio.name):
                try:
                    os.unlink(temp_audio.name)
                except:
                    pass
            
            st.session_state.transcription_running = False

# عرض النتائج المحفوظة
if 'transcript_result' in st.session_state:
    result = st.session_state.transcript_result
    
    st.subheader("📄 النص المفرغ")
    
    # تبويبات للعرض
    tab1, tab2, tab3 = st.tabs(["📝 النص الكامل", "⏱️ النص المقسم زمنياً", "📊 الإحصائيات"])
    
    with tab1:
        st.text_area("", result['text'], height=300, key="transcript_display")
        
        # أزرار التحميل
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="💾 تحميل النص (.txt)",
                data=result['text'],
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col_dl2:
            # تحميل مع الطوابع الزمنية
            if result.get('segments'):
                srt_content = ""
                for i, segment in enumerate(result['segments']):
                    start_time = f"{int(segment['start']//3600):02d}:{int((segment['start']%3600)//60):02d}:{segment['start']%60:06.3f}"
                    end_time = f"{int(segment['end']//3600):02d}:{int((segment['end']%3600)//60):02d}:{segment['end']%60:06.3f}"
                    srt_content += f"{i+1}\n{start_time} --> {end_time}\n{segment['text'].strip()}\n\n"
                
                st.download_button(
                    label="💾 تحميל SRT",
                    data=srt_content,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                    mime="text/plain"
                )
    
    with tab2:
        if result.get('segments'):
            for i, segment in enumerate(result['segments']):
                start_min = int(segment['start'] // 60)
                start_sec = int(segment['start'] % 60)
                end_min = int(segment['end'] // 60)
                end_sec = int(segment['end'] % 60)
                
                st.markdown(f"**[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]**")
                st.markdown(f"{segment['text'].strip()}")
                st.markdown("---")
        else:
            st.info("الطوابع الزمنية غير متوفرة لهذا النموذج")
    
    with tab3:
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("🔤 عدد الأحرف", len(result['text']))
            st.metric("📝 عدد الكلمات", len(result['text'].split()))
        
        with col_stat2:
            st.metric("🌍 اللغة المكتشفة", result['language'])
            st.metric("🤖 النموذج المستخدم", result['model'])
        
        with col_stat3:
            st.metric("⏱️ وقت المعالجة", f"{result['processing_time']:.1f}s")
            if result.get('segments'):
                st.metric("📊 عدد المقاطع", len(result['segments']))

# تذييل مع نصائح
st.markdown("---")
st.markdown("""
### 💡 نصائح لتحسين النتائج:

**للدقة الأفضل:**
- استخدم النماذج الأكبر (medium/large) للمحتوى المهم
- تأكد من جودة الصوت الجيدة في الفيديو
- اختر اللغة الصحيحة بدلاً من "auto"

**لتجنب تعليق الموقع:**
- استخدم النماذج الصغيرة (tiny/base/small) للفيديوهات الطويلة
- حدد الحد الأقصى للمدة للفيديوهات الطويلة
- فعل خيار "معالجة بالأجزاء"

**للسرعة:**
- النموذج "small" يوفر توازن جيد بين السرعة والدقة
- تجنب النماذج الكبيرة للاختبار السريع
""")

st.markdown("""
<div style='text-align: center; color: #666; margin-top: 2rem;'>
    <small>🔧 Built with Streamlit, Whisper & yt-dlp | 
    💡 للحصول على أفضل النتائج، استخدم فيديوهات بصوت واضح</small>
</div>
""", unsafe_allow_html=True)
