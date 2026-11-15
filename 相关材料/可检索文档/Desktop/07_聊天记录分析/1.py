import os
import time
import random
import keyboard  # 第三方库，需要安装：`pip install keyboard`

# 游戏设置
WIDTH, HEIGHT = 20, 10  # 游戏区域宽和高

# 初始化蛇和食物
snake = [(5, 5)]  # 蛇的初始位置（由多个 (x, y) 坐标组成）
food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))  # 随机生成食物
direction = "RIGHT"  # 初始方向

def print_board():
    """打印游戏区域"""
    os.system("cls" if os.name == "nt" else "clear")  # 清屏
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x, y) in snake:  # 蛇的身体
                print("O", end="")
            elif (x, y) == food:  # 食物
                print("*", end="")
            else:
                print(" ", end="")
        print()  # 换行

def move_snake():
    """根据当前方向移动蛇"""
    global snake, food, direction

    # 获取蛇头位置
    head_x, head_y = snake[0]

    # 根据方向计算蛇头的新位置
    if direction == "UP":
        head_y -= 1
    elif direction == "DOWN":
        head_y += 1
    elif direction == "LEFT":
        head_x -= 1
    elif direction == "RIGHT":
        head_x += 1

    # 蛇头移动后的位置
    new_head = (head_x % WIDTH, head_y % HEIGHT)  # 支持从屏幕另一边穿越

    # 判断是否吃到自己
    if new_head in snake:
        print("Game Over! 你撞到自己了！")
        return False

    # 判断是否吃到食物
    if new_head == food:
        snake.insert(0, new_head)  # 增加蛇长度
        food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))  # 生成新食物
    else:
        snake.insert(0, new_head)  # 增加蛇头
        snake.pop()  # 移除蛇尾

    return True

def update_direction():
    """检测用户输入，更新蛇的方向"""
    global direction
    if keyboard.is_pressed("w") and direction != "DOWN":
        direction = "UP"
    elif keyboard.is_pressed("s") and direction != "UP":
        direction = "DOWN"
    elif keyboard.is_pressed("a") and direction != "RIGHT":
        direction = "LEFT"
    elif keyboard.is_pressed("d") and direction != "LEFT":
        direction = "RIGHT"

# 游戏主循环
try:
    while True:
        print_board()  # 打印游戏区域
        update_direction()  # 更新方向
        if not move_snake():  # 移动蛇，如果返回 False 则游戏结束
            break
        time.sleep(0.2)  # 控制游戏速度
except KeyboardInterrupt:
    print("\n游戏退出，感谢游玩！")
