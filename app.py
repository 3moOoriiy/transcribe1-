import os
import tempfile
import streamlit as st
from pytube import YouTube
import whisper
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube (عادي أو Shorts أو youtu.be) لترانسكريبت محلي بدون OpenAI.")

def sanitize_youtube_url(url: str) -> str:
    """
    يستخلص video_id من الرابط ويعيد رابط نظيف من نوع watch?v=VIDEO_ID
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    # حالة watch?v=...
    if "v" in qs and qs["v"]:
        return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    # رابط Shorts
    if "/shorts/" in parsed.path:
        vid = parsed.path.split("/shorts/")[-1]
        return f"https://www.youtube.com/watch?v={vid}"
    # رابط youtu.be
    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/")
        return f"https://www.youtube.com/watch?v={vid}"
    # غير معروف، نعيد كما هو
    return url

# اختيار حجم نموذج Whisper
model_size = st.selectbox(
    "اختر حجم نموذج Whisper", 
    ["tiny", "base", "small", "medium", "large"], 
    index=2
)

video_url = st.text_input("رابط الفيديو (YouTube أو Shorts أو youtu.be)")

if st.button("Transcribe"):
    if not video_url.strip():
        st.warning("الرجاء إدخال رابط فيديو صالح.")
    else:
        # تنقية الرابط
        clean_url = sanitize_youtube_url(video_url.strip())
        # لعرض الرابط المنقّى للتأكد
        st.write("🔗 Using URL:", clean_url)

        try:
            # تحميل الصوت
            with st.spinner("⏳ Downloading & extracting audio…"):
                yt = YouTube(clean_url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                audio_stream.download(filename=tmp.name)

            # تحميل نموذج Whisper
            with st.spinner(f"🤖 Loading Whisper model ({model_size})…"):
                model = whisper.load_model(model_size)

            # إجراء الترانسكريبت
            with st.spinner("📝 Transcribing…"):
                result = model.transcribe(tmp.name)
                transcript = result["text"]

            st.success("✅ Transcription complete!")
            st.subheader("📄 Transcript")
            st.text_area("", transcript, height=300)

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
