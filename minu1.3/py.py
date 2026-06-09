import tkinter as tk
from tkinter import filedialog, messagebox, font
from tkinter import ttk
import subprocess
import sys
import threading
import re

class SyntaxHighlighter:
    """语法高亮引擎"""
    
    # Python关键字
    KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
        'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
        'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield'
    }
    
    # 内置函数
    BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr',
        'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate',
        'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
        'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
        'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open',
        'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr',
        'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
    }
    
    # 常量
    CONSTANTS = {'True', 'False', 'None', 'Ellipsis', 'NotImplemented'}
    
    def __init__(self, text_widget):
        self.text = text_widget
        self.tag_configs = {
            'keyword': '#FF7700',      # 橙色
            'builtin': '#0088FF',      # 蓝色
            'string': '#00AA00',       # 绿色
            'comment': '#888888',      # 灰色
            'number': '#FF00FF',       # 紫色
            'decorator': '#AA00AA',    # 紫罗兰
            'function': '#00AAAA',     # 青色
            'class': '#0000FF',        # 蓝色
            'constant': '#DD00DD',     # 品红
        }
        
        # 配置标签样式
        for tag, color in self.tag_configs.items():
            self.text.tag_config(tag, foreground=color)
        
        # 特殊样式
        self.text.tag_config('comment', foreground='#888888', font=('Courier', 10, 'italic'))
        self.text.tag_config('string', foreground='#00AA00', font=('Courier', 10, 'bold'))
        self.text.tag_config('keyword', foreground='#FF7700', font=('Courier', 10, 'bold'))
        self.text.tag_config('function', foreground='#00AAAA', font=('Courier', 10, 'bold'))
        self.text.tag_config('class', foreground='#0000FF', font=('Courier', 10, 'bold'))
        
    def highlight(self, event=None):
        """高亮整个文档"""
        # 清除所有标签
        for tag in self.tag_configs:
            self.text.tag_remove(tag, "1.0", tk.END)
        
        # 获取所有文本
        content = self.text.get("1.0", tk.END)
        
        # 逐行处理
        lines = content.split('\n')
        line_num = 1
        
        for line in lines:
            self.highlight_line(line, line_num)
            line_num += 1
            
    def highlight_line(self, line, line_num):
        """高亮单行"""
        if not line.strip():
            return
            
        # 处理字符串（需要特殊处理，避免字符串内高亮）
        string_regions = self.find_string_regions(line)
        
        # 处理注释
        comment_pos = self.find_comment(line, string_regions)
        if comment_pos is not None:
            comment_start = f"{line_num}.{comment_pos}"
            comment_end = f"{line_num}.{len(line)}"
            self.text.tag_add('comment', comment_start, comment_end)
            line = line[:comment_pos]  # 注释后的内容不处理
            
        # 高亮字符串
        for start, end in string_regions:
            if start < len(line):
                str_start = f"{line_num}.{start}"
                str_end = f"{line_num}.{min(end, len(line))}"
                self.text.tag_add('string', str_start, str_end)
        
        # 处理其他语法元素
        self.highlight_keywords(line, line_num, string_regions, comment_pos)
        self.highlight_numbers(line, line_num, string_regions, comment_pos)
        self.highlight_decorators(line, line_num, string_regions)
        self.highlight_functions_classes(line, line_num, string_regions)
        
    def find_string_regions(self, line):
        """查找字符串区域"""
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
                string_char = None
            elif in_string and char == '\\':
                escape = True
                
        # 处理多行字符串开始
        if in_string:
            regions.append((start, len(line)))
            
        return regions
        
    def find_comment(self, line, string_regions):
        """查找注释位置（不在字符串内）"""
        for i, char in enumerate(line):
            if char == '#':
                # 检查是否在字符串内
                in_string = False
                for start, end in string_regions:
                    if start <= i < end:
                        in_string = True
                        break
                if not in_string:
                    return i
        return None
        
    def highlight_keywords(self, line, line_num, string_regions, comment_pos):
        """高亮关键字"""
        for keyword in self.KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', line):
                start, end = match.span()
                if self.is_valid_region(start, end, string_regions, comment_pos):
                    tag_start = f"{line_num}.{start}"
                    tag_end = f"{line_num}.{end}"
                    self.text.tag_add('keyword', tag_start, tag_end)
                    
        # 高亮内置函数
        for builtin in self.BUILTINS:
            for match in re.finditer(r'\b' + re.escape(builtin) + r'\b', line):
                start, end = match.span()
                if self.is_valid_region(start, end, string_regions, comment_pos):
                    tag_start = f"{line_num}.{start}"
                    tag_end = f"{line_num}.{end}"
                    self.text.tag_add('builtin', tag_start, tag_end)
                    
        # 高亮常量
        for const in self.CONSTANTS:
            for match in re.finditer(r'\b' + re.escape(const) + r'\b', line):
                start, end = match.span()
                if self.is_valid_region(start, end, string_regions, comment_pos):
                    tag_start = f"{line_num}.{start}"
                    tag_end = f"{line_num}.{end}"
                    self.text.tag_add('constant', tag_start, tag_end)
                    
    def highlight_numbers(self, line, line_num, string_regions, comment_pos):
        """高亮数字"""
        # 整数、浮点数、十六进制、二进制、八进制
        patterns = [
            r'\b0x[0-9a-fA-F]+\b',  # 十六进制
            r'\b0b[01]+\b',         # 二进制
            r'\b0o[0-7]+\b',        # 八进制
            r'\b\d+\.\d+\b',        # 浮点数
            r'\b\d+\b',             # 整数
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                start, end = match.span()
                if self.is_valid_region(start, end, string_regions, comment_pos):
                    tag_start = f"{line_num}.{start}"
                    tag_end = f"{line_num}.{end}"
                    self.text.tag_add('number', tag_start, tag_end)
                    
    def highlight_decorators(self, line, line_num, string_regions):
        """高亮装饰器"""
        for match in re.finditer(r'@\w+', line):
            start, end = match.span()
            if self.is_valid_region(start, end, string_regions, None):
                tag_start = f"{line_num}.{start}"
                tag_end = f"{line_num}.{end}"
                self.text.tag_add('decorator', tag_start, tag_end)
                
    def highlight_functions_classes(self, line, line_num, string_regions):
        """高亮函数和类定义"""
        # 函数定义
        for match in re.finditer(r'\bdef\s+(\w+)\s*\(', line):
            start = match.start(1)
            end = match.end(1)
            if self.is_valid_region(start, end, string_regions, None):
                tag_start = f"{line_num}.{start}"
                tag_end = f"{line_num}.{end}"
                self.text.tag_add('function', tag_start, tag_end)
                
        # 类定义
        for match in re.finditer(r'\bclass\s+(\w+)', line):
            start = match.start(1)
            end = match.end(1)
            if self.is_valid_region(start, end, string_regions, None):
                tag_start = f"{line_num}.{start}"
                tag_end = f"{line_num}.{end}"
                self.text.tag_add('class', tag_start, tag_end)
                
    def is_valid_region(self, start, end, string_regions, comment_pos):
        """检查区域是否有效（不在字符串或注释中）"""
        # 检查是否在注释中
        if comment_pos is not None and start >= comment_pos:
            return False
            
        # 检查是否在字符串中
        for str_start, str_end in string_regions:
            if (str_start <= start < str_end) or (str_start < end <= str_end):
                return False
                
        return True

class MinuEditor:
    """Minu编辑器主类"""
    
    VERSION = "1.3"
    APP_NAME = "Minu"
    
    def __init__(self, root):
        self.root = root
        # 只显示 Minu v1.3
        self.root.title(f"{self.APP_NAME} {self.VERSION}")
        
        # 全屏相关变量
        self.is_fullscreen = True  # 默认全屏
        
        # 设置默认全屏（真正的全屏模式）
        self.root.attributes('-fullscreen', True)
        
        self.current_file = None
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
        
        # 绑定全屏快捷键
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen())
        
        # 自动高亮定时器
        self.highlight_timer = None
        
        # 显示启动信息
        self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 已就绪", fg='green')
        
    def toggle_fullscreen(self, event=None):
        """切换全屏模式"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
    def exit_fullscreen(self, event=None):
        """退出全屏"""
        if self.is_fullscreen:
            self.toggle_fullscreen()
        
    def setup_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        self.toolbar = tk.Frame(main_frame, bg='#E0E0E0', height=35)
        self.toolbar.pack(fill=tk.X)
        self.toolbar.pack_propagate(False)
        
        # 工具栏按钮
        buttons = [
            ("📁 新建", self.new_file), ("📂 打开", self.open_file), 
            ("💾 保存", self.save_file), ("▶ 运行", self.run_code),
            ("⏹ 停止", self.stop_code), ("🗑 清空输出", self.clear_output),
            ("🎨 高亮", self.force_highlight), ("🖥 窗口模式", self.toggle_fullscreen)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(self.toolbar, text=text, command=cmd, 
                          bg='white', relief=tk.RAISED, padx=10)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 分隔线
        tk.Frame(self.toolbar, width=2, bg='gray', relief=tk.RAISED).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 字体大小
        tk.Label(self.toolbar, text="字体:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.StringVar(value="12")
        font_spin = tk.Spinbox(self.toolbar, from_=8, to=30, width=3, 
                               textvariable=self.font_size_var, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=2)
        
        # 主题选择
        tk.Label(self.toolbar, text="主题:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(self.toolbar, textvariable=self.theme_var, 
                                  values=['default', 'dark', 'light'], width=8)
        theme_combo.pack(side=tk.LEFT, padx=2)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # 状态标签
        self.status_label = tk.Label(self.toolbar, text="就绪", bg='#E0E0E0', fg='green')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 光标位置
        self.cursor_label = tk.Label(self.toolbar, text="行:1 列:1", bg='#E0E0E0')
        self.cursor_label.pack(side=tk.RIGHT, padx=10)
        
        # 版本标签
        version_label = tk.Label(self.toolbar, text=f"v{self.VERSION}", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        version_label.pack(side=tk.RIGHT, padx=5)
        
        # 全屏提示
        fullscreen_label = tk.Label(self.toolbar, text="按ESC/F11退出全屏", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        fullscreen_label.pack(side=tk.RIGHT, padx=5)
        
        # 创建分割窗口
        paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 编辑区域框架
        edit_frame = tk.Frame(paned)
        paned.add(edit_frame, height=450)
        
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
        
        # 输出区域
        output_frame = tk.LabelFrame(paned, text="运行输出")
        paned.add(output_frame, height=200)
        
        # 输出文本框
        self.output_text = tk.Text(output_frame, font=('Courier', 10), 
                                  fg='#00FF00', bg='black', wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置输出标签
        self.output_text.tag_config('error', foreground='#FF0000')
        self.output_text.tag_config('warning', foreground='#FFFF00')
        self.output_text.tag_config('info', foreground='#00FF00')
        
        # 输出滚动条
        output_scroll = tk.Scrollbar(self.output_text)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=output_scroll.set)
        output_scroll.config(command=self.output_text.yview)
        
        # 初始化
        self.update_line_numbers()
        self.update_cursor_position()
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="打开", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="保存", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="另存为", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", accelerator="Ctrl+Q", command=self.root.quit)
        
        # 编辑菜单
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
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="窗口模式", command=self.toggle_fullscreen)
        view_menu.add_command(label="重新高亮", command=self.force_highlight)
        
        # 运行菜单
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="运行", menu=run_menu)
        run_menu.add_command(label="运行代码", accelerator="F5", command=self.run_code)
        run_menu.add_command(label="停止运行", accelerator="F6", command=self.stop_code)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于 Minu", command=self.show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<F6>', lambda e: self.stop_code())
        self.root.bind('<KeyRelease>', self.update_cursor_position)
        
    def on_text_change(self, event=None):
        """文本改变时更新"""
        self.is_saved = False
        self.update_line_numbers()
        
        # 延迟高亮（提高性能）
        if self.highlight_timer:
            self.root.after_cancel(self.highlight_timer)
        self.highlight_timer = self.root.after(500, self.highlighter.highlight)
        
    def force_highlight(self):
        """强制重新高亮"""
        self.highlighter.highlight()
        self.status_label.config(text="语法高亮完成", fg='blue')
        self.root.after(2000, lambda: self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 就绪", fg='green'))
        
    def update_line_numbers(self, event=None):
        """更新行号"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        line_count = int(self.text.index('end-1c').split('.')[0])
        line_numbers_str = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(1.0, line_numbers_str)
        self.line_numbers.config(state='disabled')
        
    def update_cursor_position(self, event=None):
        """更新光标位置"""
        cursor_pos = self.text.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        self.cursor_label.config(text=f"行:{line} 列:{int(col)+1}")
        
    def on_scroll(self, *args):
        """同步滚动"""
        self.text.yview(*args)
        self.line_numbers.yview(*args)
        
    def change_font(self):
        """改变字体大小"""
        size = int(self.font_size_var.get())
        self.text.config(font=('Courier', size))
        self.line_numbers.config(font=('Courier', size))
        
    def change_theme(self, event=None):
        """改变主题"""
        theme = self.theme_var.get()
        if theme == 'dark':
            self.text.config(bg='#2E2E2E', fg='#FFFFFF', insertbackground='white')
            self.line_numbers.config(bg='#1E1E1E', fg='#808080')
        elif theme == 'light':
            self.text.config(bg='#FFFFFF', fg='#000000', insertbackground='black')
            self.line_numbers.config(bg='#F0F0F0', fg='#000000')
        else:  # default
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
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self.text.delete(1.0, tk.END)
                    self.text.insert(1.0, f.read())
                self.current_file = file
                self.is_saved = True
                self.update_line_numbers()
                self.highlighter.highlight()
                self.status_label.config(text=f"已打开: {file}", fg='green')
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {e}")
                
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
        
    def run_code(self):
        """运行代码"""
        if self.is_running:
            messagebox.showwarning("警告", "代码正在运行中，请先停止")
            return
            
        # 保存文件
        if self.current_file:
            self.save_file()
            filename = self.current_file
        else:
            # 临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                            delete=False, encoding='utf-8') as f:
                f.write(self.text.get(1.0, tk.END))
                filename = f.name
        
        self.clear_output()
        self.output_text.insert(tk.END, f"正在运行: {filename}\n", 'info')
        self.output_text.insert(tk.END, f"{'='*60}\n", 'info')
        self.status_label.config(text="运行中...", fg='orange')
        self.is_running = True
        
        def run():
            try:
                process = subprocess.Popen(
                    [sys.executable, filename],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    bufsize=1
                )
                
                # 读取输出
                for line in iter(process.stdout.readline, ''):
                    self.output_text.insert(tk.END, line)
                    self.output_text.see(tk.END)
                    self.root.update_idletasks()
                
                stderr = process.stderr.read()
                if stderr:
                    self.output_text.insert(tk.END, f"\n错误:\n{stderr}\n", 'error')
                
                process.wait()
                self.output_text.insert(tk.END, f"\n{'='*60}\n", 'info')
                self.output_text.insert(tk.END, f"程序退出，返回码: {process.returncode}\n", 'info')
                
            except Exception as e:
                self.output_text.insert(tk.END, f"\n运行错误: {e}\n", 'error')
            finally:
                self.is_running = False
                self.status_label.config(text="运行完成", fg='green')
                
                if not self.current_file and filename:
                    import os
                    try:
                        os.unlink(filename)
                    except:
                        pass
        
        threading.Thread(target=run, daemon=True).start()
        
    def stop_code(self):
        """停止运行"""
        if self.is_running:
            messagebox.showinfo("提示", "程序运行在独立进程中\n如需停止请关闭运行窗口")
        else:
            messagebox.showinfo("提示", "没有正在运行的程序")
            
    def clear_output(self):
        """清空输出"""
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="输出已清空", fg='blue')
        
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
        
This is a minu...

作者：Gtl
邮箱：wrmfwv@163.com
公司：Micronull Inc.
网址：https://minu.micronull.cn/

© 2026 Minu"""
        messagebox.showinfo(f"关于 {self.APP_NAME}", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = MinuEditor(root)
    root.mainloop()