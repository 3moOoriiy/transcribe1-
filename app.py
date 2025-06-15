import os
import tempfile

import streamlit as st
from pytube import YouTube
import whisper

st.set_page_config(page_title="Video Transcriber (Local Whisper)", layout="wide")
st.title("🎥 Video Transcriber with Local Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube للحصول على نص الترانسكريبت بدون الحاجة لإنترنت للـ OpenAI.")

# اختيار حجم النموذج
model_size = st.selectbox("اختر حجم نموذج Whisper", ["tiny", "base", "small", "medium", "large"], index=2)
video_url = st.text_input("رابط الفيديو (YouTube)")

if st.button("Transcribe"):
    if not video_url:
        st.warning("الرجاء إدخال رابط فيديو صالح.")
    else:
        try:
            # تحميل الفيديو واستخراج الصوت
            with st.spinner("⏳ Downloading video & extracting audio..."):
                yt = YouTube(video_url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                tmp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                audio_stream.download(filename=tmp_file.name)
            
            # تحميل نموذج Whisper
            with st.spinner(f"🤖 Loading Whisper model ({model_size})..."):
                model = whisper.load_model(model_size)
            
            # تشغيل الترانسكريبت محلياً
            with st.spinner("📝 Transcribing audio..."):
                result = model.transcribe(tmp_file.name)
                transcript = result["text"]

            st.success("✅ Transcription complete!")
            st.subheader("📄 Transcript")
            st.text_area("", transcript, height=300)

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
