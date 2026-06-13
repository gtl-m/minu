#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minu Editor v1.5
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

class CSyntaxHighlighter:
    """C语言语法高亮引擎"""
    
    # C语言关键字
    KEYWORDS = {
        'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double',
        'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long', 'register',
        'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef',
        'union', 'unsigned', 'void', 'volatile', 'while', 'inline', 'restrict', '_Bool',
        '_Complex', '_Imaginary', '_Alignas', '_Alignof', '_Atomic', '_Generic', '_Noreturn',
        '_Static_assert', '_Thread_local'
    }
    
    # 预处理指令
    PREPROCESSOR = {
        '#include', '#define', '#undef', '#if', '#ifdef', '#ifndef', '#else', '#elif',
        '#endif', '#error', '#pragma', '#line'
    }
    
    # 标准库函数
    LIBRARY_FUNCS = {
        'printf', 'scanf', 'fprintf', 'fscanf', 'sprintf', 'sscanf', 'getchar', 'putchar',
        'gets', 'puts', 'fgets', 'fputs', 'malloc', 'calloc', 'realloc', 'free', 'memcpy',
        'memmove', 'memset', 'memcmp', 'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp',
        'strncmp', 'strlen', 'strstr', 'strchr', 'strrchr', 'atoi', 'atol', 'atof', 'rand',
        'srand', 'exit', 'abort', 'assert', 'system', 'qsort', 'bsearch', 'abs', 'fabs'
    }
    
    def __init__(self, text_widget):
        self.text = text_widget
        self.tag_configs = {
            'keyword': '#FF7700',      # 关键字 - 橙色
            'preprocessor': '#800080', # 预处理 - 紫色
            'string': '#00AA00',       # 字符串 - 绿色
            'comment': '#888888',      # 注释 - 灰色
            'number': '#FF00FF',       # 数字 - 品红
            'function': '#00AAAA',     # 函数 - 青色
            'library': '#0088FF',      # 库函数 - 蓝色
            'operator': '#000000',     # 运算符 - 黑色
        }
        
        for tag, color in self.tag_configs.items():
            self.text.tag_config(tag, foreground=color)
        
        self.text.tag_config('comment', foreground='#888888', font=('Courier', 10, 'italic'))
        self.text.tag_config('string', foreground='#00AA00', font=('Courier', 10, 'bold'))
        self.text.tag_config('keyword', foreground='#FF7700', font=('Courier', 10, 'bold'))
        self.text.tag_config('function', foreground='#00AAAA', font=('Courier', 10, 'bold'))
        self.text.tag_config('preprocessor', foreground='#800080', font=('Courier', 10, 'bold'))
        
    def highlight(self):
        """高亮整个文档"""
        for tag in self.tag_configs:
            self.text.tag_remove(tag, "1.0", tk.END)
        
        content = self.text.get("1.0", tk.END)
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            self.highlight_line(line, line_num)
            
    def highlight_line(self, line, line_num):
        if not line.strip():
            return
        
        # 处理字符串
        string_regions = self.find_string_regions(line)
        
        # 处理单行注释
        comment_pos = self.find_comment(line)
        
        # 高亮预处理指令
        self.highlight_preprocessor(line, line_num, comment_pos)
        
        # 高亮字符串
        for start, end in string_regions:
            if start < len(line):
                self.text.tag_add('string', f"{line_num}.{start}", f"{line_num}.{min(end, len(line))}")
        
        # 处理行内内容（跳过注释部分）
        code_line = line
        if comment_pos is not None:
            self.text.tag_add('comment', f"{line_num}.{comment_pos}", f"{line_num}.{len(line)}")
            code_line = line[:comment_pos]
        
        # 高亮其他语法元素
        self.highlight_keywords(code_line, line_num, string_regions)
        self.highlight_numbers(code_line, line_num, string_regions)
        self.highlight_functions(code_line, line_num, string_regions)
        self.highlight_library_funcs(code_line, line_num, string_regions)
        self.highlight_operators(code_line, line_num, string_regions)
        
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
                
        if in_string:
            regions.append((start, len(line)))
        return regions
        
    def find_comment(self, line):
        """查找单行注释位置"""
        for i, char in enumerate(line):
            if char == '/' and i + 1 < len(line) and line[i + 1] == '/':
                return i
        return None
        
    def highlight_preprocessor(self, line, line_num, comment_pos):
        """高亮预处理指令"""
        if line.strip().startswith('#'):
            for pp in self.PREPROCESSOR:
                if line.strip().startswith(pp):
                    start = line.find(pp)
                    end = start + len(pp)
                    if comment_pos is None or end <= comment_pos:
                        self.text.tag_add('preprocessor', f"{line_num}.{start}", f"{line_num}.{end}")
                    break
                    
    def highlight_keywords(self, line, line_num, string_regions):
        """高亮关键字"""
        def is_valid(start, end):
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        for keyword in self.KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', line):
                s, e = match.span()
                if is_valid(s, e):
                    self.text.tag_add('keyword', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_numbers(self, line, line_num, string_regions):
        """高亮数字"""
        def is_valid(start, end):
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        patterns = [
            r'\b0x[0-9a-fA-F]+\b',  # 十六进制
            r'\b0[0-7]+\b',          # 八进制
            r'\b\d+\.\d+\b',         # 浮点数
            r'\b\d+\b',              # 整数
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                s, e = match.span()
                if is_valid(s, e):
                    self.text.tag_add('number', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_functions(self, line, line_num, string_regions):
        """高亮函数调用"""
        def is_valid(start, end):
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        # 匹配函数名后跟括号
        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line):
            s, e = match.span(1)
            if is_valid(s, e):
                func_name = line[s:e]
                # 如果不是关键字或库函数
                if func_name not in self.KEYWORDS and func_name not in self.LIBRARY_FUNCS:
                    self.text.tag_add('function', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_library_funcs(self, line, line_num, string_regions):
        """高亮库函数"""
        def is_valid(start, end):
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        for func in self.LIBRARY_FUNCS:
            for match in re.finditer(r'\b' + re.escape(func) + r'\s*\(', line):
                s, e = match.span(1)
                if is_valid(s, e):
                    self.text.tag_add('library', f"{line_num}.{s}", f"{line_num}.{e}")
                    
    def highlight_operators(self, line, line_num, string_regions):
        """高亮运算符"""
        def is_valid(start, end):
            for s, e in string_regions:
                if (s <= start < e) or (s < end <= e):
                    return False
            return True
            
        operators = ['+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
                    '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '+=', '-=', '*=',
                    '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '++', '--', '->', '.']
        
        escaped_ops = [re.escape(op) for op in operators]
        pattern = '|'.join(escaped_ops)
        for match in re.finditer(pattern, line):
            s, e = match.span()
            if is_valid(s, e):
                self.text.tag_add('operator', f"{line_num}.{s}", f"{line_num}.{e}")


class PythonSyntaxHighlighter:
    """Python语法高亮引擎"""
    
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
        
    def highlight(self):
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


class Tab:
    """单个标签页"""
    def __init__(self, notebook, title="未命名", filepath=None, content=""):
        self.notebook = notebook
        self.filepath = filepath
        self.modified = False
        self.title = title
        
        # 判断语言类型
        self.language = self.get_language(filepath)
        
        # 创建框架
        self.frame = tk.Frame(notebook)
        
        # 行号区域
        self.line_numbers = tk.Text(self.frame, width=5, padx=3, takefocus=0, 
                                   border=0, background='#f0f0f0', state='disabled',
                                   wrap='none', font=('Courier', 12))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 文本编辑区域
        self.text = tk.Text(self.frame, font=('Courier', 12), wrap=tk.WORD,
                           undo=True, tabs=('4c'), background='white',
                           foreground='black', selectbackground='#3399FF')
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.frame, command=self.on_scroll)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)
        self.line_numbers.config(yscrollcommand=scrollbar.set)
        
        # 根据语言选择高亮器
        if self.language == 'c':
            self.highlighter = CSyntaxHighlighter(self.text)
        else:
            self.highlighter = PythonSyntaxHighlighter(self.text)
        
        # 绑定事件
        self.text.bind('<KeyRelease>', self.on_text_change)
        self.text.bind('<ButtonRelease-1>', self.update_line_numbers)
        
        # 设置内容
        if content:
            self.text.insert(1.0, content)
        
        self.update_line_numbers()
        self.highlight()
        
    def get_language(self, filepath):
        """根据文件扩展名判断语言"""
        if filepath:
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.c', '.h']:
                return 'c'
        return 'python'
        
    def on_scroll(self, *args):
        """同步滚动"""
        self.text.yview(*args)
        self.line_numbers.yview(*args)
        
    def on_text_change(self, event=None):
        self.modified = True
        self.update_title()
        self.update_line_numbers()
        self.highlight()
        
    def highlight(self):
        """高亮当前文本"""
        self.highlighter.highlight()
        
    def update_title(self):
        """更新标签页标题"""
        title = os.path.basename(self.filepath) if self.filepath else "未命名"
        if self.modified:
            title += " *"
        # 添加语言标识
        if self.language == 'c':
            title = f"[C] {title}"
        else:
            title = f"[Py] {title}"
        self.notebook.tab(self.frame, text=title)
        
    def update_line_numbers(self, event=None):
        """更新行号"""
        line_count = int(self.text.index('end-1c').split('.')[0])
        line_numbers_str = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        self.line_numbers.insert(1.0, line_numbers_str)
        self.line_numbers.config(state='disabled')
        
    def get_content(self):
        return self.text.get(1.0, tk.END)
    
    def set_content(self, content):
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, content)
        self.modified = False
        self.update_title()
        self.highlight()
        
    def save(self):
        if self.filepath:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_content())
            self.modified = False
            self.update_title()
            return True
        return False
    
    def save_as(self, filepath):
        self.filepath = filepath
        self.language = self.get_language(filepath)
        # 重新创建高亮器
        if self.language == 'c':
            self.highlighter = CSyntaxHighlighter(self.text)
        else:
            self.highlighter = PythonSyntaxHighlighter(self.text)
        return self.save()


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
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.history[-(self.history_index + 1)])
        return "break"
        
    def next_command(self, event=None):
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.command_entry.delete(0, tk.END)
        return "break"
        
    def execute_command(self, event=None):
        cmd = self.command_entry.get().strip()
        if not cmd:
            return
            
        self.output_text.insert(tk.END, f"\n{self.current_dir}> {cmd}\n", 'prompt')
        self.command_entry.delete(0, tk.END)
        self.output_text.see(tk.END)
        
        self.history.append(cmd)
        self.history_index = -1
        
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
        elif cmd.lower().startswith('gcc '):
            self.run_system_command(cmd)
            return
        elif cmd.lower().startswith('./') or cmd.lower().endswith('.exe'):
            self.run_system_command(cmd)
            return
        elif cmd.lower().startswith('python '):
            script = cmd[7:].strip()
            self.run_python_script(script)
            return
        elif cmd.lower().startswith('pip '):
            self.run_system_command(cmd)
            return
            
        self.run_system_command(cmd)
        
    def run_python_script(self, script):
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
    
    VERSION = "1.5"
    APP_NAME = "Minu"
    
    def __init__(self, root, open_file=None):
        self.root = root
        self.root.title(f"{self.APP_NAME} {self.VERSION} - Python/C 编辑器")
        
        self.is_fullscreen = True
        self.root.attributes('-fullscreen', True)
        
        self.tabs = []
        self.current_tab = None
        
        self.setup_ui()
        self.setup_menu()
        
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen())
        self.root.bind('<Control-t>', lambda e: self.new_tab())
        self.root.bind('<Control-w>', lambda e: self.close_current_tab())
        self.root.bind('<Control-Tab>', lambda e: self.next_tab())
        self.root.bind('<Control-Shift-Tab>', lambda e: self.prev_tab())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-n>', lambda e: self.new_file())
        
        self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 已就绪 | 支持 Python/C 语法高亮 | Ctrl+T:新建标签", fg='green')
        
        if open_file and os.path.exists(open_file):
            self.open_file_in_new_tab(open_file)
        else:
            self.new_tab()
        
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        
    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.toggle_fullscreen()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        toolbar = tk.Frame(main_frame, bg='#E0E0E0', height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        buttons = [
            ("📁 新建", self.new_file), ("📂 打开", self.open_file), 
            ("💾 保存", self.save_file), ("➕ 新标签", self.new_tab),
            ("❌ 关闭标签", self.close_current_tab), ("▶ 运行(F5)", self.run_current_code),
            ("🗑 清空终端", self.clear_terminal), ("🎨 高亮", self.force_highlight), 
            ("🖥 窗口模式", self.toggle_fullscreen)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(toolbar, text=text, command=cmd, 
                          bg='white', relief=tk.RAISED, padx=10)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        tk.Frame(toolbar, width=2, bg='gray', relief=tk.RAISED).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        tk.Label(toolbar, text="字体:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.StringVar(value="12")
        font_spin = tk.Spinbox(toolbar, from_=8, to=30, width=3, 
                               textvariable=self.font_size_var, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=2)
        
        tk.Label(toolbar, text="主题:", bg='#E0E0E0').pack(side=tk.LEFT, padx=(10,2))
        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(toolbar, textvariable=self.theme_var, 
                                  values=['default', 'dark', 'light'], width=8)
        theme_combo.pack(side=tk.LEFT, padx=2)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        self.status_label = tk.Label(toolbar, text="就绪", bg='#E0E0E0', fg='green')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        self.cursor_label = tk.Label(toolbar, text="行:1 列:1", bg='#E0E0E0')
        self.cursor_label.pack(side=tk.RIGHT, padx=10)
        
        version_label = tk.Label(toolbar, text=f"v{self.VERSION}", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        version_label.pack(side=tk.RIGHT, padx=5)
        fullscreen_label = tk.Label(toolbar, text="ESC/F11:全屏", bg='#E0E0E0', fg='gray', font=('Arial', 8))
        fullscreen_label.pack(side=tk.RIGHT, padx=5)
        
        # 创建分割窗口
        paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 标签页区域框架
        tab_frame = tk.Frame(paned)
        paned.add(tab_frame, height=350)
        
        # 标签页控件
        self.notebook = ttk.Notebook(tab_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # 终端区域
        self.terminal = Terminal(main_frame)
        
    def on_tab_changed(self, event):
        if self.notebook.select():
            for tab in self.tabs:
                if tab.frame == self.notebook.select():
                    self.current_tab = tab
                    self.update_cursor_position()
                    break
    
    def new_tab(self, content="", title="未命名", filepath=None):
        tab = Tab(self.notebook, title, filepath, content)
        self.notebook.add(tab.frame, text=f"[Py] {title}")
        self.tabs.append(tab)
        self.notebook.select(tab.frame)
        self.current_tab = tab
        self.status_label.config(text=f"新建标签: {title}", fg='blue')
        return tab
    
    def close_current_tab(self):
        if len(self.tabs) <= 1:
            if messagebox.askyesno("确认", "这是最后一个标签页，关闭后编辑器将为空。确定吗？"):
                self.new_tab()
        if self.current_tab and self.current_tab.modified:
            result = messagebox.askyesnocancel("保存", f"文件 {self.current_tab.title} 已修改，是否保存？")
            if result is None:
                return
            if result:
                self.save_file()
        if self.current_tab:
            self.notebook.forget(self.current_tab.frame)
            self.tabs.remove(self.current_tab)
            if self.tabs:
                self.current_tab = self.tabs[0]
                self.notebook.select(self.current_tab.frame)
            else:
                self.current_tab = None
            self.status_label.config(text="标签已关闭", fg='blue')
    
    def next_tab(self):
        if self.tabs and self.current_tab:
            idx = self.tabs.index(self.current_tab)
            next_idx = (idx + 1) % len(self.tabs)
            self.notebook.select(self.tabs[next_idx].frame)
            self.current_tab = self.tabs[next_idx]
    
    def prev_tab(self):
        if self.tabs and self.current_tab:
            idx = self.tabs.index(self.current_tab)
            prev_idx = (idx - 1) % len(self.tabs)
            self.notebook.select(self.tabs[prev_idx].frame)
            self.current_tab = self.tabs[prev_idx]
    
    def open_file_in_new_tab(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            title = os.path.basename(filepath)
            tab = self.new_tab(content, title, filepath)
            # 更新标签标题（会显示语言标识）
            tab.update_title()
            self.status_label.config(text=f"已打开: {filepath}", fg='green')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")
    
    def get_current_text(self):
        if self.current_tab:
            return self.current_tab.get_content()
        return ""
    
    def run_current_code(self):
        if not self.current_tab:
            return
        if self.current_tab.filepath:
            self.current_tab.save()
            filepath = self.current_tab.filepath
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.c', '.h']:
                # C 语言：先编译再运行
                exe_path = os.path.splitext(filepath)[0] + '.exe'
                compile_cmd = f'gcc "{filepath}" -o "{exe_path}"'
                self.terminal.output_text.insert(tk.END, f"\n编译: {compile_cmd}\n", 'prompt')
                self.terminal.run_system_command(compile_cmd)
                # 运行编译后的程序
                self.terminal.run_system_command(f'"{exe_path}"')
            else:
                self.terminal.run_python_script(filepath)
        else:
            import tempfile
            content = self.current_tab.get_content()
            # 检测是否为 C 代码
            if '#include' in content and ('int main' in content or 'void main' in content):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.c', 
                                                delete=False, encoding='utf-8') as f:
                    f.write(content)
                    filename = f.name
                exe_path = os.path.splitext(filename)[0] + '.exe'
                compile_cmd = f'gcc "{filename}" -o "{exe_path}"'
                self.terminal.output_text.insert(tk.END, f"\n编译: {compile_cmd}\n", 'prompt')
                self.terminal.run_system_command(compile_cmd)
                self.terminal.run_system_command(f'"{exe_path}"')
            else:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                                delete=False, encoding='utf-8') as f:
                    f.write(content)
                    filename = f.name
                self.terminal.run_python_script(filename)
    
    def clear_terminal(self):
        self.terminal.output_text.delete(1.0, tk.END)
    
    def force_highlight(self):
        if self.current_tab:
            self.current_tab.highlight()
            self.status_label.config(text="语法高亮完成", fg='blue')
        self.root.after(2000, lambda: self.status_label.config(text=f"{self.APP_NAME} {self.VERSION} 就绪", fg='green'))
    
    def update_cursor_position(self, event=None):
        if self.current_tab:
            cursor_pos = self.current_tab.text.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.cursor_label.config(text=f"行:{line} 列:{int(col)+1}")
    
    def change_font(self):
        size = int(self.font_size_var.get())
        for tab in self.tabs:
            tab.text.config(font=('Courier', size))
            tab.line_numbers.config(font=('Courier', size))
    
    def change_theme(self, event=None):
        theme = self.theme_var.get()
        for tab in self.tabs:
            if theme == 'dark':
                tab.text.config(bg='#2E2E2E', fg='#FFFFFF', insertbackground='white')
                tab.line_numbers.config(bg='#1E1E1E', fg='#808080')
            elif theme == 'light':
                tab.text.config(bg='#FFFFFF', fg='#000000', insertbackground='black')
                tab.line_numbers.config(bg='#F0F0F0', fg='#000000')
            else:
                tab.text.config(bg='white', fg='black', insertbackground='black')
                tab.line_numbers.config(bg='#f0f0f0', fg='#000000')
            tab.highlight()
    
    def new_file(self):
        self.new_tab()
    
    def open_file(self):
        if self.current_tab and self.current_tab.modified:
            result = messagebox.askyesnocancel("保存", f"当前文件已修改，是否保存？")
            if result is None:
                return
            if result:
                self.save_file()
        
        file = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("C文件", "*.c"), ("头文件", "*.h"), 
                      ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file:
            self.open_file_in_new_tab(file)
    
    def save_file(self):
        if self.current_tab:
            if self.current_tab.filepath:
                self.current_tab.save()
                self.status_label.config(text=f"已保存: {self.current_tab.filepath}", fg='green')
            else:
                self.save_as_file()
    
    def save_as_file(self):
        if self.current_tab:
            file = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python文件", "*.py"), ("C文件", "*.c"), ("头文件", "*.h"), 
                          ("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile="untitled.py"
            )
            if file:
                self.current_tab.save_as(file)
                self.current_tab.update_title()
                self.status_label.config(text=f"已保存: {file}", fg='green')
    
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
        
        tab_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="标签", menu=tab_menu)
        tab_menu.add_command(label="新建标签", accelerator="Ctrl+T", command=self.new_tab)
        tab_menu.add_command(label="关闭标签", accelerator="Ctrl+W", command=self.close_current_tab)
        tab_menu.add_command(label="下一个标签", accelerator="Ctrl+Tab", command=self.next_tab)
        tab_menu.add_command(label="上一个标签", accelerator="Ctrl+Shift+Tab", command=self.prev_tab)
        
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
    parser = argparse.ArgumentParser(
        prog='minu',
        description='Minu Editor - 轻量级代码编辑器，支持 Python/C',
        epilog='示例: python minu.py test.c'
    )
    parser.add_argument('file', nargs='?', help='要打开的文件路径')
    parser.add_argument('--version', '-v', action='version', version=f'Minu Editor v{MinuEditor.VERSION}')
    
    args = parser.parse_args()
    
    root = tk.Tk()
    open_file = args.file if args.file else None
    app = MinuEditor(root, open_file)
    root.mainloop()


if __name__ == "__main__":
    main()