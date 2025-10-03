import pyttsx3

# 初始化语音引擎
en = pyttsx3.init()

# 设置语音速度和音量
en.setProperty('rate', 150)  # 语速
en.setProperty('volume', 1.0)  # 音量

# 播放语音提示
en.say("修改已完成，请查看文件资源管理器，$RECYCLE.BIN目录已经隐藏，收藏夹在启动时会自动展开。")
en.runAndWait()