import os
import tempfile
import streamlit as st
import whisper
import yt_dlp
from urllib.parse import urlparse, parse_qs
import re

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube (عادي أو Shorts أو youtu.be) لترانسكريبت محلي بدون OpenAI.")

def sanitize_youtube_url(url: str) -> str:
    """
    يستخلص video_id من الرابط ويعيد رابط نظيف من نوع watch?v=VIDEO_ID
    """
    # إزالة المسافات الزائدة
    url = url.strip()
    
    # التعامل مع روابط youtu.be
    if "youtu.be" in url:
        video_id = url.split("/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # التعامل مع روابط YouTube Shorts
    shorts_match = re.search(r'/shorts/([a-zA-Z0-9_-]+)', url)
    if shorts_match:
        video_id = shorts_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # التعامل مع الروابط العادية
    parsed = urlparse(url)
    if parsed.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    
    return url

def download_audio(url: str, output_path: str):
    """
    يحمل أفضل مسار صوتي ويحفظه في output_path
    """
    ydl_opts = {
        "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
        "audioformat": "best",
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return True
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

# إعداد واجهة المستخدم
col1, col2 = st.columns([3, 1])

with col1:
    video_url = st.text_input("رابط الفيديو (YouTube أو Shorts أو youtu.be)", placeholder="https://www.youtube.com/watch?v=...")

with col2:
    model_size = st.selectbox(
        "حجم نموذج Whisper",
        ["tiny", "base", "small", "medium", "large"],
        index=2,
        help="النماذج الأكبر أدق لكن أبطأ"
    )

# إضافة معلومات عن أحجام النماذج
with st.expander("ℹ️ معلومات عن أحجام النماذج"):
    st.markdown("""
    - **tiny**: الأسرع، أقل دقة (~39 MB)
    - **base**: سريع، دقة متوسطة (~74 MB)  
    - **small**: متوازن (~244 MB)
    - **medium**: دقة عالية (~769 MB)
    - **large**: الأدق، الأبطأ (~1550 MB)
    """)

if st.button("🚀 Start Transcription", type="primary"):
    if not video_url.strip():
        st.warning("⚠️ الرجاء إدخال رابط فيديو صالح.")
    elif not validate_youtube_url(video_url.strip()):
        st.error("❌ الرابط المدخل ليس رابط YouTube صالح.")
    else:
        clean_url = sanitize_youtube_url(video_url.strip())
        st.info(f"🔗 استخدام الرابط: {clean_url}")
        
        # إنشاء ملف مؤقت
        temp_audio = None
        
        try:
            # تنزيل الصوت
            with st.spinner("⏳ جاري تحميل الصوت..."):
                temp_audio = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
                temp_audio.close()  # إغلاق الملف للسماح لـ yt-dlp بالكتابة فيه
                
                success = download_audio(clean_url, temp_audio.name)
                
                if not success:
                    st.error("❌ فشل في تحميل الصوت من الفيديو.")
                    st.stop()
                
                # التحقق من وجود الملف
                if not os.path.exists(temp_audio.name) or os.path.getsize(temp_audio.name) == 0:
                    st.error("❌ لم يتم تحميل الصوت بشكل صحيح.")
                    st.stop()
                
                st.success("✅ تم تحميل الصوت بنجاح!")
            
            # تحميل نموذج Whisper
            with st.spinner(f"🤖 جاري تحميل نموذج Whisper ({model_size})..."):
                try:
                    model = whisper.load_model(model_size)
                    st.success("✅ تم تحميل النموذج بنجاح!")
                except Exception as e:
                    st.error(f"❌ خطأ في تحميل نموذج Whisper: {str(e)}")
                    st.stop()
            
            # إجراء الترانسكريبت
            with st.spinner("📝 جاري التفريغ النصي..."):
                try:
                    result = model.transcribe(
                        temp_audio.name,
                        language="ar",  # يمكنك تغيير اللغة حسب الحاجة
                        task="transcribe"
                    )
                    transcript = result["text"].strip()
                    
                    if not transcript:
                        st.warning("⚠️ لم يتم العثور على نص في الصوت.")
                    else:
                        st.success("✅ تم التفريغ النصي بنجاح!")
                        
                        # عرض النتائج
                        st.subheader("📄 النص المفرغ")
                        st.text_area("", transcript, height=300, key="transcript_output")
                        
                        # زر تحميل النص
                        st.download_button(
                            label="💾 تحميل النص",
                            data=transcript,
                            file_name="transcript.txt",
                            mime="text/plain"
                        )
                        
                        # معلومات إضافية
                        with st.expander("ℹ️ معلومات إضافية"):
                            if "language" in result:
                                st.write(f"**اللغة المكتشفة:** {result['language']}")
                            st.write(f"**حجم النموذج:** {model_size}")
                            st.write(f"**طول النص:** {len(transcript)} حرف")
                            
                except Exception as e:
                    st.error(f"❌ خطأ في التفريغ النصي: {str(e)}")
                    
        except Exception as e:
            st.error(f"❌ حدث خطأ عام: {str(e)}")
            
        finally:
            # تنظيف الملفات المؤقتة
            if temp_audio and os.path.exists(temp_audio.name):
                try:
                    os.unlink(temp_audio.name)
                except:
                    pass  # تجاهل أخطاء الحذف

# إضافة تذييل مع معلومات
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>🔧 Built with Streamlit, Whisper & yt-dlp | 
    💡 Tip: استخدم النماذج الأصغر للاختبار السريع</small>
</div>
""", unsafe_allow_html=True)
