# Video Transcriber with Streamlit

هذا المشروع يسمح لك بإدخال رابط فيديو (مثلاً YouTube)، يقوم بتحميله، استخراج الصوت، ثم استخدام نموذج Whisper من OpenAI للحصول على نص ترانسكريبت.

## المتطلبات

- Python 3.8+
- مفتاح API من OpenAI (يعرف بالمتغير البيئي `OPENAI_API_KEY`)

## التثبيت

```bash
git clone https://github.com/<YourUser>/video-transcriber.git
cd video-transcriber
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
