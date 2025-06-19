import streamlit as st
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import tempfile
import os
from pydub import AudioSegment
from pydub.utils import make_chunks
import io
import time

# إعداد الصفحة
st.set_page_config(
    page_title="Video Transcription Tool",
    page_icon="🎬",
    layout="wide"
)

# العنوان والوصف
st.title("🎬 أداة تحويل الفيديو إلى نص")
st.markdown("قم برفع فيديو وسيتم استخراج النص منه تلقائياً")

# دالة لاستخراج الصوت من الفيديو
def extract_audio_from_video(video_path):
    """استخراج الصوت من الفيديو وحفظه كملف WAV"""
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        
        # حفظ الصوت في ملف مؤقت
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
            audio_path = temp_audio.name
        
        video.close()
        audio.close()
        
        return audio_path
    except Exception as e:
        st.error(f"خطأ في استخراج الصوت: {str(e)}")
        return None

# دالة لتقسيم الصوت إلى أجزاء صغيرة
def split_audio(audio_path, chunk_length_ms=30000):
    """تقسيم الصوت إلى أجزاء صغيرة للمعالجة"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        chunks = make_chunks(audio, chunk_length_ms)
        return chunks
    except Exception as e:
        st.error(f"خطأ في تقسيم الصوت: {str(e)}")
        return None

# دالة للتعرف على الكلام
def transcribe_audio_chunk(audio_chunk, language='ar-EG'):
    """تحويل جزء من الصوت إلى نص"""
    recognizer = sr.Recognizer()
    
    try:
        # تحويل AudioSegment إلى bytes
        wav_io = io.BytesIO()
        audio_chunk.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # التعرف على الكلام
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            
        # استخدام Google Speech Recognition
        text = recognizer.recognize_google(audio_data, language=language)
        return text
        
    except sr.UnknownValueError:
        return "[لم يتم التعرف على الكلام]"
    except sr.RequestError as e:
        return f"[خطأ في الخدمة: {e}]"
    except Exception as e:
        return f"[خطأ: {e}]"

# دالة لمعالجة الفيديو الكامل
def process_video(video_file, language='ar-EG', chunk_duration=30):
    """معالجة الفيديو الكامل وإرجاع النص"""
    
    # حفظ الفيديو في ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name
    
    try:
        # استخراج الصوت
        st.info("جاري استخراج الصوت من الفيديو...")
        audio_path = extract_audio_from_video(video_path)
        
        if not audio_path:
            return None
        
        # تقسيم الصوت
        st.info("جاري تقسيم الصوت...")
        chunks = split_audio(audio_path, chunk_duration * 1000)
        
        if not chunks:
            return None
        
        # معالجة كل جزء
        transcript = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, chunk in enumerate(chunks):
            status_text.text(f"معالجة الجزء {i+1} من {len(chunks)}")
            
            # تحويل الجزء إلى نص
            text = transcribe_audio_chunk(chunk, language)
            if text and text != "[لم يتم التعرف على الكلام]":
                timestamp = f"[{i*chunk_duration//60:02d}:{(i*chunk_duration)%60:02d}]"
                transcript.append(f"{timestamp} {text}")
            
            # تحديث شريط التقدم
            progress_bar.progress((i + 1) / len(chunks))
            
            # انتظار قصير لتجنب تجاوز حدود API
            time.sleep(0.5)
        
        # تنظيف الملفات المؤقتة
        os.unlink(video_path)
        os.unlink(audio_path)
        
        status_text.text("تم الانتهاء!")
        progress_bar.progress(1.0)
        
        return "\n".join(transcript)
        
    except Exception as e:
        st.error(f"خطأ في معالجة الفيديو: {str(e)}")
        # تنظيف الملفات في حالة الخطأ
        try:
            os.unlink(video_path)
            if 'audio_path' in locals():
                os.unlink(audio_path)
        except:
            pass
        return None

# واجهة المستخدم
def main():
    # الشريط الجانبي للإعدادات
    st.sidebar.header("⚙️ الإعدادات")
    
    # اختيار اللغة
    language_options = {
        "العربية": "ar-EG",
        "الإنجليزية": "en-US",
        "الفرنسية": "fr-FR",
        "الألمانية": "de-DE",
        "الإسبانية": "es-ES"
    }
    
    selected_language = st.sidebar.selectbox(
        "اختر لغة الفيديو:",
        list(language_options.keys()),
        index=0
    )
    
    # مدة كل جزء
    chunk_duration = st.sidebar.slider(
        "مدة كل جزء (ثانية):",
        min_value=10,
        max_value=60,
        value=30,
        step=5
    )
    
    # رفع الفيديو
    st.header("📁 رفع الفيديو")
    uploaded_file = st.file_uploader(
        "اختر ملف فيديو",
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
        help="الحد الأقصى للحجم: 200MB"
    )
    
    if uploaded_file is not None:
        # عرض معلومات الملف
        file_details = {
            "اسم الملف": uploaded_file.name,
            "حجم الملف": f"{uploaded_file.size / (1024*1024):.2f} MB",
            "نوع الملف": uploaded_file.type
        }
        
        st.subheader("📋 معلومات الملف")
        for key, value in file_details.items():
            st.write(f"**{key}:** {value}")
        
        # زر المعالجة
        if st.button("🚀 بدء استخراج النص", type="primary"):
            if uploaded_file.size > 200 * 1024 * 1024:  # 200MB
                st.error("حجم الملف كبير جداً! الحد الأقصى 200MB")
            else:
                with st.spinner("جاري معالجة الفيديو..."):
                    transcript = process_video(
                        uploaded_file, 
                        language_options[selected_language],
                        chunk_duration
                    )
                
                if transcript:
                    st.success("تم استخراج النص بنجاح!")
                    
                    st.subheader("📝 النص المستخرج")
                    st.text_area("النتيجة:", transcript, height=400)
                    
                    # زر التحميل
                    st.download_button(
                        label="📥 تحميل النص",
                        data=transcript,
                        file_name=f"transcript_{uploaded_file.name}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error("فشل في استخراج النص من الفيديو")
    
    # معلومات إضافية
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ معلومات مهمة")
    st.sidebar.markdown("""
    - يدعم التطبيق معظم صيغ الفيديو الشائعة
    - يتم معالجة الفيديو محلياً
    - يستخدم Google Speech Recognition
    - قد تحتاج لاتصال إنترنت
    - دقة النتائج تعتمد على جودة الصوت
    """)

if __name__ == "__main__":
    main()
