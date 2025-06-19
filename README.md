# 🎬 Video Transcription Tool

أداة تحويل الفيديو إلى نص باستخدام Streamlit مع حل شامل للمشاكل الشائعة

## الميزات

- ✅ دعم جميع صيغ الفيديو الشائعة (MP4, AVI, MOV, MKV, WebM, FLV)
- ✅ دعم متعدد اللغات (العربية، الإنجليزية، الفرنسية، الألمانية، الإسبانية)
- ✅ واجهة مستخدم محسنة وسريعة
- ✅ إمكانية تحميل النتائج كملف نصي أو SRT للترجمة
- ✅ معالجة محسنة للأخطاء
- ✅ تثبيت تلقائي للمكتبات المطلوبة

## متطلبات التشغيل

- Python 3.7 أو أحدث
- اتصال بالإنترنت (للتعرف على الكلام)
- مساحة تخزين كافية للملفات المؤقتة (1-2 GB)

## التثبيت السريع ⚡

### الطريقة الأولى: التثبيت التلقائي (الأسهل)
```bash
# تحميل المشروع
git clone [repository-url]
cd video-transcript-tool

# تشغيل المثبت التلقائي
python install.py

# تشغيل التطبيق
python run.py
```

### الطريقة الثانية: التثبيت اليدوي
```bash
# إنشاء بيئة افتراضية (اختياري)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# تثبيت المكتبات
pip install --upgrade pip
pip install streamlit SpeechRecognition pydub moviepy requests
```

## التشغيل

```bash
streamlit run app.py
```

## الاستخدام

1. افتح التطبيق في المتصفح
2. اختر لغة الفيديو من الشريط الجانبي
3. حدد مدة كل جزء للمعالجة
4. ارفع ملف الفيديو
5. اضغط "بدء استخراج النص"
6. انتظر حتى انتهاء المعالجة
7. حمّل النتيجة كملف نصي

## ملاحظات مهمة

- الحد الأقصى لحجم الملف: 200MB
- يتطلب اتصال إنترنت للتعرف على الكلام
- دقة النتائج تعتمد على جودة الصوت في الفيديو
- يستخدم Google Speech Recognition API المجاني

## استكشاف الأخطاء

### خطأ في تثبيت PyAudio:
في Windows:
```bash
pip install pipwin
pipwin install pyaudio
```

في Linux/Ubuntu:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

في Mac:
```bash
brew install portaudio
pip install pyaudio
```

### خطأ في معالجة الفيديو:
- تأكد من أن صيغة الفيديو مدعومة
- تأكد من وجود صوت في الفيديو
- جرب تقليل مدة الأجزاء في الإعدادات

## المساهمة

نرحب بالمساهمات! يرجى فتح issue أو pull request.

## الترخيص

MIT License
