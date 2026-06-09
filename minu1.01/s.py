import tkinter as tk
import random

# 游戏设置
CELL_SIZE = 20      # 每个格子20像素
COLS = 30           # 30列
ROWS = 20           # 20行
WIDTH = COLS * CELL_SIZE    # 600
HEIGHT = ROWS * CELL_SIZE   # 400

# 颜色
DARK_GREEN = "#1a5f1a"
LIGHT_GREEN = "#2d7a2d"
SNAKE_HEAD = "#3cba54"
SNAKE_BODY = "#4cae4c"
FOOD_COLOR = "#ff5252"

class SnakeGame:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🐍 贪吃蛇游戏")
        self.window.resizable(False, False)
        
        # 分数显示
        self.score_label = tk.Label(self.window, text="分数: 0", font=("微软雅黑", 14, "bold"), fg=DARK_GREEN)
        self.score_label.pack(pady=5)
        
        # 画布
        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT, bg=LIGHT_GREEN, highlightthickness=0)
        self.canvas.pack()
        
        # 游戏状态
        self.snake = [(COLS//2, ROWS//2)]  # 蛇身坐标列表
        self.direction = "Right"           # 当前方向
        self.next_direction = "Right"      # 下一个方向（防止一帧内多次转向）
        self.food = self.generate_food()
        self.score = 0
        self.game_over_flag = False
        self.speed = 150  # 毫秒
        
        # 绑定键盘事件
        self.window.bind("<Key>", self.on_key_press)
        
        # 绘制网格线
        self.draw_grid()
        
        # 开始游戏循环
        self.update()
        
        # 让窗口居中
        self.center_window()
        
        self.window.mainloop()
    
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - WIDTH) // 2
        y = (self.window.winfo_screenheight() - HEIGHT - 50) // 2
        self.window.geometry(f"{WIDTH}x{HEIGHT+40}+{x}+{y}")
    
    def draw_grid(self):
        """绘制浅色网格线"""
        for i in range(COLS):
            self.canvas.create_line(i*CELL_SIZE, 0, i*CELL_SIZE, HEIGHT, fill="#4a9e4a", width=1)
        for i in range(ROWS):
            self.canvas.create_line(0, i*CELL_SIZE, WIDTH, i*CELL_SIZE, fill="#4a9e4a", width=1)
    
    def generate_food(self):
        """随机生成食物，避开蛇身"""
        while True:
            x = random.randint(0, COLS-1)
            y = random.randint(0, ROWS-1)
            if (x, y) not in self.snake:
                return (x, y)
    
    def on_key_press(self, event):
        """处理键盘方向键"""
        key = event.keysym
        # 防止蛇直接反向
        if key == "Up" and self.direction != "Down":
            self.next_direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.next_direction = "Down"
        elif key == "Left" and self.direction != "Right":
            self.next_direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.next_direction = "Right"
        elif key == "r" or key == "R":
            self.restart()
        elif key == "space" and self.game_over_flag:
            self.restart()
    
    def move_snake(self):
        """移动蛇"""
        head = self.snake[0]
        new_head = head
        
        if self.direction == "Up":
            new_head = (head[0], head[1]-1)
        elif self.direction == "Down":
            new_head = (head[0], head[1]+1)
        elif self.direction == "Left":
            new_head = (head[0]-1, head[1])
        elif self.direction == "Right":
            new_head = (head[0]+1, head[1])
        
        # 检查是否吃到食物
        if new_head == self.food:
            # 吃到食物：蛇头插入，尾巴不动（长度+1）
            self.snake.insert(0, new_head)
            self.food = self.generate_food()
            self.score += 10
            self.score_label.config(text=f"分数: {self.score}")
            # 每得50分加速一次
            if self.score % 50 == 0 and self.speed > 50:
                self.speed -= 10
            return True
        else:
            # 没吃到：蛇头插入，尾巴弹出
            self.snake.insert(0, new_head)
            self.snake.pop()
            return False
    
    def check_collision(self):
        """检查是否撞墙或撞自己"""
        head = self.snake[0]
        # 撞墙
        if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS:
            return True
        # 撞自己（检查蛇头是否和身体其他部分重叠）
        if head in self.snake[1:]:
            return True
        return False
    
    def draw(self):
        """绘制所有元素"""
        self.canvas.delete("all")
        self.draw_grid()
        
        # 绘制食物
        fx, fy = self.food
        x1 = fx * CELL_SIZE
        y1 = fy * CELL_SIZE
        self.canvas.create_oval(x1+2, y1+2, x1+CELL_SIZE-2, y1+CELL_SIZE-2, fill=FOOD_COLOR, outline="")
        
        # 绘制蛇
        for i, (sx, sy) in enumerate(self.snake):
            x1 = sx * CELL_SIZE
            y1 = sy * CELL_SIZE
            if i == 0:
                color = SNAKE_HEAD
            else:
                color = SNAKE_BODY
            self.canvas.create_rectangle(x1, y1, x1+CELL_SIZE, y1+CELL_SIZE, fill=color, outline=DARK_GREEN, width=1)
        
        # 绘制眼睛（蛇头）
        head_x, head_y = self.snake[0]
        hx = head_x * CELL_SIZE
        hy = head_y * CELL_SIZE
        eye_size = 4
        if self.direction == "Right":
            self.canvas.create_oval(hx+CELL_SIZE-6, hy+5, hx+CELL_SIZE-2, hy+9, fill="white")
            self.canvas.create_oval(hx+CELL_SIZE-6, hy+CELL_SIZE-9, hx+CELL_SIZE-2, hy+CELL_SIZE-5, fill="white")
            self.canvas.create_oval(hx+CELL_SIZE-5, hy+6, hx+CELL_SIZE-3, hy+8, fill="black")
            self.canvas.create_oval(hx+CELL_SIZE-5, hy+CELL_SIZE-8, hx+CELL_SIZE-3, hy+CELL_SIZE-6, fill="black")
        elif self.direction == "Left":
            self.canvas.create_oval(hx+2, hy+5, hx+6, hy+9, fill="white")
            self.canvas.create_oval(hx+2, hy+CELL_SIZE-9, hx+6, hy+CELL_SIZE-5, fill="white")
            self.canvas.create_oval(hx+3, hy+6, hx+5, hy+8, fill="black")
            self.canvas.create_oval(hx+3, hy+CELL_SIZE-8, hx+5, hy+CELL_SIZE-6, fill="black")
        elif self.direction == "Up":
            self.canvas.create_oval(hx+5, hy+2, hx+9, hy+6, fill="white")
            self.canvas.create_oval(hx+CELL_SIZE-9, hy+2, hx+CELL_SIZE-5, hy+6, fill="white")
            self.canvas.create_oval(hx+6, hy+3, hx+8, hy+5, fill="black")
            self.canvas.create_oval(hx+CELL_SIZE-8, hy+3, hx+CELL_SIZE-6, hy+5, fill="black")
        elif self.direction == "Down":
            self.canvas.create_oval(hx+5, hy+CELL_SIZE-6, hx+9, hy+CELL_SIZE-2, fill="white")
            self.canvas.create_oval(hx+CELL_SIZE-9, hy+CELL_SIZE-6, hx+CELL_SIZE-5, hy+CELL_SIZE-2, fill="white")
            self.canvas.create_oval(hx+6, hy+CELL_SIZE-5, hx+8, hy+CELL_SIZE-3, fill="black")
            self.canvas.create_oval(hx+CELL_SIZE-8, hy+CELL_SIZE-5, hx+CELL_SIZE-6, hy+CELL_SIZE-3, fill="black")
    
    def show_game_over(self):
        """显示游戏结束画面"""
        self.canvas.create_rectangle(WIDTH//2-100, HEIGHT//2-40, WIDTH//2+100, HEIGHT//2+40, fill="white", outline="black", width=2)
        self.canvas.create_text(WIDTH//2, HEIGHT//2-10, text="游戏结束", font=("微软雅黑", 18, "bold"), fill="red")
        self.canvas.create_text(WIDTH//2, HEIGHT//2+20, text=f"最终得分: {self.score}", font=("微软雅黑", 12), fill=DARK_GREEN)
        self.canvas.create_text(WIDTH//2, HEIGHT//2+55, text="按 R 键或空格重新开始", font=("微软雅黑", 10), fill="gray")
    
    def update(self):
        """游戏主循环"""
        if not self.game_over_flag:
            # 更新方向
            self.direction = self.next_direction
            # 移动蛇
            self.move_snake()
            # 检查碰撞
            if self.check_collision():
                self.game_over_flag = True
                self.show_game_over()
            else:
                self.draw()
        
        # 继续循环
        self.window.after(self.speed, self.update)
    
    def restart(self):
        """重新开始游戏"""
        self.snake = [(COLS//2, ROWS//2)]
        self.direction = "Right"
        self.next_direction = "Right"
        self.food = self.generate_food()
        self.score = 0
        self.speed = 150
        self.game_over_flag = False
        self.score_label.config(text="分数: 0")
        self.draw()

if __name__ == "__main__":
    game = SnakeGame()