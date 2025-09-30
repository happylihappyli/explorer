import winsound
import time

# 播放提示音
winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
time.sleep(1)
print("主人运行完毕，过来看看！")