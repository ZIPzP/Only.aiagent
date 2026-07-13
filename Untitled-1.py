# -*- coding: utf-8 -*-
"""
贪吃蛇游戏（优化版）
===================
思路：
1. 把游戏拆成几个清晰的步骤：初始化 → 事件处理 → 逻辑更新 → 画面绘制
2. 每个步骤写成一个函数，让主循环简洁易读
3. 用字典映射方向，避免大量 if-elif 判断
"""

import pygame
import random
import sys

# ==================== 初始化 ====================
pygame.init()  # 启动 pygame 所有模块（显示、事件、字体等）

# --- 常量定义：把不会变的值写成大写，方便修改和阅读 ---
WIDTH, HEIGHT = 600, 400          # 窗口宽高（像素）
CELL_SIZE = 20                     # 每个格子的边长
COLS = WIDTH // CELL_SIZE          # 列数 = 600/20 = 30
ROWS = HEIGHT // CELL_SIZE         # 行数 = 400/20 = 20

# 颜色（RGB 三元组）
WHITE = (255, 255, 255)            # 文字颜色
BLACK = (0, 0, 0)                  # 背景色
RED   = (255, 0, 0)                # 食物颜色
GREEN = (0, 255, 0)                # 蛇的颜色

# 方向：用坐标偏移量 (dx, dy) 表示，直觉就是「朝哪个方向走一格」
# 字典存储，键是方向名，值是 (x偏移, y偏移)
DIRECTIONS = {
    'UP':    (0, -CELL_SIZE),      # 向上：x不变，y减少一格
    'DOWN':  (0,  CELL_SIZE),      # 向下：x不变，y增加一格
    'LEFT':  (-CELL_SIZE, 0),      # 向左：x减少一格，y不变
    'RIGHT': ( CELL_SIZE, 0),      # 向右：x增加一格，y不变
}

# 禁止反向的规则：比如当前向右走，不能立刻按左
# 键=当前方向 → 值=禁止的方向
OPPOSITE = {
    'UP': 'DOWN',
    'DOWN': 'UP',
    'LEFT': 'RIGHT',
    'RIGHT': 'LEFT',
}

# 键盘按键 → 方向的映射（处理输入用）
KEY_TO_DIR = {
    pygame.K_UP:    'UP',
    pygame.K_DOWN:  'DOWN',
    pygame.K_LEFT:  'LEFT',
    pygame.K_RIGHT: 'RIGHT',
    pygame.K_w:     'UP',      # 支持 WASD（可选）
    pygame.K_s:     'DOWN',
    pygame.K_a:     'LEFT',
    pygame.K_d:     'RIGHT',
}

# --- 创建窗口 ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # 创建 600×400 的窗口
pygame.display.set_caption('贪吃蛇 - 优化版')       # 窗口标题
clock = pygame.time.Clock()                         # 时钟，控制帧率
font = pygame.font.Font(None, 24)                   # 提前创建字体（避免每帧重复创建）


# ==================== 工具函数 ====================

def random_food_position(snake_body):
    """
    生成一个「不在蛇身上」的食物坐标。
    思路：
      1. 生成随机格子坐标（对齐网格）
      2. 如果落在蛇身上 → 重新生成（while 循环）
      3. 返回坐标列表 [x, y]
    """
    while True:
        x = random.randint(0, COLS - 1) * CELL_SIZE   # 随机列 × 格子大小 = 像素坐标
        y = random.randint(0, ROWS - 1) * CELL_SIZE   # 随机行 × 格子大小 = 像素坐标
        if [x, y] not in snake_body:                  # 只有不在蛇身上才有效
            return [x, y]


def draw_snake(snake_body):
    """
    绘制整条蛇：遍历蛇身的每一节，画绿色矩形。
    思路：snake_body 是列表，如 [[100,50], [80,50], [60,50]]
         列表第一个元素是蛇头，后面的是身体
    """
    for segment in snake_body:
        # pygame.Rect(x, y, 宽, 高) 创建一个矩形对象
        rect = pygame.Rect(segment[0], segment[1], CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, GREEN, rect)  # 在屏幕上画绿色矩形


def draw_food(food_pos):
    """绘制食物：一个红色矩形"""
    rect = pygame.Rect(food_pos[0], food_pos[1], CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, RED, rect)


def show_text(text, pos, color=WHITE):
    """
    在屏幕上显示文字。
    参数：text=要显示的文字, pos=(x,y)坐标, color=颜色
    """
    surface = font.render(text, True, color)  # 把文字渲染成图片
    screen.blit(surface, pos)                 # 把图片贴到屏幕上


def show_game_over(score):
    """
    游戏结束画面。
    思路：
      1. 清屏，显示「游戏结束」和分数
      2. 提示按 R 重玩、按 Q 退出
      3. 循环等待玩家选择（这样窗口不会卡死）
    """
    screen.fill(BLACK)
    show_text("游戏结束!", (WIDTH // 2 - 60, HEIGHT // 2 - 40), RED)
    show_text(f"最终得分: {score}", (WIDTH // 2 - 70, HEIGHT // 2), WHITE)
    show_text("按 R 重新开始 / 按 Q 退出", (WIDTH // 2 - 120, HEIGHT // 2 + 40), WHITE)
    pygame.display.update()

    while True:  # 等待玩家按键
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False              # 点×关闭 → 退出
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True           # 按 R → 重新开始
                if event.key == pygame.K_q:
                    return False          # 按 Q → 退出


# ==================== 主游戏循环 ====================

def main():
    """
    游戏主函数。
    整体结构（游戏循环的标准写法）：
      初始化游戏状态
      while 游戏在运行:
          ├── ① 处理输入（事件）
          ├── ② 更新逻辑（蛇移动、碰撞检测）
          ├── ③ 绘制画面（渲染）
          └── ④ 控制帧率
    游戏结束后：显示结束画面 → 重玩或退出
    """
    # --- 初始状态 ---
    snake_pos  = [COLS // 2 * CELL_SIZE, ROWS // 2 * CELL_SIZE]  # 蛇头放屏幕中央
    snake_body = [
        snake_pos.copy(),                      # 蛇头（第0节）
        [snake_pos[0] - CELL_SIZE, snake_pos[1]],  # 第1节：向左偏移一格
        [snake_pos[0] - CELL_SIZE * 2, snake_pos[1]],  # 第2节：向左偏移两格
    ]
    direction  = 'RIGHT'                       # 当前移动方向
    food_pos   = random_food_position(snake_body)  # 安全生成食物
    score      = 0

    running = True
    while running:
        # ---- ① 处理输入 ----
        for event in pygame.event.get():       # 获取所有待处理事件
            if event.type == pygame.QUIT:      # 玩家点了窗口右上角的 ×
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:   # 玩家按下了键盘
                if event.key in KEY_TO_DIR:    # 是不是方向键？
                    new_dir = KEY_TO_DIR[event.key]
                    # 关键：不允许反向（比如向右时不能按左）
                    # 但也要防止同一帧内按两次导致的「间接反向」
                    if new_dir != OPPOSITE[direction]:
                        direction = new_dir   # 接受新方向

        # ---- ② 更新逻辑 ----
        # 根据方向计算蛇头新位置
        dx, dy = DIRECTIONS[direction]         # 取出偏移量，如 RIGHT → (20, 0)
        snake_pos[0] += dx                     # x 坐标偏移
        snake_pos[1] += dy                     # y 坐标偏移

        # 把新蛇头插入到蛇身列表的最前面
        snake_body.insert(0, snake_pos.copy())

        # 判断是否吃到食物
        if snake_pos == food_pos:              # 蛇头坐标 == 食物坐标
            score += 10                        # 加分
            food_pos = random_food_position(snake_body)  # 生成新食物（保证不在蛇身上）
            # 注意：吃到食物时不 pop，蛇身自然增长一节
        else:
            snake_body.pop()                   # 没吃到 → 去掉尾部，蛇保持原长度

        # 碰撞检测（撞墙 或 撞自己）
        head_x, head_y = snake_pos
        hit_wall = head_x < 0 or head_x >= WIDTH or head_y < 0 or head_y >= HEIGHT
        hit_self = snake_pos in snake_body[1:]  # 蛇头是否与身体重叠（排除蛇头自身）

        if hit_wall or hit_self:
            running = False                    # 退出主循环，进入结束画面

        # ---- ③ 绘制画面 ----
        screen.fill(BLACK)                     # 先清屏（全部涂黑）
        draw_snake(snake_body)                 # 画蛇
        draw_food(food_pos)                    # 画食物
        show_text(f"得分: {score}", (10, 10))  # 画分数（左上角）
        pygame.display.update()                # 把画好的内容刷新到屏幕上

        # ---- ④ 控制帧率 ----
        clock.tick(10)                         # 每秒10帧 → 蛇每0.1秒移动一次

    # 游戏结束：显示结束画面
    if show_game_over(score):                  # 玩家选了「重新开始」
        main()                                 # 递归调用自己，重新开始
    else:
        pygame.quit()                          # 玩家选了「退出」
        sys.exit()


# ==================== 入口 ====================
if __name__ == "__main__":
    """
    这个 if 判断的含义：
      - 如果直接运行这个文件 → __name__ 等于 "__main__" → 执行 main()
      - 如果被其他文件 import → __name__ 是文件名 → 不自动执行
      这是一种 Python 约定，让代码既可以运行，也可以被导入复用。
    """
    main()
