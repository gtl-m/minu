#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minu Editor v1.4 - 命令行版
一个轻量级Python代码编辑器，内置命令行终端

使用方式：
    python minu.py              # 启动编辑器
    python minu.py test.py      # 打开指定文件

声明：
本软件采用MIT许可证开源，可免费使用、修改和分发。

项目地址：https://github.com/gtl-m/minu
网站：https://minu.micronull.cn/
"""

import tkinter as tk
from tkinter import filedialog, messagebox, font
from tkinter import ttk
import subprocess
import sys
import threading
import re
import os
import argparse

class SyntaxHighlighter:
    """语法高亮引擎"""
    
    KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
        'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
        'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield'
    }
    
    BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr',
        'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate',
        'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
        'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
        'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open',
        'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr',
        'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
    }
    
    CONSTANTS = {'True', 'False', 'None', 'Ellipsis', 'NotImplemented'}
    
    def __init__(self, text_widget):
        self.text = text_widget
        self.tag_configs = {
            'keyword': '#FF7700', 'builtin': '#0088FF', 'string': '#00AA00',
            'comment': '#888888', 'number': '#FF00FF', 'decorator': '#AA00AA',
            'function': '#00AAAA', 'class': '#0000FF', 'constant': '#DD00DD',
        }
        
        for tag, color in self.tag_configs.items():
            self.text.tag_config(tag, foreground=color)
        
        self.text.tag_config('comment', foreground='#888888', font=('Courier', 10, 'italic'))
        self.text.tag_config('string', foreground='#00AA00', font=('Courier', 10, 'bold'))
        self.text.tag_config('keyword', foreground='#FF7700', font=('Courier', 10, 'bold'))
        self.text.tag_config('function', foreground='#00AAAA', font=('Courier', 10, 'bold'))
        self.text.tag_config('class', foreground='#0000FF', font=('Courier', 10, 'bold'))
        
    def highlight(self, event=None):
        for tag in self.tag_configs:
            self.text.tag_remove(tag, "1.0", tk.END)
        
        content = self.text.get("1.0", tk.END)
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            self.highlight_line(line, line_num)
            
    def highlight_line(self, line, line_num):
        if not line.strip():
            return
            
        string_regions = self.find_string_regions(line)
        comment_pos = self.find_comment(line, string_regions)
        
        if comment_pos is not None:
            self.text.tag_add('comment', f"{line_num}.{comment_pos}", f"{line_num}.{len(line)}")
            line = line[:comment_pos]
            
        for start, end in string_regions:
            if start < len(line):
                self.text.tag_add('string', f"{line_num}.{start}", f"{line_num}.{min(end, len(line))}")
        
        self.highlight_keywords(line, line_num, string_regions, comment_pos)
        self.highlight_numbers(line, line_num, string_regions, comment_pos)
        self.highlight_decorators(line, line_num, string_regions)
        self.highlight_functions_classes(line, line_num, string_regions)
        
    def find_string_regions(self, line):
        regions = []
        in_string = False
        string_char = None
        escape = False
        start = 0
        
        for i, char in enumerate(line):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if not in_string and char in ('"', "'"):
                in_string = True
                string_char = char
                start = i
            elif in_string and char == string_char:
                in_string = False
                regions.append((start, i + 1))
                
        if in_string:
            regions.append((start, len(line)))
        return regions
        
    def find_comment(self, line, string_regions):
        for i, char in enumerate(line):
            if char == '#':
                in_string = False
                for start, end in string_regions:
                    if start <= i < end:
                        in_string = True
                        break
                if not in_string:
                    return i
        return None
        
    def highlight_keywords(self, line, line_num, string_regions, comment_pos):
        def is_valid(start, end):
            if comment_pos is not None and start >= comment_pos:
                return False
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        for keyword in self.KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', line):
                s, e = match.span()
                if is_valid(s, e):
                    self.text.tag_add('keyword', f"{line_num}.{s}", f"{line_num}.{e}")
                    
        for builtin in self.BUILTINS:
            for match in re.finditer(r'\b' + re.escape(builtin) + r'\b', line):
                s, e = match.span()
                if is_valid(s, e):
                    self.text.tag_add('builtin', f"{line_num}.{s}", f"{line_num}.{e}")
                    
        for const in self.CONSTANTS:
            for match in re.finditer(r'\b' + re.escape(const) + r'\b', line):
                s, e = match.span()
                if is_valid(s, e):
                    self.text.tag_add('constant', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_numbers(self, line, line_num, string_regions, comment_pos):
        patterns = [r'\b0x[0-9a-fA-F]+\b', r'\b0b[01]+\b', r'\b0o[0-7]+\b',
                   r'\b\d+\.\d+\b', r'\b\d+\b']
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                s, e = match.span()
                valid = True
                if comment_pos is not None and s >= comment_pos:
                    valid = False
                for ss, ee in string_regions:
                    if (ss <= s < ee) or (ss < e <= ee):
                        valid = False
                        break
                if valid:
                    self.text.tag_add('number', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_decorators(self, line, line_num, string_regions):
        for match in re.finditer(r'@\w+', line):
            s, e = match.span()
            valid = True
            for ss, ee in string_regions:
                if (ss <= s < ee) or (ss < e <= ee):
                    valid = False
                    break
            if valid:
                self.text.tag_add('decorator', f"{line_num}.{s}", f"{line_num}.{e}")
                
    def highlight_functions_classes(self, line, line_num, string_regions):
        for match in re.finditer(r'\bdef\s+(\w+)\s*\(', line):
            s, e = match.span(1)
            valid = True
            for ss, ee in string_regions:
                if (ss <= s < ee) or (ss < e <= ee):
                    valid = False
                    break
            if valid:
                self.text.tag_add('function', f"{line_num}.{s}", f"{line_num}.{e}")
                
        for match in re.finditer(r'\bclass\s+(\w+)', line):
            s, e = match.span(1)
            valid = True
            for ss, ee in string_regions:
                if (ss <= s < ee) or (ss < e <= ee):
                    valid = False
                    break
            if valid:
                self.text.tag_add('class', f"{line_num}.{s}", f"{line_num}.{e}")


class Terminal:
    """命令行终端组件"""
    
    def __init__(self, parent):
        self.parent = parent
        self.process = None
        self.current_dir = os.getcwd()
        
        # 创建终端框架
        self.frame = tk.LabelFrame(parent, text="终端", font=('Arial', 9))
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 终端显示和滚动条容器
        text_frame = tk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 终端显示区域
        self.output_text = tk.Text(text_frame, font=('Courier', 10), 
                                   bg='#1e1e1e', fg='#d4d4d4', 
                                   wrap=tk.WORD, height=10)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # 配置标签样式
        self.output_text.tag_config('prompt', foreground='#4ec9b0')
        self.output_text.tag_config('error', foreground='#f48771')
        self.output_text.tag_config('stdout', foreground='#d4d4d4')
        self.output_text.tag_config('stderr', foreground='#f48771')
        
        # 输入框架
        input_frame = tk.Frame(self.frame)
        input_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # 提示符
        self.prompt_label = tk.Label(input_frame, text=f"{self.current_dir}> ", 
                                     font=('Courier', 10), fg='#4ec9b0', bg='#2d2d2d')
        self.prompt_label.pack(side=tk.LEFT)
        
        # 命令输入框
        self.command_entry = tk.Entry(input_frame, font=('Courier', 10),
                                      bg='#2d2d2d', fg='#d4d4d4',
                                      insertbackground='white')
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.bind('<Up>', self.previous_command)
        self.command_entry.bind('<Down>', self.next_command)
        
        # 历史命令
        self.history = []
        self.history_index = -1
        
    def update_prompt(self):
        """更新提示符路径"""
        self.prompt_label.config(text=f"{self.current_dir}> ")
        
    def previous_command(self, event=None):
        """上一条命令"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.history[-(self.history_index + 1)])
        return "break"
        
    def next_command(self, event=None):
        """下一条命令"""
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.command_entry.delete(0, tk.END)
        return "break"
        
    def execute_command(self, event=None):
        """执行命令"""
        cmd = self.command_entry.get().strip()
        if not cmd:
            return
            
        # 显示输入的命令
        self.output_text.insert(tk.END, f"\n{self.current_dir}> {cmd}\n", 'prompt')
        self.command_entry.delete(0, tk.END)
        self.output_text.see(tk.END)
        
        # 保存到历史
        self.history.append(cmd)
        self.history_index = -1
        
        # 处理内置命令
        if cmd.lower() == 'cls' or cmd.lower() == 'clear':
            self.output_text.delete(1.0, tk.END)
            return
        elif cmd.lower() == 'exit':
            self.parent.quit()
            return
        elif cmd.lower().startswith('cd '):
            try:
                new_dir = cmd[3:].strip()
                if new_dir == '~':
                    new_dir = os.path.expanduser('~')
                os.chdir(new_dir)
                self.current_dir = os.getcwd()
                self.update_prompt()
                self.output_text.insert(tk.END, f"{self.current_dir}> \n", 'prompt')
            except Exception as e:
                self.output_text.insert(tk.END, f"错误: {e}\n", 'error')
            return
        elif cmd.lower() == 'dir' or cmd.lower() == 'ls':
            try:
                files = os.listdir('.')
                for f in files:
                    self.output_text.insert(tk.END, f"{f}\n", 'stdout')
            except Exception as e:
                self.output_text.insert(tk.END, f"错误: {e}\n", 'error')
            return
        elif cmd.lower().startswith('python '):
            script = cmd[7:].strip()
            self.run_python_script(script)
            return
        elif cmd.lower().startswith('pip '):
            self.run_system_command(cmd)
            return
            
        # 其他命令直接通过系统执行
        self.run_system_command(cmd)
        
    def run_python_script(self, script):
        """运行 Python 脚本"""
        if not os.path.exists(script):
            self.output_text.insert(tk.END, f"错误: 文件 '{script}' 不存在\n", 'error')
            return
            
        def run():
            try:
                process = subprocess.Popen(
                    [sys.executable, script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    cwd=self.current_dir
                )
                
                for line in iter(process.stdout.readline, ''):
                    self.output_text.insert(tk.END, line, 'stdout')
                    self.output_text.see(tk.END)
                    self.parent.update_idletasks()
                
                stderr = process.stderr.read()
                if stderr:
                    self.output_text.insert(tk.END, stderr, 'stderr')
                    self.output_text.see(tk.END)
                
                process.wait()
                self.output_text.insert(tk.END, f"\n[退出码: {process.returncode}]\n", 'stdout')
                self.output_text.see(tk.END)
                self.update_prompt()
                
            except Exception as e:
                self.output_text.insert(tk.END, f"\n运行错误: {e}\n", 'error')
                self.output_text.see(tk.END)
        
        threading.Thread(target=run, daemon=True).start()
        
    def run_system_command(self, cmd):
        """运行系统命令"""
        def run():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    shell=True,
                    cwd=self.current_dir
                )
                
                for line in iter(process.stdout.readline, ''):
                    self.output_text.insert(tk.END, line, 'stdout')
                    self.output_text.see(tk.END)
                    self.parent.update_idletasks()
                
                stderr = process.stderr.read()
                if stderr:
                    self.output_text.insert(tk.END, stderr, 'stderr')
                    self.output_text.see(tk.END)
                
                process.wait()
                self.update_prompt()
                
            except Exception as e:
                self.output_text.insert(tk.END, f"\n执行错误: {e}\n", 'error')
                self.output_text.see(tk.END)
        
        threading.Thread(target=run, daemon=True).start()


class MinuEditor:
    """Minu编辑器主类"""
    
    VERSION = "1.4"
    APP_NAME = "Minu"
    
    def __init__(self, root, open_file=None):
        self.root = root
        self.root.title(f"{self.APP_NAME} {self.VERSION}")
        
        # 全屏相关变量
        self.is_fullscreen = True
        self.root.attributes('-fullscreen', True)
        
        self.current_file = open_file
        self.is_running = False
        self.is_saved = True
        
        self.setup_ui()
        self.setup_menu()
        
        # 初始化语法高亮器
        self.highlighter = SyntaxHighlighter(self.text)
        
        # 绑定事件
        self.text.bind('<KeyRelease>', self.on_text_change)
        self.text.bind('<ButtonRelease-1>', self.update_line_numbers)
        self.text.bind('<MouseWheel>', self.update_line_numbers)
        
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen())
        
        self.highlight_timer = None
        self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 已就绪", fg='green')
        
        # 如果指定了文件，自动打开
        if open_file and os.path.exists(open_file):
            self.load_file(open_file)
        
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.toggle_fullscreen()
        
    def setup_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        toolbar = tk.Frame(main_frame, bg='#E0E0E0', height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 工具栏按钮
        buttons = [
            ("📁 新建", self.new_file), ("📂 打开", self.open_file), 
            ("💾 保存", self.save_file), ("▶ 运行代码(F5)", self.run_current_code),
            ("🗑 清空终端", self.clear_terminal), ("🎨 高亮", self.force_highlight), 
            ("🖥 窗口模式", self.toggle_fullscreen)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(toolbar, text=text, command=cmd, 
                          bg='white', relief=tk.RAISED, padx=10)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 分隔线
        tk.Frame(toolbar, width=2, bg='gray', relief=tk.RAISED).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 字体大小
        tk.Label(toolbar, text="字体:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.StringVar(value="12")
        font_spin = tk.Spinbox(toolbar, from_=8, to=30, width=3, 
                               textvariable=self.font_size_var, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=2)
        
        # 主题选择
        tk.Label(toolbar, text="主题:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(toolbar, textvariable=self.theme_var, 
                                  values=['default', 'dark', 'light'], width=8)
        theme_combo.pack(side=tk.LEFT, padx=2)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # 状态标签
        self.status_label = tk.Label(toolbar, text="就绪", bg='#E0E0E0', fg='green')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 光标位置
        self.cursor_label = tk.Label(toolbar, text="行:1 列:1", bg='#E0E0E0')
        self.cursor_label.pack(side=tk.RIGHT, padx=10)
        
        # 版本标签
        version_label = tk.Label(toolbar, text=f"v{self.VERSION}", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        version_label.pack(side=tk.RIGHT, padx=5)
        
        # 全屏提示
        fullscreen_label = tk.Label(toolbar, text="ESC/F11:全屏", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        fullscreen_label.pack(side=tk.RIGHT, padx=5)
        
        # 创建分割窗口
        paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 编辑区域框架
        edit_frame = tk.Frame(paned)
        paned.add(edit_frame, height=350)
        
        # 行号区域
        self.line_numbers = tk.Text(edit_frame, width=5, padx=3, takefocus=0, 
                                   border=0, background='#f0f0f0', state='disabled',
                                   wrap='none', font=('Courier', 12))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 文本编辑区域
        self.text = tk.Text(edit_frame, font=('Courier', 12), wrap=tk.WORD,
                           undo=True, tabs=('4c'), background='white',
                           foreground='black', selectbackground='#3399FF')
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(edit_frame, command=self.on_scroll)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)
        self.line_numbers.config(yscrollcommand=scrollbar.set)
        
        # 终端区域
        self.terminal = Terminal(main_frame)
        
        self.update_line_numbers()
        self.update_cursor_position()
        
    def run_current_code(self):
        """运行当前编辑的代码"""
        if not self.current_file:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                            delete=False, encoding='utf-8') as f:
                f.write(self.text.get(1.0, tk.END))
                filename = f.name
            self.terminal.run_python_script(filename)
        else:
            self.save_file()
            self.terminal.run_python_script(self.current_file)
            
    def clear_terminal(self):
        """清空终端"""
        self.terminal.output_text.delete(1.0, tk.END)
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="打开", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="保存", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="另存为", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", accelerator="Ctrl+Q", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", accelerator="Ctrl+Z", command=self.text.edit_undo)
        edit_menu.add_command(label="重做", accelerator="Ctrl+Y", command=self.text.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="复制", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="粘贴", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="全选", accelerator="Ctrl+A", command=self.select_all)
        
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="运行", menu=run_menu)
        run_menu.add_command(label="运行当前代码", accelerator="F5", command=self.run_current_code)
        run_menu.add_command(label="清空终端", command=self.clear_terminal)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="窗口模式", command=self.toggle_fullscreen)
        view_menu.add_command(label="重新高亮", command=self.force_highlight)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于 Minu", command=self.show_about)
        
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<F5>', lambda e: self.run_current_code())
        self.root.bind('<KeyRelease>', self.update_cursor_position)
        
    def load_file(self, filepath):
        """加载文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.text.delete(1.0, tk.END)
                self.text.insert(1.0, f.read())
            self.current_file = filepath
            self.is_saved = True
            self.update_line_numbers()
            self.highlighter.highlight()
            self.status_label.config(text=f"已打开: {filepath}", fg='green')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")
        
    def on_text_change(self, event=None):
        self.is_saved = False
        self.update_line_numbers()
        if self.highlight_timer:
            self.root.after_cancel(self.highlight_timer)
        self.highlight_timer = self.root.after(500, self.highlighter.highlight)
        
    def force_highlight(self):
        self.highlighter.highlight()
        self.status_label.config(text="语法高亮完成", fg='blue')
        self.root.after(2000, lambda: self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 就绪", fg='green'))
        
    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        line_count = int(self.text.index('end-1c').split('.')[0])
        line_numbers_str = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(1.0, line_numbers_str)
        self.line_numbers.config(state='disabled')
        
    def update_cursor_position(self, event=None):
        cursor_pos = self.text.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        self.cursor_label.config(text=f"行:{line} 列:{int(col)+1}")
        
    def on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)
        
    def change_font(self):
        size = int(self.font_size_var.get())
        self.text.config(font=('Courier', size))
        self.line_numbers.config(font=('Courier', size))
        
    def change_theme(self, event=None):
        theme = self.theme_var.get()
        if theme == 'dark':
            self.text.config(bg='#2E2E2E', fg='#FFFFFF', insertbackground='white')
            self.line_numbers.config(bg='#1E1E1E', fg='#808080')
        elif theme == 'light':
            self.text.config(bg='#FFFFFF', fg='#000000', insertbackground='black')
            self.line_numbers.config(bg='#F0F0F0', fg='#000000')
        else:
            self.text.config(bg='white', fg='black', insertbackground='black')
            self.line_numbers.config(bg='#f0f0f0', fg='#000000')
        self.highlighter.highlight()
        
    def new_file(self):
        if not self.is_saved and self.text.get(1.0, tk.END).strip():
            if not messagebox.askyesno("新建", "是否保存当前文件？"):
                return
            self.save_file()
        self.text.delete(1.0, tk.END)
        self.current_file = None
        self.is_saved = True
        self.update_line_numbers()
        self.status_label.config(text="新建文件", fg='blue')
        
    def open_file(self):
        if not self.is_saved and self.text.get(1.0, tk.END).strip():
            if not messagebox.askyesno("打开", "是否保存当前文件？"):
                return
            self.save_file()
            
        file = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file:
            self.load_file(file)
                
    def save_file(self):
        if not self.current_file:
            return self.save_as_file()
        else:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.text.get(1.0, tk.END))
                self.is_saved = True
                self.status_label.config(text=f"已保存: {self.current_file}", fg='green')
                return True
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
                return False
                
    def save_as_file(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile="untitled.py"
        )
        if file:
            self.current_file = file
            return self.save_file()
        return False
        
    def cut(self):
        self.text.event_generate("<<Cut>>")
        
    def copy(self):
        self.text.event_generate("<<Copy>>")
        
    def paste(self):
        self.text.event_generate("<<Paste>>")
        self.update_line_numbers()
        
    def select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)
        
    def show_about(self):
        about_text = f"""{self.APP_NAME}编辑器 {self.VERSION}

作者：Gtl
邮箱：wrmfwv@163.com
公司：Micronull Inc.
网址：https://minu.micronull.cn/
GitHub：https://github.com/gtl-m/minu

© 2026 Minu"""
        messagebox.showinfo(f"关于 {self.APP_NAME}", about_text)


def main():
    """主函数 - 处理命令行参数"""
    parser = argparse.ArgumentParser(
        prog='minu',
        description='Minu Editor - 轻量级Python代码编辑器',
        epilog='示例: python minu.py test.py'
    )
    parser.add_argument('file', nargs='?', help='要打开的文件路径')
    parser.add_argument('--version', '-v', action='version', version=f'Minu Editor v{MinuEditor.VERSION}')
    
    args = parser.parse_args()
    
    root = tk.Tk()
    open_file = args.file if args.file and os.path.exists(args.file) else None
    app = MinuEditor(root, open_file)
    root.mainloop()


if __name__ == "__main__":
    main()