import streamlit as st
import whisper
import tempfile
import os
import torch

# Configure page
st.set_page_config(
    page_title="🎬 Fast Transcriber", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Cache the model loading
@st.cache_resource
def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=device)
    return model

# Initialize model once
if 'model' not in st.session_state:
    with st.spinner("Loading AI model... (first time only)"):
        st.session_state.model = load_model()

st.title("⚡ Fast Video Transcriber")
st.caption("AI-powered transcription with caching for speed")

# Model selection
model_size = st.selectbox(
    "Model Quality",
    ["tiny", "base", "small", "medium"],
    index=1,
    help="Tiny=fastest, Medium=best quality"
)

# File uploader
video_file = st.file_uploader(
    "Upload your file",
    type=["mp4", "mkv", "wav", "mp3", "m4a", "flac", "webm"],
    help="Supports video and audio files"
)

if video_file is not None:
    # Show file info
    file_size = len(video_file.read()) / (1024*1024)  # MB
    video_file.seek(0)  # Reset file pointer
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File Size", f"{file_size:.1f} MB")
    with col2:
        st.metric("Model", model_size.upper())
    
    if st.button("🚀 Start Transcription", type="primary"):
        try:
            # Create temp file
            file_ext = os.path.splitext(video_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(video_file.read())
                tmp_path = tmp.name
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Loading model...")
            progress_bar.progress(25)
            
            # Load model if different size selected
            if model_size != "base":
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model = whisper.load_model(model_size, device=device)
            else:
                model = st.session_state.model
            
            status_text.text("Processing audio...")
            progress_bar.progress(50)
            
            # Transcribe with options for speed
            result = model.transcribe(
                tmp_path,
                fp16=torch.cuda.is_available(),  # Use fp16 on GPU for speed
                verbose=False
            )
            
            progress_bar.progress(100)
            status_text.text("Complete!")
            
            # Results
            st.success("✅ Transcription completed!")
            
            # Display transcript
            transcript_text = result["text"].strip()
            st.text_area(
                "📝 Transcript",
                transcript_text,
                height=250,
                help="Copy the text or download below"
            )
            
            # Download button
            st.download_button(
                label="📥 Download Transcript",
                data=transcript_text,
                file_name=f"{os.path.splitext(video_file.name)[0]}_transcript.txt",
                mime="text/plain"
            )
            
            # Show segments if available
            if "segments" in result and st.checkbox("Show timestamped segments"):
                st.subheader("🕐 Timestamped Segments")
                for i, segment in enumerate(result["segments"][:10]):  # Show first 10
                    start = int(segment["start"])
                    end = int(segment["end"])
                    text = segment["text"].strip()
                    st.write(f"**{start//60:02d}:{start%60:02d} - {end//60:02d}:{end%60:02d}**: {text}")
            
            # Cleanup
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        finally:
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_text' in locals():
                status_text.empty()

else:
    st.info("👆 Upload a video or audio file to get started")
    
    # Tips section
    with st.expander("💡 Speed Tips"):
        st.write("""
        - **Tiny model**: Fastest, good for quick drafts
        - **Base model**: Good balance of speed and accuracy  
        - **Small/Medium**: Better accuracy, slower processing
        - **GPU**: Automatically used if available for 2-3x speed boost
        - Files are processed locally and not stored
        """)