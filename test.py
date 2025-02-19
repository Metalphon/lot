import speech_recognition as sr
from pydub import AudioSegment
import os

def convert_wav_to_text(wav_path):
    # 初始化识别器
    recognizer = sr.Recognizer()
    
    try:
        # 读取音频文件
        with sr.AudioFile(wav_path) as source:
            print("正在读取音频文件...")
            # 获取音频数据
            audio = recognizer.record(source)
            
            print("正在识别...")
            # 尝试不同的语言
            for lang in ['ja-JP', 'zh-CN', 'en-US']:
                try:
                    text = recognizer.recognize_google(audio, language=lang)
                    print(f"使用{lang}识别结果：{text}")
                except:
                    continue
            
    except Exception as e:
        print("处理过程中出错：", str(e))

# 运行识别
wav_file = "tohka-vocal3c36238efb437ce1d8bc263d12e9f4800e91dcc6.wav_0002118720_0002200640.wav"
convert_wav_to_text(wav_file)