# 🎬 Video Transcription Tool

أداة تحويل الفيديو إلى نص باستخدام Streamlit

## الميزات

- ✅ دعم معظم صيغ الفيديو (MP4, AVI, MOV, MKV, WMV)
- ✅ دعم متعدد اللغات (العربية، الإنجليزية، الفرنسية، الألمانية، الإسبانية)
- ✅ واجهة مستخدم سهلة وبسيطة
- ✅ إمكانية تحميل النتائج كملف نصي
- ✅ معالجة محلية للملفات
- ✅ شريط تقدم لمتابعة المعالجة

## متطلبات التشغيل

- Python 3.7+
- اتصال بالإنترنت (للتعرف على الكلام)
- مساحة تخزين كافية للملفات المؤقتة

## التثبيت

1. استنسخ المشروع:
```bash
git clone [repository-url]
cd video-transcript-tool
```

2. إنشاء بيئة افتراضية:
```bash
python -m venv venv
source venv/bin/activate  # في Linux/Mac
# أو
venv\Scripts\activate  # في Windows
```

3. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
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
