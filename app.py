import os
import tempfile
import streamlit as st
from pytube import YouTube
import whisper

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube (عادي أو Shorts) لترانسكريبت محلي بدون OpenAI.")

# اختيار حجم نموذج Whisper
model_size = st.selectbox("اختر حجم نموذج Whisper", ["tiny","base","small","medium","large"], index=2)
video_url = st.text_input("رابط الفيديو (YouTube أو Shorts)")

if st.button("Transcribe"):
    if not video_url.strip():
        st.warning("الرجاء إدخال رابط فيديو صالح.")
    else:
        # ـــ تحويل روابط Shorts إلى watch?v= ـــ
        if "/shorts/" in video_url:
            vid_id = video_url.split("/shorts/")[-1].split("?")[0]
            video_url = f"https://www.youtube.com/watch?v={vid_id}"

        try:
            # تحميل الصوت
            with st.spinner("⏳ Downloading & extracting audio…"):
                yt = YouTube(video_url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                audio_stream.download(filename=tmp.name)

            # تحميل نموذج Whisper
            with st.spinner(f"🤖 Loading Whisper model ({model_size})…"):
                model = whisper.load_model(model_size)

            # الترانسكريبت محلياً
            with st.spinner("📝 Transcribing…"):
                result = model.transcribe(tmp.name)
                transcript = result["text"]

            st.success("✅ Transcription complete!")
            st.subheader("📄 Transcript")
            st.text_area("", transcript, height=300)

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
