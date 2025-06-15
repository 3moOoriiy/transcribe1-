# streamlit_app.py

import os
import tempfile

import streamlit as st
from pytube import YouTube
import openai

# إعداد صفحة Streamlit
st.set_page_config(page_title="Video Transcriber", layout="wide")
st.title("🎥 Video Transcriber with Whisper 🚀")
st.markdown("أدخل رابط فيديو YouTube للحصول على نص الترانسكريبت.")

# جلب مفتاح OpenAI من البيئة
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# مربع إدخال رابط الفيديو
video_url = st.text_input("رابط الفيديو (YouTube)")

if st.button("Transcribe"):
    if not video_url:
        st.warning("الرجاء إدخال رابط فيديو صالح.")
    else:
        try:
            # تحميل الفيديو واستخراج المسار الصوتي
            with st.spinner("⏳ Downloading video & extracting audio..."):
                yt = YouTube(video_url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                tmp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                audio_stream.download(filename=tmp_file.name)

            # إرسال الملف إلى نموذج Whisper
            with st.spinner("🤖 Sending to Whisper..."):
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=open(tmp_file.name, "rb")
                )
                transcript = response["text"]

            # عرض النتائج
            st.success("✅ Transcription complete!")
            st.subheader("📄 Transcript")
            st.text_area("", transcript, height=300)

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
