import os
import sys
import winsound
import subprocess
import time

"""
资源管理器启动脚本
- 运行主程序
- 播放声音提示
"""

def play_sound():
    """播放声音提示"""
    try:
        # 播放简单的提示音
        winsound.Beep(1000, 300)  # 1000Hz，持续300毫秒
        time.sleep(0.1)
        winsound.Beep(1500, 200)  # 1500Hz，持续200毫秒
    except:
        # 如果无法播放声音，静默忽略
        pass

def main():
    """主函数"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置工作目录
    os.chdir(script_dir)
    
    try:
        # 运行资源管理器程序
        print("正在启动资源管理器...")
        
        # 使用subprocess启动主程序，这样可以在程序运行后播放声音
        process = subprocess.Popen([sys.executable, "resource_explorer.py"])
        
        # 等待一小段时间确保程序已经启动
        time.sleep(1)
        
        # 播放声音提示
        play_sound()
        print("资源管理器已启动，请查看窗口。")
        print("主人运行完毕，过来看看！")
        
        # 保持脚本运行直到主程序结束
        process.wait()
        
    except Exception as e:
        print(f"启动资源管理器时出错: {str(e)}")
        input("按Enter键退出...")

if __name__ == "__main__":
    main()