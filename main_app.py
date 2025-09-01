#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试系统 - Python App模式
整合前后端功能，使用tkinter作为GUI界面
"""

import os
import sys
import json
import logging
import threading
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import subprocess

# 项目根目录加入路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from communicators.operation_multi_machine import MultiMachineOperation
import app_config as config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main_app")

# 自定义日志处理器，用于在GUI中显示日志
class GUILogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.tag_configure("INFO", foreground="black")
        self.text_widget.tag_configure("WARNING", foreground="orange")
        self.text_widget.tag_configure("ERROR", foreground="red")
        self.text_widget.tag_configure("DEBUG", foreground="blue")
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.text_widget.insert(tk.END, msg + "\n", record.levelname)
            self.text_widget.see(tk.END)
            self.text_widget.update_idletasks()
        except Exception:
            pass

# 全局异常处理装饰器
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"操作失败: {str(e)}"
            logger.error(f"{func.__name__} 执行失败: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            messagebox.showerror("错误", error_msg)
        return None
    return wrapper

class ScriptManager:
    """脚本管理器"""
    
    def __init__(self, storage_file: str, counter_file: str):
        self.storage_file = storage_file
        self.counter_file = counter_file
        self.scripts_storage: Dict[str, dict] = {}
        self.script_counter = 0
        self._ensure_storage_dir()
        self._load_data()
    
    def _ensure_storage_dir(self):
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
    
    def _load_data(self):
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.scripts_storage = json.load(f)
            
            if os.path.exists(self.counter_file):
                with open(self.counter_file, 'r', encoding='utf-8') as f:
                    counter_data = json.load(f)
                    self.script_counter = counter_data.get('counter', 0)
        except Exception as e:
            logger.error(f"加载脚本数据失败: {e}")
            self.scripts_storage = {}
            self.script_counter = 0
    
    def _save_data(self):
        try:
            self._ensure_storage_dir()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.scripts_storage, f, ensure_ascii=False, indent=2)
            
            with open(self.counter_file, 'w', encoding='utf-8') as f:
                json.dump({'counter': self.script_counter}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存脚本数据失败: {e}")
            raise
    
    def get_all_scripts(self) -> List[dict]:
        return list(self.scripts_storage.values())
    
    def get_script(self, script_id: str) -> Optional[dict]:
        return self.scripts_storage.get(script_id)
    
    def create_script(self, name: str, description: str, content: str) -> dict:
        self.script_counter += 1
        script_id = f"script_{self.script_counter}"
        
        now = datetime.now().isoformat()
        script_info = {
            "id": script_id,
            "name": name,
            "description": description,
            "content": content,
            "createdAt": now,
            "updatedAt": now,
            "status": "idle",
            "runCount": 0
        }
        
        self.scripts_storage[script_id] = script_info
        self._save_data()
        return script_info
    
    def delete_script(self, script_id: str) -> bool:
        if script_id in self.scripts_storage:
            del self.scripts_storage[script_id]
            self._save_data()
            return True
        return False

class AutoTestApp:
    """自动化测试应用主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("自动化测试系统 v2.0")
        self.root.geometry("1400x900")
        # 设置窗口最大化
        self.root.state('zoomed')
        
        # 设置应用图标和样式
        self.setup_styles()
        
        # 初始化组件
        self.server: Optional[MultiMachineOperation] = None
        self.is_running = False
        self.current_machine_id: Optional[str] = None
        self.current_app_name: Optional[str] = None
        
        # 脚本管理器
        self.script_manager = ScriptManager(
            config.SCRIPT_STORAGE_FILE,
            config.SCRIPT_COUNTER_FILE
        )
        
        # 日志显示组件
        self.log_text = None
        
        self.setup_ui()
        self.setup_logging()
        
    def setup_styles(self):
        """设置应用样式"""
        style = ttk.Style()
        
        # 配置主题样式
        style.theme_use('clam')
        
        # 配置标签页样式
        style.configure('TNotebook.Tab', padding=[10, 5], font=('微软雅黑', 9))
        style.configure('TNotebook', background='#f0f0f0')
        
        # 配置按钮样式
        style.configure('TButton', padding=[8, 4], font=('微软雅黑', 9))
        style.configure('Accent.TButton', background='#0078d4', foreground='white')
        
        # 配置标签样式
        style.configure('TLabel', font=('微软雅黑', 9))
        style.configure('Title.TLabel', font=('微软雅黑', 12, 'bold'))
        style.configure('Status.TLabel', font=('微软雅黑', 10))
        
        # 配置框架样式
        style.configure('Card.TFrame', relief='solid', borderwidth=1)
        
    def setup_logging(self):
        """设置日志系统"""
        if self.log_text:
            # 添加GUI日志处理器
            gui_handler = GUILogHandler(self.log_text)
            gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(gui_handler)
            
            # 设置日志级别
            logger.setLevel(logging.INFO)
            
            logger.info("日志系统初始化完成")
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 顶部标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(title_frame, text="自动化测试系统", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        # 顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="服务器控制", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 服务器状态和控制按钮
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="服务器状态: 未启动", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=(0, 30))
        
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(btn_frame, text="启动服务器", command=self.start_server, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(btn_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 创建notebook用于标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 仪表板页面
        self.setup_dashboard_tab()
        
        # 操作控制页面
        self.setup_operation_tab()
        
        # 脚本管理页面
        self.setup_script_tab()
        
        # 日志显示页面
        self.setup_log_tab()
        
        # 底部状态栏
        self.setup_status_bar()
        
    def setup_status_bar(self):
        """设置底部状态栏"""
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 分隔线
        separator = ttk.Separator(status_bar, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 5))
        
        # 状态信息
        self.status_info = ttk.Label(status_bar, text="就绪", style="Status.TLabel")
        self.status_info.pack(side=tk.LEFT)
        
        # 时间显示
        self.time_label = ttk.Label(status_bar, text="", style="Status.TLabel")
        self.time_label.pack(side=tk.RIGHT)
        
        # 更新时间
        self.update_time()
        
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)  # 每秒更新一次
        
    def setup_log_tab(self):
        """设置日志显示标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="系统日志")
        
        # 日志控制区域
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        # 日志级别选择
        ttk.Label(log_control_frame, text="日志级别:").pack(side=tk.LEFT, padx=(0, 10))
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                      state="readonly", width=10)
        log_level_combo.pack(side=tk.LEFT, padx=(0, 20))
        log_level_combo.bind("<<ComboboxSelected>>", self.change_log_level)
        
        # 日志操作按钮
        clear_log_btn = ttk.Button(log_control_frame, text="清空日志", command=self.clear_logs)
        clear_log_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_log_btn = ttk.Button(log_control_frame, text="保存日志", command=self.save_logs)
        save_log_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 日志显示区域
        log_display_frame = ttk.LabelFrame(log_frame, text="实时日志", padding=15)
        log_display_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_display_frame, height=20, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志文本框标签
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("DEBUG", foreground="blue")
        
    def change_log_level(self, event=None):
        """改变日志级别"""
        level = self.log_level_var.get()
        logger.setLevel(getattr(logging, level))
        logger.info(f"日志级别已更改为: {level}")
        
    def clear_logs(self):
        """清空日志"""
        if self.log_text:
            self.log_text.delete(1.0, tk.END)
            logger.info("日志已清空")
        
    def save_logs(self):
        """保存日志到文件"""
        if not self.log_text:
            return
            
        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
                logger.info(f"日志已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {str(e)}")
                logger.error(f"保存日志失败: {e}")
        
    def setup_dashboard_tab(self):
        """设置仪表板标签页"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="仪表板")
        
        # 连接状态
        status_frame = ttk.LabelFrame(dashboard_frame, text="连接状态", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 15), padx=15)
        
        # 状态指示器框架
        status_indicator_frame = ttk.Frame(status_frame)
        status_indicator_frame.pack(fill=tk.X)
        
        # 连接状态标签
        self.connection_status = ttk.Label(status_indicator_frame, text="未连接")
        self.connection_status.pack(side=tk.LEFT)
        
        # 当前目标显示
        target_frame = ttk.Frame(status_frame)
        target_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(target_frame, text="当前目标:").pack(side=tk.LEFT)
        self.current_target_label = ttk.Label(target_frame, text="未设置", foreground="gray")
        self.current_target_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 快速设置目标按钮
        quick_target_btn = ttk.Button(target_frame, text="快速设置", command=self.quick_set_target)
        quick_target_btn.pack(side=tk.RIGHT)
        
        # 机器列表
        machine_frame = ttk.LabelFrame(dashboard_frame, text="已连接机器", padding=15)
        machine_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 机器列表树形视图
        columns = ("机器ID", "IP地址", "端口", "状态", "应用", "连接时间")
        self.machine_tree = ttk.Treeview(machine_frame, columns=columns, show="headings")
        
        # 设置列标题和宽度
        column_configs = [
            ("机器ID", 120),
            ("IP地址", 120),
            ("端口", 80),
            ("状态", 100),
            ("应用", 150),
            ("连接时间", 150)
        ]
        
        for col, width in column_configs:
            self.machine_tree.heading(col, text=col)
            self.machine_tree.column(col, width=width)
        
        self.machine_tree.pack(fill=tk.BOTH, expand=True)
        
        # 绑定右键菜单
        self.machine_tree.bind("<Button-3>", self.show_machine_context_menu)
        
        # 创建右键菜单
        self.machine_context_menu = tk.Menu(self.root, tearoff=0)
        self.machine_context_menu.add_command(label="设置为目标", command=self.set_selected_as_target)
        self.machine_context_menu.add_command(label="查看详情", command=self.show_machine_details)
        self.machine_context_menu.add_separator()
        self.machine_context_menu.add_command(label="断开连接", command=self.disconnect_machine)
        
        # 机器操作按钮框架
        machine_btn_frame = ttk.Frame(machine_frame)
        machine_btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 新建连接按钮
        new_conn_btn = ttk.Button(machine_btn_frame, text="新建连接", command=self.show_new_connection_dialog, style="Accent.TButton")
        new_conn_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 断开连接按钮
        disconnect_btn = ttk.Button(machine_btn_frame, text="断开连接", command=self.disconnect_machine)
        disconnect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = ttk.Button(machine_btn_frame, text="刷新", command=self.refresh_machines)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
    def setup_operation_tab(self):
        """设置操作控制标签页"""
        operation_frame = ttk.Frame(self.notebook)
        self.notebook.add(operation_frame, text="操作控制")
        
        # 目标设置
        target_frame = ttk.LabelFrame(operation_frame, text="目标设置", padding=15)
        target_frame.pack(fill=tk.X, pady=(0, 15), padx=15)
        
        ttk.Label(target_frame, text="机器ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.machine_id_entry = ttk.Entry(target_frame, width=20)
        self.machine_id_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(target_frame, text="应用名称:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.app_name_entry = ttk.Entry(target_frame, width=20)
        self.app_name_entry.grid(row=0, column=3, padx=(0, 20))
        
        set_target_btn = ttk.Button(target_frame, text="设置目标", command=self.set_target)
        set_target_btn.grid(row=0, column=4)
        
        # 操作按钮
        operation_frame_inner = ttk.LabelFrame(operation_frame, text="操作", padding=15)
        operation_frame_inner.pack(fill=tk.X, pady=(0, 15), padx=15)
        
        btn_frame = ttk.Frame(operation_frame_inner)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="截图", command=self.take_screenshot, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="点击元素", command=self.click_element, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="点击图片", command=self.click_image, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # 操作结果显示
        result_frame = ttk.LabelFrame(operation_frame, text="操作结果", padding=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 进度条
        progress_frame = ttk.Frame(result_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(progress_frame, text="操作进度:").pack(side=tk.LEFT, padx=(0, 10))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, font=('Consolas', 9))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_script_tab(self):
        """设置脚本管理标签页"""
        script_frame = ttk.Frame(self.notebook)
        self.notebook.add(script_frame, text="脚本管理")
        
        # 脚本列表
        list_frame = ttk.LabelFrame(script_frame, text="脚本列表", padding=15)
        list_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=15, pady=15)
        
        # 脚本列表树形视图
        columns = ("ID", "名称", "状态", "运行次数")
        self.script_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.script_tree.heading(col, text=col)
            self.script_tree.column(col, width=100)
        
        self.script_tree.pack(fill=tk.BOTH, expand=True)
        
        # 脚本操作按钮
        script_btn_frame = ttk.Frame(list_frame)
        script_btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(script_btn_frame, text="新建", command=self.new_script, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(script_btn_frame, text="编辑", command=self.edit_script).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(script_btn_frame, text="删除", command=self.delete_script).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(script_btn_frame, text="运行", command=self.run_script, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # 脚本编辑区域
        edit_frame = ttk.LabelFrame(script_frame, text="脚本编辑", padding=15)
        edit_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=(15, 15), pady=15)
        
        ttk.Label(edit_frame, text="脚本名称:").pack(anchor=tk.W)
        self.script_name_entry = ttk.Entry(edit_frame)
        self.script_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(edit_frame, text="脚本描述:").pack(anchor=tk.W)
        self.script_desc_entry = ttk.Entry(edit_frame)
        self.script_desc_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(edit_frame, text="脚本内容:").pack(anchor=tk.W)
        self.script_content_text = scrolledtext.ScrolledText(edit_frame, height=15)
        self.script_content_text.pack(fill=tk.BOTH, expand=True)
        
        # 保存按钮
        save_btn = ttk.Button(edit_frame, text="保存", command=self.save_script, style="Accent.TButton")
        save_btn.pack(pady=(15, 0))
        
        # 加载脚本列表
        self.refresh_script_list()
        
    @handle_exceptions
    def start_server(self):
        """启动服务器"""
        self.server = MultiMachineOperation(
            bind_host=config.DEFAULT_HOST,
            server_port=config.DEFAULT_PORT
        )
        self.is_running = True
        
        self.status_label.config(text=f"服务器状态: 运行中 ({config.DEFAULT_HOST}:{config.DEFAULT_PORT})")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.connection_status.config(text="已连接")
        
        messagebox.showinfo("成功", f"服务器已启动 {config.DEFAULT_HOST}:{config.DEFAULT_PORT}")
        logger.info(f"服务器已启动 {config.DEFAULT_HOST}:{config.DEFAULT_PORT}")
        self.update_status("服务器运行中")
    
    @handle_exceptions
    def stop_server(self):
        """停止服务器"""
        if self.server:
            self.server.close()
        self.server = None
        self.is_running = False
        
        self.status_label.config(text="服务器状态: 已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.connection_status.config(text="未连接")
        
        messagebox.showinfo("成功", "服务器已停止")
        logger.info("服务器已停止")
        self.update_status("服务器已停止")
    
    @handle_exceptions
    def refresh_machines(self):
        """刷新机器列表"""
        if not self.is_running or not self.server:
            messagebox.showwarning("警告", "服务器未启动")
            return
        
        # 清空现有列表
        for item in self.machine_tree.get_children():
            self.machine_tree.delete(item)
        
        # 获取机器列表
        machines = self.server.get_available_machines()
        for machine_id in machines:
            # 这里可以根据实际的机器信息来填充数据
            # 暂时使用模拟数据
            current_time = datetime.now().strftime("%H:%M:%S")
            self.machine_tree.insert("", "end", values=(
                machine_id, 
                "127.0.0.1",  # IP地址
                "8888",        # 端口
                "已连接",      # 状态
                "测试应用",     # 应用名称
                current_time    # 连接时间
            ))
        
        logger.info(f"机器列表已刷新，共 {len(machines)} 台机器")
        self.update_status(f"机器列表已刷新，共 {len(machines)} 台机器")
        
    def update_status(self, message):
        """更新状态栏信息"""
        if hasattr(self, 'status_info'):
            self.status_info.config(text=message)
            # 3秒后恢复默认状态
            self.root.after(3000, lambda: self.status_info.config(text="就绪"))
        
    def show_new_connection_dialog(self):
        """显示新建连接对话框"""
        if not self.is_running or not self.server:
            messagebox.showwarning("警告", "服务器未启动")
            return
        
        # 创建新建连接对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("新建机器连接")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # 居中显示对话框
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # 创建表单框架
        form_frame = ttk.Frame(dialog, padding=25)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(form_frame, text="新建机器连接", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 机器ID输入
        ttk.Label(form_frame, text="机器ID:").grid(row=1, column=0, sticky=tk.W, pady=(0, 15))
        machine_id_entry = ttk.Entry(form_frame, width=35, font=('微软雅黑', 9))
        machine_id_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 15), padx=(15, 0))
        
        # IP地址输入
        ttk.Label(form_frame, text="IP地址:").grid(row=2, column=0, sticky=tk.W, pady=(0, 15))
        ip_entry = ttk.Entry(form_frame, width=35, font=('微软雅黑', 9))
        ip_entry.grid(row=2, column=1, sticky=tk.W, pady=(0, 15), padx=(15, 0))
        ip_entry.insert(0, "127.0.0.1")
        
        # 端口输入
        ttk.Label(form_frame, text="端口:").grid(row=3, column=0, sticky=tk.W, pady=(0, 15))
        port_entry = ttk.Entry(form_frame, width=35, font=('微软雅黑', 9))
        port_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 15), padx=(15, 0))
        port_entry.insert(0, "8888")
        
        # 应用名称输入
        ttk.Label(form_frame, text="应用名称:").grid(row=4, column=0, sticky=tk.W, pady=(0, 15))
        app_name_entry = ttk.Entry(form_frame, width=35, font=('微软雅黑', 9))
        app_name_entry.grid(row=4, column=1, sticky=tk.W, pady=(0, 15), padx=(15, 0))
        app_name_entry.insert(0, "default_app")
        
        # 描述输入
        ttk.Label(form_frame, text="描述:").grid(row=5, column=0, sticky=tk.W, pady=(0, 15))
        desc_entry = ttk.Entry(form_frame, width=35, font=('微软雅黑', 9))
        desc_entry.grid(row=5, column=1, sticky=tk.W, pady=(0, 15), padx=(15, 0))
        desc_entry.insert(0, "自动化测试应用")
        
        # 按钮框架
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(25, 0))
        
        # 连接按钮
        connect_btn = ttk.Button(btn_frame, text="连接", command=lambda: self.create_connection(
            dialog, machine_id_entry.get(), ip_entry.get(), port_entry.get(), 
            app_name_entry.get(), desc_entry.get()
        ), style="Accent.TButton", width=12)
        connect_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # 取消按钮
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12)
        cancel_btn.pack(side=tk.LEFT)
        
        # 设置焦点
        machine_id_entry.focus()
        
        # 绑定回车键
        dialog.bind('<Return>', lambda e: connect_btn.invoke())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def create_connection(self, dialog, machine_id, ip, port, app_name, desc):
        """创建新连接"""
        # 验证输入
        if not machine_id.strip() or not ip.strip() or not port.strip() or not app_name.strip():
            messagebox.showwarning("警告", "请填写所有必填字段")
            return
        
        try:
            port_num = int(port)
            if port_num <= 0 or port_num > 65535:
                raise ValueError("端口号无效")
        except ValueError:
            messagebox.showerror("错误", "端口号必须是1-65535之间的数字")
            return
        
        try:
            # 调用服务器的连接方法
            if hasattr(self.server, 'connect_to_machine') and callable(getattr(self.server, 'connect_to_machine')):
                result = self.server.connect_to_machine(machine_id, ip, port_num)
                if result.get("success"):
                    messagebox.showinfo("成功", f"成功连接到机器 {machine_id}")
                    dialog.destroy()
                    # 刷新机器列表
                    self.refresh_machines()
                else:
                    messagebox.showerror("错误", f"连接失败: {result.get('error', '未知错误')}")
            else:
                # 如果没有connect_to_machine方法，尝试其他方式
                messagebox.showinfo("信息", f"尝试连接到 {ip}:{port}")
                dialog.destroy()
                self.refresh_machines()
                
        except Exception as e:
            messagebox.showerror("错误", f"创建连接失败: {str(e)}")
            logger.error(f"创建连接失败: {e}")
    
    def disconnect_machine(self):
        """断开选中的机器连接"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要断开的机器")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("确认", f"确定要断开机器 {machine_id} 的连接吗？"):
            try:
                if hasattr(self.server, 'disconnect_machine') and callable(getattr(self.server, 'disconnect_machine')):
                    result = self.server.disconnect_machine(machine_id)
                    if result.get("success"):
                        messagebox.showinfo("成功", f"机器 {machine_id} 已断开")
                        self.refresh_machines()
                    else:
                        messagebox.showerror("错误", f"断开失败: {result.get('error')}")
                else:
                    # 如果没有disconnect_machine方法，尝试其他方式
                    messagebox.showinfo("信息", f"尝试断开机器 {machine_id}")
                    self.refresh_machines()
                    
            except Exception as e:
                messagebox.showerror("错误", f"断开连接失败: {str(e)}")
                logger.error(f"断开连接失败: {e}")
    
    def show_machine_context_menu(self, event):
        """显示机器右键菜单"""
        # 获取点击位置的项
        item = self.machine_tree.identify_row(event.y)
        if item:
            # 选中该项
            self.machine_tree.selection_set(item)
            # 显示右键菜单
            self.machine_context_menu.post(event.x_root, event.y_root)
    
    def set_selected_as_target(self):
        """将选中的机器设置为目标"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择机器")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        
        # 弹出对话框让用户选择应用
        app_name = tk.simpledialog.askstring("设置目标", f"请输入机器 {machine_id} 上的应用名称:")
        if app_name:
            try:
                if self.server.set_target(machine_id, app_name):
                    self.current_machine_id = machine_id
                    self.current_app_name = app_name
                    # 更新仪表板显示
                    self.current_target_label.config(text=f"{machine_id} - {app_name}", foreground="green")
                    messagebox.showinfo("成功", f"目标已设置为: {machine_id} - {app_name}")
                else:
                    messagebox.showerror("错误", "设置目标失败")
            except Exception as e:
                messagebox.showerror("错误", f"设置目标失败: {str(e)}")
    
    def show_machine_details(self):
        """显示机器详情"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择机器")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        machine_ip = self.machine_tree.item(selection[0])['values'][1]
        machine_port = self.machine_tree.item(selection[0])['values'][2]
        machine_status = self.machine_tree.item(selection[0])['values'][3]
        machine_apps = self.machine_tree.item(selection[0])['values'][4]
        machine_time = self.machine_tree.item(selection[0])['values'][5]
        
        details = f"""机器详情:
        
机器ID: {machine_id}
IP地址: {machine_ip}
端口: {machine_port}
状态: {machine_status}
应用: {machine_apps or '无'}
连接时间: {machine_time}
        """
        
        messagebox.showinfo("机器详情", details)
    
    def quick_set_target(self):
        """快速设置目标"""
        if not self.is_running or not self.server:
            messagebox.showwarning("警告", "服务器未启动")
            return
        
        # 获取当前选中的机器
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择机器")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        
        # 弹出对话框让用户选择应用
        app_name = tk.simpledialog.askstring("快速设置目标", f"请输入机器 {machine_id} 上的应用名称:")
        if app_name:
            try:
                if self.server.set_target(machine_id, app_name):
                    self.current_machine_id = machine_id
                    self.current_app_name = app_name
                    self.current_target_label.config(text=f"{machine_id} - {app_name}", foreground="green")
                    messagebox.showinfo("成功", f"目标已设置为: {machine_id} - {app_name}")
                else:
                    messagebox.showerror("错误", "设置目标失败")
            except Exception as e:
                messagebox.showerror("错误", f"设置目标失败: {str(e)}")
    
    def set_target(self):
        """设置目标机器和应用"""
        machine_id = self.machine_id_entry.get().strip()
        app_name = self.app_name_entry.get().strip()
        
        if not machine_id or not app_name:
            messagebox.showwarning("警告", "请输入机器ID和应用名称")
            return
        
        if not self.is_running or not self.server:
            messagebox.showwarning("警告", "服务器未启动")
            return
        
        try:
            if self.server.set_target(machine_id, app_name):
                self.current_machine_id = machine_id
                self.current_app_name = app_name
                # 更新仪表板显示
                self.current_target_label.config(text=f"{machine_id} - {app_name}", foreground="green")
                messagebox.showinfo("成功", f"目标已设置为: {machine_id} - {app_name}")
            else:
                messagebox.showerror("错误", "设置目标失败")
        except Exception as e:
            messagebox.showerror("错误", f"设置目标失败: {str(e)}")
    
    def take_screenshot(self):
        """截图操作"""
        if not self.check_target():
            return
        
        self.start_progress("正在截图...")
        self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 开始截图操作...\n")
        
        try:
            result = self.server.get_screenshot()
            if result.get("success"):
                self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 截图成功\n")
                self.update_status("截图操作成功")
            else:
                self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 截图失败: {result.get('error')}\n")
                self.update_status("截图操作失败")
        except Exception as e:
            self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 截图操作异常: {str(e)}\n")
            self.update_status("截图操作异常")
        finally:
            self.stop_progress()
    
    def start_progress(self, message):
        """开始显示进度"""
        self.progress_bar.start()
        self.update_status(message)
        
    def stop_progress(self):
        """停止显示进度"""
        self.progress_bar.stop()
        
    def click_element(self):
        """点击元素操作"""
        if not self.check_target():
            return
        
        element_path = simpledialog.askstring("点击元素", "请输入元素路径:")
        if not element_path:
            return
        
        self.start_progress("正在点击元素...")
        self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 开始点击元素: {element_path}\n")
        
        try:
            result = self.server.click_element(element_path)
            self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 点击元素成功: {result}\n")
            self.update_status("点击元素操作成功")
        except Exception as e:
            self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 点击元素失败: {str(e)}\n")
            self.update_status("点击元素操作失败")
        finally:
            self.stop_progress()
    
    def click_image(self):
        """点击图片操作"""
        if not self.check_target():
            return
        
        image_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not image_path:
            return
        
        self.start_progress("正在点击图片...")
        self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 开始点击图片: {image_path}\n")
        
        try:
            result = self.server.click_image(image_path)
            if result.get("success"):
                self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 点击图片成功\n")
                self.update_status("点击图片操作成功")
            else:
                self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 点击图片失败: {result.get('error')}\n")
                self.update_status("点击图片操作失败")
        except Exception as e:
            self.result_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 点击图片操作异常: {str(e)}\n")
            self.update_status("点击图片操作异常")
        finally:
            self.stop_progress()
    
    def check_target(self):
        """检查是否已设置目标"""
        if not self.is_running or not self.server:
            messagebox.showwarning("警告", "服务器未启动")
            return False
        
        if not self.current_machine_id or not self.current_app_name:
            messagebox.showwarning("警告", "请先设置目标机器和应用")
            return False
        
        return True
    
    def refresh_script_list(self):
        """刷新脚本列表"""
        # 清空现有列表
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        # 加载脚本
        scripts = self.script_manager.get_all_scripts()
        for script in scripts:
            self.script_tree.insert("", "end", values=(
                script["id"],
                script["name"],
                script["status"],
                script["runCount"]
            ))
    
    def new_script(self):
        """新建脚本"""
        self.script_name_entry.delete(0, tk.END)
        self.script_desc_entry.delete(0, tk.END)
        self.script_content_text.delete(1.0, tk.END)
        
        # 生成默认名称
        default_name = f"新脚本_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.script_name_entry.insert(0, default_name)
    
    def edit_script(self):
        """编辑脚本"""
        selection = self.script_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的脚本")
            return
        
        script_id = self.script_tree.item(selection[0])['values'][0]
        script = self.script_manager.get_script(script_id)
        
        if script:
            self.script_name_entry.delete(0, tk.END)
            self.script_name_entry.insert(0, script["name"])
            
            self.script_desc_entry.delete(0, tk.END)
            self.script_desc_entry.insert(0, script.get("description", ""))
            
            self.script_content_text.delete(1.0, tk.END)
            self.script_content_text.insert(1.0, script["content"])
    
    @handle_exceptions
    def save_script(self):
        """保存脚本"""
        name = self.script_name_entry.get().strip()
        description = self.script_desc_entry.get().strip()
        content = self.script_content_text.get(1.0, tk.END).strip()
        
        if not name or not content:
            messagebox.showwarning("警告", "脚本名称和内容不能为空")
            return
        
        script = self.script_manager.create_script(name, description, content)
        messagebox.showinfo("成功", "脚本保存成功")
        self.refresh_script_list()
        self.update_status("脚本保存成功")
        logger.info(f"脚本 '{name}' 保存成功")
    
    def delete_script(self):
        """删除脚本"""
        selection = self.script_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的脚本")
            return
        
        script_id = self.script_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("确认", "确定要删除这个脚本吗？"):
            try:
                if self.script_manager.delete_script(script_id):
                    messagebox.showinfo("成功", "脚本删除成功")
                    self.refresh_script_list()
                else:
                    messagebox.showerror("错误", "脚本删除失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除脚本失败: {str(e)}")
    
    @handle_exceptions
    def run_script(self):
        """运行脚本"""
        selection = self.script_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要运行的脚本")
            return
        
        script_id = self.script_tree.item(selection[0])['values'][0]
        script = self.script_manager.get_script(script_id)
        
        if not script:
            messagebox.showerror("错误", "脚本不存在")
            return
        
        if messagebox.askyesno("确认", f"确定要运行脚本 '{script['name']}' 吗？"):
            self.start_progress(f"正在运行脚本: {script['name']}")
            self.update_status(f"正在运行脚本: {script['name']}")
            
            try:
                # 创建临时文件运行脚本
                with open("temp_script.py", "w", encoding="utf-8") as f:
                    f.write(script["content"])
                
                result = subprocess.run([sys.executable, "temp_script.py"], 
                                     capture_output=True, text=True, timeout=30)
                
                os.remove("temp_script.py")
                
                if result.returncode == 0:
                    messagebox.showinfo("成功", f"脚本运行成功\n输出: {result.stdout}")
                    self.update_status(f"脚本 '{script['name']}' 运行成功")
                    logger.info(f"脚本 '{script['name']}' 运行成功")
                else:
                    messagebox.showerror("错误", f"脚本运行失败\n错误: {result.stderr}")
                    self.update_status(f"脚本 '{script['name']}' 运行失败")
                    logger.error(f"脚本 '{script['name']}' 运行失败: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                messagebox.showerror("错误", "脚本执行超时")
                self.update_status(f"脚本 '{script['name']}' 执行超时")
                logger.warning(f"脚本 '{script['name']}' 执行超时")
            finally:
                self.stop_progress()
    
    def run(self):
        """运行应用"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("应用被用户中断")
        finally:
            if self.server:
                self.server.close()

def main():
    """主函数"""
    try:
        app = AutoTestApp()
        app.run()
    except Exception as e:
        error_msg = f"应用启动失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        # 尝试显示错误对话框，如果失败则打印到控制台
        try:
            messagebox.showerror("严重错误", error_msg)
        except:
            print(f"错误: {error_msg}")
            print(f"详细错误信息: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
