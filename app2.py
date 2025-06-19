#!/usr/bin/env python3
"""
سكريبت تثبيت تلقائي لأداة تحويل الفيديو إلى نص
يقوم بتثبيت جميع المكتبات المطلوبة تلقائياً
"""

import subprocess
import sys
import os

def run_command(command):
    """تشغيل أمر في النظام"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ نجح: {command}")
            return True
        else:
            print(f"❌ فشل: {command}")
            print(f"الخطأ: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ خطأ في تشغيل: {command}")
        print(f"التفاصيل: {str(e)}")
        return False

def check_python_version():
    """التحقق من إصدار Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ يتطلب Python 3.7 أو أحدث")
        print(f"الإصدار الحالي: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ إصدار Python مناسب: {version.major}.{version.minor}.{version.micro}")
        return True

def install_packages():
    """تثبيت المكتبات المطلوبة"""
    packages = [
        "streamlit>=1.28.0",
        "SpeechRecognition>=3.10.0", 
        "requests>=2.25.0",
        "pydub>=0.25.1",
        "moviepy>=1.0.3"
    ]
    
    print("🔄 جاري تحديث pip...")
    if not run_command(f"{sys.executable} -m pip install --upgrade pip"):
        print("⚠️ فشل في تحديث pip، المتابعة...")
    
    print("\n📦 جاري تثبيت المكتبات...")
    
    for package in packages:
        print(f"\n🔄 تثبيت {package}...")
        command = f"{sys.executable} -m pip install {package}"
        
        if not run_command(command):
            print(f"⚠️ فشل في تثبيت {package}")
            
            # محاولة طرق بديلة
            print("🔄 محاولة طريقة بديلة...")
            alt_command = f"{sys.executable} -m pip install --user {package}"
            
            if not run_command(alt_command):
                print(f"❌ فشل نهائياً في تثبيت {package}")
                return False
    
    return True

def test_imports():
    """اختبار استيراد المكتبات"""
    print("\n🧪 اختبار المكتبات...")
    
    test_modules = [
        ("streamlit", "st"),
        ("speech_recognition", "sr"), 
        ("requests", "requests"),
        ("pydub", "AudioSegment"),
        ("moviepy.editor", "VideoFileClip")
    ]
    
    failed_imports = []
    
    for module_name, import_name in test_modules:
        try:
            if module_name == "pydub":
                from pydub import AudioSegment
            elif module_name == "moviepy.editor":
                from moviepy.editor import VideoFileClip
            else:
                __import__(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {str(e)}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def create_run_script():
    """إنشاء سكريبت تشغيل سريع"""
    script_content = f"""#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    print("🚀 تشغيل أداة تحويل الفيديو إلى نص...")
    
    # التأكد من وجود الملف
    if not os.path.exists("app.py"):
        print("❌ لم يتم العثور على app.py")
        return
    
    # تشغيل streamlit
    try:
        subprocess.run(["{sys.executable}", "-m", "streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ فشل في تشغيل التطبيق")
    except KeyboardInterrupt:
        print("\\n👋 تم إغلاق التطبيق")

if __name__ == "__main__":
    main()
"""
    
    try:
        with open("run.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        print("✅ تم إنشاء ملف التشغيل السريع: run.py")
        return True
    except Exception as e:
        print(f"❌ فشل في إنشاء ملف التشغيل: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("="*50)
    print("🎬 مثبت أداة تحويل الفيديو إلى نص")
    print("="*50)
    
    # التحقق من Python
    if not check_python_version():
        return
    
    # تثبيت المكتبات
    if not install_packages():
        print("\n❌ فشل في تثبيت بعض المكتبات")
        print("💡 حاول تشغيل الأوامر التالية يدوياً:")
        print("pip install --upgrade pip")
        print("pip install streamlit SpeechRecognition pydub moviepy requests")
        return
    
    # اختبار الاستيراد
    if not test_imports():
        print("\n⚠️ بعض المكتبات لم يتم تثبيتها بشكل صحيح")
        print("💡 حاول إعادة تشغيل المثبت أو التثبيت اليدوي")
        return
    
    # إنشاء سكريبت التشغيل
    create_run_script()
    
    print("\n" + "="*50)
    print("🎉 تم التثبيت بنجاح!")
    print("="*50)
    print("\n📋 لتشغيل التطبيق:")
    print("1️⃣ تشغيل مباشر: python run.py")
    print("2️⃣ تشغيل streamlit: streamlit run app.py")
    print("\n💡 تأكد من وجود ملف app.py في نفس المجلد")
    print("🌐 سيتم فتح المتصفح تلقائياً على http://localhost:8501")

if __name__ == "__main__":
    main()
