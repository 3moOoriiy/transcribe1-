import streamlit as st
import os
import tempfile
import io
from typing import Optional, List
import time
import threading
from pathlib import Path
import streamlit as st

try:
    import moviepy.editor as mp
    st.success("✅ تم استيراد moviepy بنجاح!")
except ImportError:
    st.error("❌ لم يتم تثبيت مكتبة moviepy. تأكد من أن 'moviepy' موجودة في requirements.txt")
# Try to import required libraries with error handling
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
except ImportError as e:
    st.error(f"مكتبة مطلوبة غير مثبتة: {str(e)}")
    st.info("يرجى تثبيت المكتبات المطلوبة باستخدام الأمر التالي:")
    st.code("pip install SpeechRecognition pydub")
    st.stop()

try:
    import moviepy
    from moviepy.editor import VideoFileClip
except ImportError:
    st.error("مكتبة moviepy غير مثبتة")
    st.info("يرجى تثبيت moviepy باستخدام الأمر التالي:")
    st.code("pip install moviepy")
    st.stop()

# Configuration
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']
SUPPORTED_LANGUAGES = {
    'ar-SA': 'العربية',
    'en-US': 'English',
    'fr-FR': 'Français',
    'de-DE': 'Deutsch',
    'es-ES': 'Español',
    'it-IT': 'Italiano',
    'ja-JP': '日本語',
    'ko-KR': '한국어',
    'zh-CN': '中文'
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

def setup_page():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="🎬 أداة تحويل الفيديو إلى نص",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for RTL support and better styling
    st.markdown("""
    <style>
    .main > div {
        direction: rtl;
        text-align: right;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    """Extract audio from video file"""
    try:
        with VideoFileClip(video_path) as video:
            if video.audio is None:
                st.error("❌ الفيديو لا يحتوي على مسار صوتي")
                return False
            
            audio = video.audio
            # Convert to wav format for better compatibility
            audio.write_audiofile(output_path, verbose=False, logger=None)
            
        return True
    except Exception as e:
        st.error(f"❌ خطأ في استخراج الصوت: {str(e)}")
        return False

def split_audio_into_chunks(audio_path: str, chunk_length_ms: int = 30000) -> List[AudioSegment]:
    """Split audio into smaller chunks for processing"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        
        # Split on silence if possible, otherwise split by time
        try:
            chunks = split_on_silence(
                audio,
                min_silence_len=1000,  # 1 second
                silence_thresh=audio.dBFS - 14,
                keep_silence=500
            )
            
            # If no silence found, split by time
            if len(chunks) <= 1:
                chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
                
        except:
            # Fallback to time-based splitting
            chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        
        return chunks
    except Exception as e:
        st.error(f"❌ خطأ في تقسيم الصوت: {str(e)}")
        return []

def transcribe_audio_chunk(audio_chunk: AudioSegment, language: str) -> str:
    """Transcribe a single audio chunk"""
    recognizer = sr.Recognizer()
    
    try:
        # Convert AudioSegment to wav bytes
        wav_bytes = io.BytesIO()
        audio_chunk.export(wav_bytes, format="wav")
        wav_bytes.seek(0)
        
        # Create AudioFile from bytes
        with sr.AudioFile(wav_bytes) as source:
            audio_data = recognizer.record(source)
        
        # Recognize speech
        text = recognizer.recognize_google(audio_data, language=language)
        return text
        
    except sr.UnknownValueError:
        return ""  # No speech detected
    except sr.RequestError as e:
        st.warning(f"⚠️ خطأ في خدمة التعرف على الكلام: {str(e)}")
        return ""
    except Exception as e:
        st.warning(f"⚠️ خطأ في معالجة الجزء: {str(e)}")
        return ""

def transcribe_video(video_file, language: str, chunk_duration: int, progress_callback=None) -> Optional[str]:
    """Main transcription function"""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        temp_audio_path = temp_audio.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_video:
        temp_video.write(video_file.read())
        temp_video_path = temp_video.name
    
    try:
        # Extract audio from video
        if progress_callback:
            progress_callback(10, "🎵 استخراج الصوت من الفيديو...")
        
        if not extract_audio_from_video(temp_video_path, temp_audio_path):
            return None
        
        # Split audio into chunks
        if progress_callback:
            progress_callback(20, "✂️ تقسيم الصوت إلى أجزاء...")
        
        chunk_length_ms = chunk_duration * 1000
        audio_chunks = split_audio_into_chunks(temp_audio_path, chunk_length_ms)
        
        if not audio_chunks:
            st.error("❌ فشل في تقسيم الصوت")
            return None
        
        # Transcribe each chunk
        transcript_parts = []
        total_chunks = len(audio_chunks)
        
        for i, chunk in enumerate(audio_chunks):
            if progress_callback:
                progress = 30 + (60 * i // total_chunks)
                progress_callback(progress, f"🔤 معالجة الجزء {i+1} من {total_chunks}...")
            
            text = transcribe_audio_chunk(chunk, language)
            if text.strip():
                transcript_parts.append(text.strip())
            
            # Small delay to avoid hitting API limits
            time.sleep(0.5)
        
        if progress_callback:
            progress_callback(95, "📝 تجميع النص النهائي...")
        
        # Combine all text parts
        full_transcript = " ".join(transcript_parts)
        
        if progress_callback:
            progress_callback(100, "✅ تم الانتهاء!")
        
        return full_transcript if full_transcript.strip() else None
        
    except Exception as e:
        st.error(f"❌ خطأ عام في المعالجة: {str(e)}")
        return None
    
    finally:
        # Clean up temporary files
        try:
            os.unlink(temp_audio_path)
            os.unlink(temp_video_path)
        except:
            pass

def create_srt_content(transcript: str, chunk_duration: int) -> str:
    """Create SRT subtitle content from transcript"""
    lines = transcript.split('. ')
    srt_content = ""
    
    for i, line in enumerate(lines):
        if line.strip():
            start_time = i * chunk_duration
            end_time = (i + 1) * chunk_duration
            
            start_hours = start_time // 3600
            start_minutes = (start_time % 3600) // 60
            start_seconds = start_time % 60
            
            end_hours = end_time // 3600
            end_minutes = (end_time % 3600) // 60
            end_seconds = end_time % 60
            
            srt_content += f"{i+1}\n"
            srt_content += f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d},000 --> "
            srt_content += f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d},000\n"
            srt_content += f"{line.strip()}.\n\n"
    
    return srt_content

def main():
    setup_page()
    
    # Header
    st.markdown("# 🎬 أداة تحويل الفيديو إلى نص")
    st.markdown("### استخراج النص من الفيديو باستخدام تقنية التعرف على الكلام")
    
    # Sidebar settings
    with st.sidebar:
        st.markdown("## ⚙️ الإعدادات")
        
        # Language selection
        selected_language = st.selectbox(
            "🌐 اختر لغة الفيديو:",
            options=list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda x: SUPPORTED_LANGUAGES[x],
            index=0
        )
        
        # Chunk duration
        chunk_duration = st.slider(
            "⏱️ مدة كل جزء (ثانية):",
            min_value=10,
            max_value=60,
            value=30,
            step=5,
            help="مدة أطول = دقة أفضل لكن معالجة أبطأ"
        )
        
        st.markdown("---")
        st.markdown("### 📋 الصيغ المدعومة:")
        st.markdown("• MP4, AVI, MOV")
        st.markdown("• MKV, WebM, FLV")
        st.markdown("• M4V")
        
        st.markdown("### 📏 الحد الأقصى:")
        st.markdown("• حجم الملف: 200MB")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "📁 اختر ملف الفيديو:",
            type=[fmt[1:] for fmt in SUPPORTED_VIDEO_FORMATS],
            help="اسحب وأسقط الملف هنا أو اضغط لاختيار الملف"
        )
        
        if uploaded_file is not None:
            # File validation
            file_size = len(uploaded_file.getvalue())
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_size > MAX_FILE_SIZE:
                st.error(f"❌ حجم الملف كبير جداً: {file_size/1024/1024:.1f}MB (الحد الأقصى: 200MB)")
                return
            
            if file_extension not in SUPPORTED_VIDEO_FORMATS:
                st.error(f"❌ صيغة الملف غير مدعومة: {file_extension}")
                return
            
            # File info
            st.success(f"✅ تم تحميل الملف: {uploaded_file.name}")
            st.info(f"📊 حجم الملف: {file_size/1024/1024:.1f} MB")
            
            # Processing button
            if st.button("🚀 بدء استخراج النص", type="primary"):
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(progress, message):
                    progress_bar.progress(progress)
                    status_text.text(message)
                
                # Start transcription
                with st.spinner("⏳ جاري المعالجة..."):
                    transcript = transcribe_video(
                        uploaded_file, 
                        selected_language, 
                        chunk_duration,
                        update_progress
                    )
                
                if transcript:
                    st.markdown("---")
                    st.markdown("## 📄 النتيجة:")
                    
                    # Display transcript
                    st.text_area(
                        "النص المستخرج:",
                        value=transcript,
                        height=300,
                        disabled=True
                    )
                    
                    # Download options
                    col_download1, col_download2 = st.columns(2)
                    
                    with col_download1:
                        # Text file download
                        st.download_button(
                            label="💾 تحميل كملف نصي",
                            data=transcript,
                            file_name=f"{Path(uploaded_file.name).stem}_transcript.txt",
                            mime="text/plain"
                        )
                    
                    with col_download2:
                        # SRT file download
                        srt_content = create_srt_content(transcript, chunk_duration)
                        st.download_button(
                            label="🎬 تحميل كملف ترجمة SRT",
                            data=srt_content,
                            file_name=f"{Path(uploaded_file.name).stem}_subtitles.srt",
                            mime="text/plain"
                        )
                    
                    # Statistics
                    word_count = len(transcript.split())
                    char_count = len(transcript)
                    
                    st.markdown("### 📊 إحصائيات:")
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("عدد الكلمات", word_count)
                    with col_stat2:
                        st.metric("عدد الأحرف", char_count)
                    with col_stat3:
                        st.metric("مدة المعالجة", f"{chunk_duration}s/جزء")
                
                else:
                    st.error("❌ لم يتم العثور على نص في الفيديو أو حدث خطأ في المعالجة")
    
    with col2:
        st.markdown("## 💡 نصائح للحصول على أفضل النتائج:")
        st.markdown("""
        **🎤 جودة الصوت:**
        • تأكد من وضوح الصوت
        • تجنب الضوضاء الخلفية
        • استخدم ميكروفون جيد
        
        **🗣️ طريقة الكلام:**
        • تحدث بوضوح ووتيرة مناسبة
        • تجنب التحدث السريع
        • اترك فترات صمت قصيرة
        
        **⚙️ الإعدادات:**
        • اختر اللغة الصحيحة
        • قلل مدة الأجزاء للفيديوهات السريعة
        • زد المدة للمحادثات الهادئة
        """)
        
        st.markdown("---")
        st.markdown("## 🆘 حل المشاكل الشائعة:")
        
        with st.expander("خطأ في تثبيت المكتبات"):
            st.code("""
# تثبيت المكتبات المطلوبة
pip install --upgrade pip
pip install streamlit
pip install SpeechRecognition
pip install pydub
pip install moviepy

# في حالة مشاكل PyAudio
pip install pipwin
pipwin install pyaudio
            """)
        
        with st.expander("لا يتم استخراج نص"):
            st.markdown("""
            • تأكد من وجود صوت في الفيديو
            • جرب لغة مختلفة
            • قلل مدة الأجزاء
            • تحقق من جودة الصوت
            """)

if __name__ == "__main__":
    main()
