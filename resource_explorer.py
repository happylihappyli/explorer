import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import webbrowser
import subprocess
from pathlib import Path
import mimetypes
import time
import json
import os

# 定义一些简单的图标字符
FOLDER_ICON = "📁"
FILE_ICON = "📄"
DRIVE_ICON = "💾"
# 特定文件类型的图标
DOC_ICON = "📝"
IMAGE_ICON = "🖼️"
AUDIO_ICON = "🔊"
VIDEO_ICON = "🎬"
EXE_ICON = "⚙️"
# 收藏夹图标
FAVORITES_ICON = "⭐"

class ResourceExplorer:
    def __init__(self, root):
        """初始化资源管理器"""
        self.root = root
        self.root.title("资源管理器")
        self.root.geometry("1000x600")
        
        # 设置中文字体支持
        self.style = ttk.Style()
        try:
            self.style.configure("Treeview", font=("Microsoft YaHei UI", 10))
            self.style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        except:
            pass  # 如果字体不可用，使用默认字体
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建可调整大小的分隔窗格
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧导航面板
        self.nav_frame = ttk.LabelFrame(self.paned_window, text="导航")
        self.paned_window.add(self.nav_frame, weight=5)  # 初始宽度比例设为2，比之前更大
        
        # 右侧内容区域
        self.content_frame = ttk.LabelFrame(self.paned_window, text="内容")
        self.paned_window.add(self.content_frame, weight=3)  # 初始宽度比例设为3
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 当前路径
        self.current_path = None
        
        # 收藏夹相关
        self.favorites = []
        self.favorites_file = os.path.join(os.path.expanduser("~"), ".resource_explorer_favorites.json")
        self.favorites_id = None
        
        # 加载收藏夹
        self.load_favorites()
        
        # 创建导航树
        self.create_navigation_tree()
        
        # 创建内容视图
        self.create_content_view()
        
        # 初始化驱动器列表和收藏夹
        self.init_drives()
    
    def create_navigation_tree(self):
        """创建导航树视图"""
        # 创建设备树
        self.nav_tree = ttk.Treeview(self.nav_frame, show="tree", selectmode="browse")
        self.nav_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.nav_tree, orient="vertical", command=self.nav_tree.yview)
        self.nav_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        self.nav_tree.bind("<Double-1>", self.on_nav_item_double_click)
        self.nav_tree.bind("<Button-1>", self.on_nav_item_click)
    
    def create_content_view(self):
        """创建内容视图"""
        # 创建工具栏
        self.toolbar_frame = ttk.Frame(self.content_frame)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 路径输入框
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(self.toolbar_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind("<Return>", self.navigate_to_path)
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(self.toolbar_frame, text="刷新", command=self.refresh_content)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 视图切换按钮
        self.view_var = tk.StringVar(value="list")
        self.list_view_btn = ttk.Radiobutton(self.toolbar_frame, text="列表", variable=self.view_var, value="list", command=self.switch_view)
        self.list_view_btn.pack(side=tk.LEFT, padx=5)
        self.details_view_btn = ttk.Radiobutton(self.toolbar_frame, text="详情", variable=self.view_var, value="details", command=self.switch_view)
        self.details_view_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建内容表格，添加图标列
        columns = ("icon", "name", "type", "size", "modified")
        self.content_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")
        
        # 设置列宽和标题
        self.content_tree.column("icon", width=30, anchor=tk.CENTER)
        self.content_tree.column("name", width=170, anchor=tk.W)
        self.content_tree.column("type", width=100, anchor=tk.W)
        self.content_tree.column("size", width=80, anchor=tk.E)
        self.content_tree.column("modified", width=150, anchor=tk.W)
        
        # 设置表头和排序功能
        self.content_tree.heading("icon", text="")
        self.content_tree.heading("name", text="名称", command=lambda: self.sort_by_column("name"))
        self.content_tree.heading("type", text="类型", command=lambda: self.sort_by_column("type"))
        self.content_tree.heading("size", text="大小", command=lambda: self.sort_by_column("size"))
        self.content_tree.heading("modified", text="修改日期", command=lambda: self.sort_by_column("modified"))
        
        # 排序状态变量
        self.sort_column = "name"  # 默认按名称排序
        self.sort_order = "ascending"  # 默认升序
        self.items_data = []  # 存储项目数据，用于排序
        
        # 添加滚动条
        yscrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.content_tree.yview)
        self.content_tree.configure(yscrollcommand=yscrollbar.set)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        xscrollbar = ttk.Scrollbar(self.content_frame, orient="horizontal", command=self.content_tree.xview)
        self.content_tree.configure(xscrollcommand=xscrollbar.set)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定事件
        self.content_tree.bind("<Double-1>", self.on_content_item_double_click)
        self.content_tree.bind("<Button-3>", self.show_context_menu)
        
        self.content_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建右键菜单
        self.create_context_menu()
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="打开", command=self.open_selected_item)
        self.context_menu.add_command(label="属性", command=self.show_item_properties)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="添加到收藏夹", command=self.add_selected_to_favorites)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制", command=self.copy_item)
        self.context_menu.add_command(label="剪切", command=self.cut_item)
        self.context_menu.add_command(label="粘贴", command=self.paste_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_item)
        
        # 剪贴板操作变量
        self.copied_item = None
        self.is_cut = False
    
    def get_file_icon(self, file_path):
        """根据文件类型返回对应的图标"""
        # 首先获取文件扩展名
        _, ext = os.path.splitext(file_path.lower())
        
        # 根据扩展名返回对应的图标
        if ext in ['.txt', '.doc', '.docx', '.pdf', '.md', '.rtf']:
            return DOC_ICON
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']:
            return IMAGE_ICON
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            return AUDIO_ICON
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']:
            return VIDEO_ICON
        elif ext in ['.exe', '.bat', '.cmd', '.msi']:
            return EXE_ICON
        else:
            return FILE_ICON
    
    def load_favorites(self):
        """加载收藏夹列表"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
        except Exception as e:
            print(f"加载收藏夹失败: {str(e)}")
            self.favorites = []
    
    def save_favorites(self):
        """保存收藏夹列表"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存收藏夹失败: {str(e)}")
    
    def add_to_favorites(self, path):
        """添加目录到收藏夹"""
        if path not in self.favorites:
            self.favorites.append(path)
            self.save_favorites()
            self.update_favorites_view()
            return True
        return False
    
    def remove_from_favorites(self, path):
        """从收藏夹移除目录"""
        if path in self.favorites:
            self.favorites.remove(path)
            self.save_favorites()
            self.update_favorites_view()
            return True
        return False
    
    def update_favorites_view(self):
        """更新收藏夹视图"""
        # 清除现有的收藏夹项目
        if self.favorites_id and self.nav_tree.exists(self.favorites_id):
            children = self.nav_tree.get_children(self.favorites_id)
            for child in children:
                self.nav_tree.delete(child)
            
            # 添加收藏夹项目
            for path in self.favorites:
                folder_name = os.path.basename(path)
                self.nav_tree.insert(self.favorites_id, tk.END, text=FOLDER_ICON + " " + folder_name, values=(path,))
    
    def init_drives(self):
        """初始化系统驱动器和收藏夹"""
        # 先添加收藏夹
        self.favorites_id = self.nav_tree.insert("", tk.END, text=FAVORITES_ICON + " 收藏夹")
        self.update_favorites_view()
        
        # 添加分隔线
        self.nav_tree.insert("", tk.END, text="------------------------------------------", tags=("separator",))
        self.nav_tree.tag_configure("separator", foreground="gray", font=("Arial", 8))
        
        # 获取Windows系统驱动器
        if sys.platform == 'win32':
            drives = []
            for drive_letter in range(ord('A'), ord('Z') + 1):
                drive = f"{chr(drive_letter)}:/"
                if os.path.exists(drive):
                    try:
                        # 尝试获取驱动器类型
                        subprocess_result = subprocess.run(
                            ["fsutil", "fsinfo", "drivetype", drive],
                            capture_output=True, text=True, shell=True
                        )
                        drive_type = subprocess_result.stdout.strip().split(":")[-1].strip()
                        drives.append((drive, drive_type))
                    except:
                        drives.append((drive, "本地磁盘"))
        else:
            # 非Windows系统
            drives = [("/", "根目录")]
        
        # 添加驱动器到导航树
        for drive, drive_type in drives:
            drive_id = self.nav_tree.insert("", tk.END, text=DRIVE_ICON + " " + f"{drive} ({drive_type})")
            # 预加载一级目录
            try:
                for item in os.listdir(drive):
                    item_path = os.path.join(drive, item)
                    if os.path.isdir(item_path):
                        # 添加文件夹图标
                        self.nav_tree.insert(drive_id, tk.END, text=FOLDER_ICON + " " + item, values=(item_path,))
            except PermissionError:
                pass
    
    def on_nav_item_double_click(self, event):
        """导航树双击事件处理"""
        try:
            item = self.nav_tree.selection()[0]
            item_text = self.nav_tree.item(item, "text")
            item_values = self.nav_tree.item(item, "values")
            
            # 处理分隔线
            if "------------------------------------------" in item_text:
                return
            
            # 处理收藏夹节点
            if item == self.favorites_id:
                # 收藏夹节点不需要加载子目录
                return
            
            # 处理收藏的目录项
            if item_values and len(item_values) > 0:
                path = item_values[0]
            # 处理驱动器
            elif len(item_text) >= 3 and item_text[1] == ":" and item_text[2] == "/":
                path = item_text.split()[0]  # 获取驱动器路径
            else:
                # 尝试获取父节点路径
                parent = self.nav_tree.parent(item)
                if not parent:
                    # 如果没有父节点，可能是驱动器或特殊节点
                    return
                
                parent_text = self.nav_tree.item(parent, "text")
                parent_values = self.nav_tree.item(parent, "values")
                
                if parent_values and len(parent_values) > 0:
                    parent_path = parent_values[0]
                elif len(parent_text) >= 3 and parent_text[1] == ":" and parent_text[2] == "/":
                    parent_path = parent_text.split()[0]
                else:
                    # 如果无法获取父路径，则无法继续
                    return
                
                # 从item_text中提取文件夹名称（去除图标）
                folder_name = item_text.split(" ")[-1]
                path = os.path.join(parent_path, folder_name)
            
            # 加载子目录
            self.load_directory(path, item)
            
            # 显示目录内容
            self.show_directory_content(path)
        except Exception as e:
            # 添加错误处理
            print(f"导航树双击事件处理错误: {str(e)}")
    
    def on_nav_item_click(self, event):
        """导航树单击事件处理"""
        # 这里可以添加单击选中的逻辑
        pass
    
    def load_directory(self, path, tree_item):
        """加载目录内容到导航树"""
        # 清除现有子项
        children = self.nav_tree.get_children(tree_item)
        for child in children:
            self.nav_tree.delete(child)
        
        # 添加新子项
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        # 检查是否有权限访问
                        os.scandir(item_path)
                        # 添加文件夹图标
                        self.nav_tree.insert(tree_item, tk.END, text=FOLDER_ICON + " " + item, values=(item_path,))
                    except PermissionError:
                        pass  # 无权限访问的目录跳过
        except PermissionError:
            messagebox.showerror("错误", f"无法访问 {path}: 权限被拒绝")
        except Exception as e:
            messagebox.showerror("错误", f"加载目录时出错: {str(e)}")
    
    def show_directory_content(self, path):
        """显示目录内容"""
        start_time = time.time()  # 开始计时
        
        # 保存当前路径
        self.current_path = path
        
        # 更新路径输入框
        self.path_var.set(path)
        
        # 清除现有内容
        for item in self.content_tree.get_children():
            self.content_tree.delete(item)
        
        # 获取目录内容并显示
        try:
            items = []
            # 先添加目录
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        stats = os.stat(item_path)
                        modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_mtime))
                        # 存储原始大小用于排序
                        items.append((item, "文件夹", "", modified_time, item_path, True, stats.st_mtime))
                    except:
                        pass  # 跳过无法访问的项目
            
            # 再添加文件
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    try:
                        stats = os.stat(item_path)
                        file_size = self.format_size(stats.st_size)
                        modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_mtime))
                        
                        # 获取文件类型
                        mime_type, _ = mimetypes.guess_type(item_path)
                        if mime_type:
                            file_type = mime_type.split('/')[1].upper() + "文件"
                        else:
                            _, ext = os.path.splitext(item_path)
                            if ext:
                                file_type = ext[1:].upper() + "文件"
                            else:
                                file_type = "文件"
                        
                        # 存储原始大小和时间戳用于排序
                        items.append((item, file_type, file_size, modified_time, item_path, False, stats.st_size, stats.st_mtime))
                    except:
                        pass  # 跳过无法访问的项目
            
            # 保存数据用于排序
            self.items_data = items
            
            # 首次显示时按默认方式排序
            self.sort_by_column(self.sort_column, force=True)
            

            
            # 更新状态栏
            elapsed_time = time.time() - start_time
            self.status_var.set(f"显示 {len(items)} 个项目 ({elapsed_time:.2f}s)")
            
        except PermissionError:
            messagebox.showerror("错误", f"无法访问 {path}: 权限被拒绝")
            self.status_var.set("无法访问目录")
        except Exception as e:
            messagebox.showerror("错误", f"显示目录内容时出错: {str(e)}")
            self.status_var.set("显示目录内容时出错")
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def on_content_item_double_click(self, event):
        """内容项双击事件处理"""
        self.open_selected_item()
    
    def open_selected_item(self):
        """打开选中的项目"""
        try:
            selected_item = self.content_tree.selection()[0]
            # 注意：现在第一列是图标，文件名在索引1的位置
            item_name = self.content_tree.item(selected_item, "values")[1]
            item_type = self.content_tree.item(selected_item, "values")[2]
            
            if self.current_path:
                item_path = os.path.join(self.current_path, item_name)
                
                if os.path.isdir(item_path):
                    # 打开目录
                    self.show_directory_content(item_path)
                    # 更新导航树选择
                    self.update_nav_tree_selection(item_path)
                else:
                    # 打开文件
                    try:
                        if sys.platform == 'win32':
                            os.startfile(item_path)
                        else:
                            subprocess.run(['xdg-open', item_path])
                    except Exception as e:
                        messagebox.showerror("错误", f"无法打开文件: {str(e)}")
        except IndexError:
            pass  # 没有选中任何项
        except Exception as e:
            messagebox.showerror("错误", f"打开项目时出错: {str(e)}")
    
    def update_nav_tree_selection(self, path):
        """更新导航树选中状态"""
        # 简单实现：尝试展开当前路径的所有父目录
        # 注意：这是一个简化版本，完整实现可能需要更复杂的逻辑
        pass  # 在实际应用中可以完善此功能
        
    def sort_by_column(self, col, force=False):
        """按指定列对内容进行排序"""
        # 切换排序顺序（除非强制使用当前顺序）
        if not force and col == self.sort_column:
            self.sort_order = not self.sort_order
        else:
            self.sort_column = col
            self.sort_order = False  # 默认为升序
        
        # 定义排序键函数
        def get_sort_key(item):
            if col == 0:  # 名称列
                return item[0].lower()
            elif col == 1:  # 类型列
                return item[1].lower()
            elif col == 2:  # 大小列
                if item[5]:  # 目录
                    return 0  # 目录大小为0
                else:
                    return item[6]  # 文件大小
            elif col == 3:  # 修改日期列
                if item[5]:  # 目录
                    return item[6]  # 目录时间戳
                else:
                    return item[7]  # 文件时间戳
            return ''
        
        # 对数据进行排序
        sorted_items = sorted(self.items_data, key=get_sort_key, reverse=self.sort_order)
        
        # 先清除当前显示的内容
        for item in self.content_tree.get_children():
            self.content_tree.delete(item)
        
        # 添加排序后的内容
        for item in sorted_items:
            if item[5]:  # 如果是目录
                self.content_tree.insert("", tk.END, values=(FOLDER_ICON, item[0], item[1], item[2], item[3]))
            else:  # 如果是文件
                icon = self.get_file_icon(item[4])
                self.content_tree.insert("", tk.END, values=(icon, item[0], item[1], item[2], item[3]))
        
        # 更新表头指示排序方向
        for c in range(4):
            if c == col:
                symbol = "↑" if not self.sort_order else "↓"
                header = f"{['名称', '类型', '大小', '修改日期'][c]}{symbol}"
            else:
                header = ['名称', '类型', '大小', '修改日期'][c]
            self.content_tree.heading(c+1, text=header, command=lambda _col=c: self.sort_by_column(_col))
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 选中右键点击的项目
            item = self.content_tree.identify_row(event.y)
            if item:
                self.content_tree.selection_set(item)
                self.content_tree.focus(item)
                
                # 获取选中项目的信息
                selected_item = self.content_tree.selection()[0]
                item_name = self.content_tree.item(selected_item, "values")[1]
                item_path = os.path.join(self.current_path, item_name) if self.current_path else ""
                
                # 重新创建菜单，确保菜单选项正确
                self.context_menu.delete(0, tk.END)  # 清空现有菜单
                self.context_menu.add_command(label="打开", command=self.open_selected_item)
                self.context_menu.add_command(label="属性", command=self.show_item_properties)
                self.context_menu.add_separator()
                
                # 根据项目类型添加收藏夹相关选项
                if item_path and os.path.isdir(item_path):
                    if item_path in self.favorites:
                        self.context_menu.add_command(label="从收藏夹移除", command=self.remove_selected_from_favorites)
                    else:
                        self.context_menu.add_command(label="添加到收藏夹", command=self.add_selected_to_favorites)
                
                self.context_menu.add_separator()
                self.context_menu.add_command(label="复制", command=self.copy_item)
                self.context_menu.add_command(label="剪切", command=self.cut_item)
                self.context_menu.add_command(label="粘贴", command=self.paste_item)
                self.context_menu.add_separator()
                self.context_menu.add_command(label="删除", command=self.delete_item)
                
                # 显示菜单
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            # 添加错误信息，便于调试
            print(f"显示右键菜单时出错: {str(e)}")
            pass
    
    def add_selected_to_favorites(self):
        """将选中的目录添加到收藏夹"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[1]
            
            if self.current_path:
                item_path = os.path.join(self.current_path, item_name)
                if os.path.isdir(item_path):
                    if self.add_to_favorites(item_path):
                        messagebox.showinfo("成功", f"已将 '{item_name}' 添加到收藏夹")
                    else:
                        messagebox.showinfo("提示", f"'{item_name}' 已在收藏夹中")
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"添加到收藏夹时出错: {str(e)}")
    
    def remove_selected_from_favorites(self):
        """从收藏夹移除选中的目录"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[1]
            
            if self.current_path:
                item_path = os.path.join(self.current_path, item_name)
                if self.remove_from_favorites(item_path):
                    messagebox.showinfo("成功", f"已从收藏夹移除 '{item_name}'")
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"从收藏夹移除时出错: {str(e)}")
    
    def show_item_properties(self):
        """显示项目属性"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[0]
            
            if self.current_path:
                item_path = os.path.join(self.current_path, item_name)
                
                # 创建属性窗口
                prop_window = tk.Toplevel(self.root)
                prop_window.title(f"{item_name} 属性")
                prop_window.geometry("400x300")
                prop_window.resizable(False, False)
                
                # 创建属性列表
                props_frame = ttk.Frame(prop_window)
                props_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # 添加属性项
                ttk.Label(props_frame, text=f"名称: {item_name}").pack(anchor=tk.W, pady=2)
                ttk.Label(props_frame, text=f"位置: {self.current_path}").pack(anchor=tk.W, pady=2)
                ttk.Label(props_frame, text=f"路径: {item_path}").pack(anchor=tk.W, pady=2)
                
                try:
                    stats = os.stat(item_path)
                    if os.path.isdir(item_path):
                        ttk.Label(props_frame, text=f"类型: 文件夹").pack(anchor=tk.W, pady=2)
                    else:
                        size = stats.st_size
                        formatted_size = self.format_size(size)
                        ttk.Label(props_frame, text=f"类型: 文件").pack(anchor=tk.W, pady=2)
                        ttk.Label(props_frame, text=f"大小: {formatted_size} ({size} 字节)").pack(anchor=tk.W, pady=2)
                    
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_ctime))
                    modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_mtime))
                    accessed_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_atime))
                    
                    ttk.Label(props_frame, text=f"创建时间: {created_time}").pack(anchor=tk.W, pady=2)
                    ttk.Label(props_frame, text=f"修改时间: {modified_time}").pack(anchor=tk.W, pady=2)
                    ttk.Label(props_frame, text=f"访问时间: {accessed_time}").pack(anchor=tk.W, pady=2)
                except Exception as e:
                    ttk.Label(props_frame, text=f"无法获取完整属性: {str(e)}").pack(anchor=tk.W, pady=2)
                
                # 确定按钮
                ttk.Button(prop_window, text="确定", command=prop_window.destroy).pack(pady=10)
        except IndexError:
            pass  # 没有选中任何项
        except Exception as e:
            messagebox.showerror("错误", f"显示属性时出错: {str(e)}")
    
    def copy_item(self):
        """复制选中的项目"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[0]
            
            if self.current_path:
                self.copied_item = os.path.join(self.current_path, item_name)
                self.is_cut = False
                self.status_var.set(f"已复制: {item_name}")
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"复制项目时出错: {str(e)}")
    
    def cut_item(self):
        """剪切选中的项目"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[0]
            
            if self.current_path:
                self.copied_item = os.path.join(self.current_path, item_name)
                self.is_cut = True
                self.status_var.set(f"已剪切: {item_name}")
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"剪切项目时出错: {str(e)}")
    
    def paste_item(self):
        """粘贴项目"""
        try:
            if self.copied_item and self.current_path:
                # 获取目标路径
                dest_name = os.path.basename(self.copied_item)
                dest_path = os.path.join(self.current_path, dest_name)
                
                # 如果目标已存在，添加数字后缀
                counter = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(dest_name)
                    dest_path = os.path.join(self.current_path, f"{name}({counter}){ext}")
                    counter += 1
                
                # 复制或移动文件
                if os.path.isdir(self.copied_item):
                    # 复制目录
                    import shutil
                    shutil.copytree(self.copied_item, dest_path)
                    
                    # 如果是剪切操作，删除原文件
                    if self.is_cut:
                        shutil.rmtree(self.copied_item)
                else:
                    # 复制文件
                    with open(self.copied_item, 'rb') as src, open(dest_path, 'wb') as dst:
                        # 使用缓冲区提高大文件复制速度
                        buffer_size = 1024 * 1024  # 1MB
                        while True:
                            buffer = src.read(buffer_size)
                            if not buffer:
                                break
                            dst.write(buffer)
                    
                    # 如果是剪切操作，删除原文件
                    if self.is_cut:
                        os.remove(self.copied_item)
                
                # 刷新当前目录
                self.refresh_content()
                
                # 清除剪贴板（如果是剪切操作）
                if self.is_cut:
                    self.copied_item = None
                    self.is_cut = False
                
                self.status_var.set(f"已粘贴到: {self.current_path}")
        except Exception as e:
            messagebox.showerror("错误", f"粘贴项目时出错: {str(e)}")
    
    def delete_item(self):
        """删除选中的项目"""
        try:
            selected_item = self.content_tree.selection()[0]
            item_name = self.content_tree.item(selected_item, "values")[0]
            
            if self.current_path:
                item_path = os.path.join(self.current_path, item_name)
                
                # 确认删除
                if messagebox.askyesno("确认删除", f"确定要删除 '{item_name}' 吗？\n此操作无法撤销。"):
                    if os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    
                    # 刷新当前目录
                    self.refresh_content()
                    self.status_var.set(f"已删除: {item_name}")
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("错误", f"删除项目时出错: {str(e)}")
    
    def navigate_to_path(self, event=None):
        """导航到指定路径"""
        path = self.path_var.get()
        if os.path.exists(path) and os.path.isdir(path):
            self.show_directory_content(path)
        else:
            messagebox.showerror("错误", f"无效的路径: {path}")
    
    def refresh_content(self):
        """刷新当前目录内容"""
        if self.current_path:
            self.show_directory_content(self.current_path)
    
    def switch_view(self):
        """切换视图模式"""
        # 这里可以添加不同视图模式的切换逻辑
        # 当前版本主要支持列表视图，详情视图基本相同
        pass

def main():
    """主函数"""
    # 设置中文字体支持
    root = tk.Tk()
    
    # 创建应用实例
    app = ResourceExplorer(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()