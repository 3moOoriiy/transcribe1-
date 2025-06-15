import os
import tempfile
import streamlit as st
import whisper
import yt_dlp
from urllib.parse import urlparse, parse_qs
import re
import time
from datetime import datetime

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube (عادي أو Shorts أو youtu.be) لترانسكريبت محلي بدون OpenAI.")

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

def get_video_duration(url: str):
    """
    الحصول على مدة الفيديو قبل التحميل
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'غير متوفر'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'غير متوفر')
            }
    except:
        return None

def download_audio_simple(url: str, output_path: str):
    """
    تحميل صوت مبسط وموثوق
    """
    # إزالة امتداد الملف من المسار للسماح لـ yt-dlp بتحديد الامتداد
    output_template = output_path.rsplit('.', 1)[0] + '.%(ext)s'
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "prefer_ffmpeg": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            
            # البحث عن الملف المحمل
            possible_extensions = ['.wav', '.webm', '.m4a', '.mp3', '.ogg']
            base_path = output_path.rsplit('.', 1)[0]
            
            for ext in possible_extensions:
                test_path = base_path + ext
                if os.path.exists(test_path) and os.path.getsize(test_path) > 0:
                    # إعادة تسمية الملف للمسار المطلوب
                    if test_path != output_path:
                        import shutil
                        shutil.move(test_path, output_path)
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"خطأ في تحميل الصوت: {str(e)}")
            return False

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

def transcribe_with_better_accuracy(model, audio_path, language):
    """
    تفريغ نصي مع دقة محسنة
    """
    transcribe_options = {
        "task": "transcribe",
        "fp16": False,  # تحسين الدقة
        "temperature": 0.0,  # أقل عشوائية
    }
    
    # إضافة اللغة إذا لم تكن auto
    if language != "auto":
        transcribe_options["language"] = language
    
    # خيارات إضافية للنماذج الكبيرة
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
        st.error(f"خطأ في التفريغ النصي: {str(e)}")
        return None

# إعداد واجهة المستخدم
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    video_url = st.text_input("رابط الفيديو (YouTube أو Shorts أو youtu.be)", 
                             placeholder="https://www.youtube.com/watch?v=...")

with col2:
    model_size = st.selectbox(
        "حجم نموذج Whisper",
        ["tiny", "base", "small", "medium", "large"],
        index=2,  # small بشكل افتراضي
        help="النماذج الأكبر أدق لكن أبطأ"
    )

with col3:
    language = st.selectbox(
        "اللغة",
        ["auto", "ar", "en", "fr", "es", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        index=1,  # Arabic بشكل افتراضي
        help="auto للكشف التلقائي"
    )

# إضافة معلومات عن النماذج
with st.expander("ℹ️ دليل اختيار النموذج"):
    st.markdown("""
    | النموذج | الحجم | أفضل استخدام | تحذيرات |
    |---------|-------|-------------|---------|
    | **tiny** | 39 MB | اختبار سريع | دقة منخفضة |
    | **base** | 74 MB | فيديوهات قصيرة | - |
    | **small** | 244 MB | **الأفضل للاستخدام العام** | - |
    | **medium** | 769 MB | دقة عالية | بطيء مع الفيديوهات الطويلة |
    | **large** | 1550 MB | أقصى دقة | ⚠️ قد يعلق مع الفيديوهات >5 دقائق |
    
    **💡 نصيحة:** ابدأ بـ "small" - يعطي توازن ممتاز بين السرعة والدقة
    """)

# تحذير للنماذج الكبيرة
if model_size in ["large", "medium"]:
    st.warning(f"⚠️ تحذير: النموذج {model_size} قد يستغرق وقتاً طويلاً ويستهلك ذاكرة كبيرة. لتجنب تعليق الموقع، استخدمه فقط مع الفيديوهات القصيرة (<5 دقائق).")

if st.button("🚀 بدء التفريغ النصي", type="primary"):
    if not video_url.strip():
        st.warning("⚠️ الرجاء إدخال رابط فيديو صالح.")
    elif not validate_youtube_url(video_url.strip()):
        st.error("❌ الرابط المدخل ليس رابط YouTube صالح.")
    else:
        clean_url = sanitize_youtube_url(video_url.strip())
        st.info(f"🔗 استخدام الرابط: {clean_url}")
        
        # التحقق من مدة الفيديو أولاً
        video_info = get_video_duration(clean_url)
        if video_info:
            duration_minutes = video_info['duration'] // 60
            st.success(f"📹 **{video_info['title']}**")
            st.info(f"⏱️ المدة: {duration_minutes} دقيقة و {video_info['duration'] % 60} ثانية")
            st.info(f"👤 القناة: {video_info['uploader']}")
            
            # تحذير شديد للفيديوهات الطويلة مع النماذج الكبيرة
            if duration_minutes > 5 and model_size in ["large", "medium"]:
                st.error(f"❌ **خطر تعليق الموقع!** الفيديو طويل ({duration_minutes} دقيقة) والنموذج كبير ({model_size})")
                st.error("🛑 **لا ننصح بالمتابعة** - قد يؤدي لتعليق الموقع لفترة طويلة")
                st.info("💡 **البدائل:**")
                st.info("- استخدم النموذج 'small' أو 'base'")
                st.info("- أو جرب فيديو أقصر (<5 دقائق)")
                
                # إيقاف المعالجة
                if not st.checkbox("⚠️ أفهم المخاطر وأريد المتابعة رغم ذلك"):
                    st.stop()
            
            elif duration_minutes > 10:
                st.warning(f"⚠️ الفيديو طويل جداً ({duration_minutes} دقيقة). قد يستغرق وقتاً طويلاً.")
        
        temp_audio = None
        
        try:
            # تنزيل الصوت
            with st.spinner("⏳ جاري تحميل الصوت..."):
                temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_audio.close()
                
                success = download_audio_simple(clean_url, temp_audio.name)
                
                if not success:
                    st.error("❌ فشل في تحميل الصوت من الفيديو.")
                    st.info("🔧 تأكد من:")
                    st.info("1. FFmpeg مثبت على النظام")
                    st.info("2. الرابط صحيح ومتاح")
                    st.info("3. الاتصال بالإنترنت مستقر")
                    st.stop()
                
                if not os.path.exists(temp_audio.name) or os.path.getsize(temp_audio.name) == 0:
                    st.error("❌ لم يتم تحميل الصوت بشكل صحيح.")
                    st.stop()
                
                file_size_mb = os.path.getsize(temp_audio.name) / (1024 * 1024)
                st.success(f"✅ تم تحميل الصوت بنجاح! ({file_size_mb:.1f} MB)")
            
            # تحميل نموذج Whisper
            with st.spinner(f"🤖 جاري تحميل نموذج Whisper ({model_size})..."):
                try:
                    if model_size == "large":
                        st.warning("⏳ النموذج الكبير قد يستغرق عدة دقائق للتحميل...")
                    
                    model = whisper.load_model(model_size)
                    st.success("✅ تم تحميل النموذج بنجاح!")
                except Exception as e:
                    st.error(f"❌ خطأ في تحميل نموذج Whisper: {str(e)}")
                    st.stop()
            
            # إجراء الترانسكريبت
            with st.spinner("📝 جاري التفريغ النصي... (قد يستغرق عدة دقائق)"):
                start_time = time.time()
                
                result = transcribe_with_better_accuracy(model, temp_audio.name, language)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if result is None:
                    st.error("❌ فشل في التفريغ النصي")
                    st.stop()
                
                transcript = result["text"].strip()
                
                if not transcript:
                    st.warning("⚠️ لم يتم العثور على نص في الصوت.")
                    st.info("💡 نصائح لتحسين النتائج:")
                    st.info("- تأكد من وجود كلام واضح في الفيديو")
                    st.info("- جرب نموذج أكبر للدقة الأفضل")
                    st.info("- تحقق من اختيار اللغة الصحيحة")
                else:
                    st.success(f"✅ تم التفريغ النصي بنجاح! (استغرق {processing_time:.1f} ثانية)")
                    
                    # عرض النتائج
                    st.subheader("📄 النص المفرغ")
                    st.text_area("", transcript, height=300, key="final_transcript")
                    
                    # معلومات النتيجة
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        detected_lang = result.get("language", "غير محدد")
                        st.info(f"🌍 اللغة المكتشفة: {detected_lang}")
                    with col_info2:
                        st.info(f"🔤 عدد الأحرف: {len(transcript)}")
                    with col_info3:
                        st.info(f"📝 عدد الكلمات: {len(transcript.split())}")
                    
                    # أزرار التحميل
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.download_button(
                            label="💾 تحميل النص (.txt)",
                            data=transcript,
                            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    with col_btn2:
                        # إنشاء ملف SRT إذا كانت المقاطع متوفرة
                        if "segments" in result and result["segments"]:
                            srt_content = ""
                            for i, segment in enumerate(result["segments"]):
                                start_time = segment["start"]
                                end_time = segment["end"]
                                
                                start_h = int(start_time // 3600)
                                start_m = int((start_time % 3600) // 60)
                                start_s = start_time % 60
                                
                                end_h = int(end_time // 3600)
                                end_m = int((end_time % 3600) // 60)
                                end_s = end_time % 60
                                
                                srt_content += f"{i+1}\n"
                                srt_content += f"{start_h:02d}:{start_m:02d}:{start_s:06.3f} --> {end_h:02d}:{end_m:02d}:{end_s:06.3f}\n"
                                srt_content += f"{segment['text'].strip()}\n\n"
                            
                            st.download_button(
                                label="💾 تحميل SRT",
                                data=srt_content,
                                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                                mime="text/plain"
                            )
                        else:
                            st.info("الطوابع الزمنية غير متوفرة مع هذا النموذج")
                    
                    # عرض المقاطع الزمنية إذا كانت متوفرة
                    if "segments" in result and result["segments"]:
                        with st.expander("⏱️ عرض النص مع الطوابع الزمنية"):
                            for segment in result["segments"]:
                                start_min = int(segment["start"] // 60)
                                start_sec = int(segment["start"] % 60)
                                end_min = int(segment["end"] // 60)
                                end_sec = int(segment["end"] % 60)
                                
                                st.markdown(f"**[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]** {segment['text'].strip()}")
                                
        except Exception as e:
            st.error(f"❌ حدث خطأ عام: {str(e)}")
            
        finally:
            # تنظيف الملفات المؤقتة
            if temp_audio and os.path.exists(temp_audio.name):
                try:
                    os.unlink(temp_audio.name)
                except:
                    pass

# إضافة نصائح مهمة
st.markdown("---")
st.markdown("### 💡 نصائح مهمة لتحسين الأداء:")

col_tip1, col_tip2 = st.columns(2)

with col_tip1:
    st.markdown("""
    **🎯 للحصول على أفضل دقة:**
    - اختر اللغة الصحيحة بدلاً من "auto"
    - استخدم النموذج "medium" للمحتوى المهم
    - تأكد من جودة الصوت في الفيديو
    - تجنب الفيديوهات بضوضاء كثيرة
    """)

with col_tip2:
    st.markdown("""
    **⚡ لتجنب تعليق الموقع:**
    - استخدم "small" للفيديوهات >5 دقائق
    - تجنب "large" مع الفيديوهات الطويلة
    - أغلق التطبيقات الأخرى لتوفير الذاكرة
    - جرب الفيديوهات القصيرة أولاً
    """)

st.markdown("""
<div style='text-align: center; color: #666; margin-top: 2rem; padding: 1rem; background-color: #f0f2f6; border-radius: 10px;'>
    <strong>🚀 النموذج المُوصى به: "small"</strong><br>
    <small>يوفر توازن ممتاز بين السرعة والدقة لمعظم الاستخدامات</small>
</div>
""", unsafe_allow_html=True)
