import os
import subprocess
from SCons.Script import DefaultEnvironment

# 获取环境
env = DefaultEnvironment()

# 定义项目名称和主要文件
PROJECT_NAME = "ResourceExplorer"
MAIN_SCRIPT = "resource_explorer.py"

# 安装pyinstaller
def install_pyinstaller():
    print("正在安装PyInstaller...")
    try:
        subprocess.run(["pip", "install", "--user", "pyinstaller", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"], check=True)
        print("PyInstaller安装成功！")
    except Exception as e:
        print(f"安装PyInstaller失败: {str(e)}")
        raise

# 创建编译目标
def build_exe(target, source, env):
    try:
        # 检查pyinstaller是否可导入
        import PyInstaller
        print(f"使用已安装的PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        # 安装pyinstaller
        install_pyinstaller()
    
    # 构建pyinstaller命令
    cmd = [
        "pyinstaller",
        "--onefile",  # 创建单个可执行文件
        "--console",  # 使用控制台模式，方便调试
        "--name", PROJECT_NAME,
        "--icon", "NONE",  # 无图标
        MAIN_SCRIPT
    ]
    
    print(f"正在编译{PROJECT_NAME}...")
    print(f"执行命令: {' '.join(cmd)}")
    
    # 执行编译命令
    subprocess.run(cmd, check=True)
    
    print(f"\n编译成功！可执行文件位于 dist/{PROJECT_NAME}.exe")

# 添加构建目标
env.Command(
    target=PROJECT_NAME,
    source=[MAIN_SCRIPT],
    action=build_exe
)

# 设置默认目标
env.Default(PROJECT_NAME)