import pygame
import random
import sys

# Инициализация Pygame и микшера для звуков
pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)

# Функция для генерации простых звуковых эффектов (процедурный звук)
def create_sound(frequency, duration, volume=0.3):
    sample_rate = 22050
    num_samples = int(sample_rate * (duration / 1000.0))
    buffer = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        # Простая синусоида с затуханием
        value = int(32767 * volume * pygame.math.math.sin(2 * pygame.math.math.pi * frequency * t) * (1 - i / num_samples))
        buffer.extend(value.to_bytes(2, byteorder='little', signed=True))
    return pygame.mixer.Sound(buffer=bytes(buffer))

# Создаем звуки прямо в коде
try:
    sound_move = create_sound(300, 50, 0.1)
    sound_rotate = create_sound(450, 70, 0.15)
    sound_drop = create_sound(150, 100, 0.2)
    sound_clear = create_sound(600, 200, 0.25)
    sound_gameover = create_sound(100, 500, 0.3)
except:
    sound_move = sound_rotate = sound_drop = sound_clear = sound_gameover = None

# Настройки экрана
BLOCK_SIZE = 25
COLUMNS = 10
ROWS = 20
GAME_WIDTH = COLUMNS * BLOCK_SIZE  # 250
PANEL_WIDTH = 160
WIDTH = GAME_WIDTH + PANEL_WIDTH   # 410
GAME_HEIGHT = ROWS * BLOCK_SIZE    # 500
CONTROL_PANEL_HEIGHT = 160         # Увеличили место для кнопок и инструкции
HEIGHT = GAME_HEIGHT + CONTROL_PANEL_HEIGHT

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🐍 Python Tetris Mobile")

# Цвета (RGB)
BLACK = (15, 15, 20)
GRAY = (40, 40, 50)
WHITE = (255, 255, 255)
PANEL_BG = (25, 25, 35)
BTN_BG = (60, 60, 80)
BTN_PRESS = (90, 90, 120)

COLORS = [
    (0, 240, 240),  # I - Голубой
    (240, 240, 0),  # O - Желтый
    (160, 0, 240),  # T - Фиолетовый
    (0, 240, 0),    # S - Зеленый
    (240, 0, 0),    # Z - Красный
    (0, 0, 240),    # J - Синий
    (240, 160, 0)   # L - Оранжевый
]

# Формы фигур (Тетромино)
SHAPES = [
    [[1, 1, 1, 1]],                    # I
    [[1, 1], [1, 1]],                  # O
    [[0, 1, 0], [1, 1, 1]],            # T
    [[0, 1, 1], [1, 1, 0]],            # S
    [[1, 1, 0], [0, 1, 1]],            # Z
    [[1, 0, 0], [1, 1, 1]],            # J
    [[0, 0, 1], [1, 1, 1]]             # L
]

class Tetris:
    def __init__(self):
        self.grid = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.next_shape_idx = random.randint(0, len(SHAPES) - 1)
        self.new_piece()

    def new_piece(self):
        self.shape_idx = self.next_shape_idx
        self.shape = [row[:] for row in SHAPES[self.shape_idx]]
        self.color = self.shape_idx + 1
        self.x = COLUMNS // 2 - len(self.shape[0]) // 2
        self.y = 0
        
        self.next_shape_idx = random.randint(0, len(SHAPES) - 1)
        
        if not self.check_collision(self.x, self.y, self.shape):
            self.game_over = True
            if sound_gameover: sound_gameover.play()

    def check_collision(self, offset_x, offset_y, shape):
        for r_idx, row in enumerate(shape):
            for c_idx, val in enumerate(row):
                if val:
                    new_x = offset_x + c_idx
                    new_y = offset_y + r_idx
                    if new_x < 0 or new_x >= COLUMNS or new_y >= ROWS:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def merge_piece(self):
        for r_idx, row in enumerate(self.shape):
            for c_idx, val in enumerate(row):
                if val:
                    self.grid[self.y + r_idx][self.x + c_idx] = self.color
        self.clear_lines()
        if not self.game_over:
            self.new_piece()

    def clear_lines(self):
        full_rows = [i for i, row in enumerate(self.grid) if all(row)]
        num_cleared = len(full_rows)
        if num_cleared > 0:
            for r in full_rows:
                del self.grid[r]
                self.grid.insert(0, [0] * COLUMNS)
            
            points = {1: 100, 2: 300, 3: 700, 4: 1500}
            self.score += points.get(num_cleared, 100 * num_cleared) * self.level
            self.lines_cleared += num_cleared
            self.level = 1 + self.lines_cleared // 10
            if sound_clear: sound_clear.play()

    def rotate_piece(self):
        rotated = [list(row) for row in zip(*self.shape[::-1])]
        if self.check_collision(self.x, self.y, rotated):
            self.shape = rotated
            if sound_rotate: sound_rotate.play()

    def move(self, dx, dy):
        if self.check_collision(self.x + dx, self.y + dy, self.shape):
            self.x += dx
            self.y += dy
            if dx != 0 and sound_move:
                sound_move.play()
            return True
        return False

    def hard_drop(self):
        # Мгновенное опускание до упора вниз
        dropped_rows = 0
        while self.check_collision(self.x, self.y + 1, self.shape):
            self.y += 1
            dropped_rows += 1
        if dropped_rows > 0 and sound_drop:
            sound_drop.play()
        self.merge_piece()

# Зоны сенсорных кнопок (x, y, w, h)
buttons = {
    "left": pygame.Rect(10, GAME_HEIGHT + 10, 70, 45),
    "rotate": pygame.Rect(85, GAME_HEIGHT + 10, 80, 45),
    "right": pygame.Rect(170, GAME_HEIGHT + 10, 70, 45),
    "pause": pygame.Rect(245, GAME_HEIGHT + 10, 75, 45),
    "drop": pygame.Rect(325, GAME_HEIGHT + 10, 75, 45),
    "restart": pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 30, 200, 50)
}

# Запуск игры
clock = pygame.time.Clock()
game = Tetris()
fall_time = 0

font_small = pygame.font.SysFont("arial", 14)
font_large = pygame.font.SysFont("arial", 20, bold=True)

running = True
while running:
    fall_speed = max(100, 500 - (game.level - 1) * 40)
    
    SCREEN.fill(BLACK)
    
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                game.paused = not game.paused
            if game.game_over:
                if event.key == pygame.K_r:
                    game = Tetris()
            elif not game.paused:
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1)
                elif event.key == pygame.K_UP:
                    game.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if game.game_over:
                if buttons["restart"].collidepoint(pos):
                    game = Tetris()
            else:
                if buttons["pause"].collidepoint(pos):
                    game.paused = not game.paused
                elif not game.paused:
                    if buttons["left"].collidepoint(pos):
                        game.move(-1, 0)
                    elif buttons["right"].collidepoint(pos):
                        game.move(1, 0)
                    elif buttons["rotate"].collidepoint(pos):
                        game.rotate_piece()
                    elif buttons["drop"].collidepoint(pos):
                        game.hard_drop()
                    elif buttons["down"].collidepoint(pos):
                        game.move(0, 1)

    # Автоматическое падение фигуры
    if not game.game_over and not game.paused:
        fall_time += clock.get_time()
        if fall_time > fall_speed:
            if not game.move(0, 1):
                game.merge_piece()
            fall_time = 0

    clock.tick(60)

    # Отрисовка стакана и сетки
    for r in range(ROWS):
        for c in range(COLUMNS):
            pygame.draw.rect(SCREEN, GRAY, (c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)
            if game.grid[r][c]:
                pygame.draw.rect(SCREEN, COLORS[game.grid[r][c] - 1], (c * BLOCK_SIZE + 1, r * BLOCK_SIZE + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))

    # Отрисовка падающей фигуры
    if not game.game_over:
        for r_idx, row in enumerate(game.shape):
            for c_idx, val in enumerate(row):
                if val:
                    pygame.draw.rect(SCREEN, COLORS[game.color - 1], ((game.x + c_idx) * BLOCK_SIZE + 1, (game.y + r_idx) * BLOCK_SIZE + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2))

    # Боковая панель (Счет, уровень, линии, след. фигура)
    pygame.draw.rect(SCREEN, PANEL_BG, (GAME_WIDTH, 0, PANEL_WIDTH, GAME_HEIGHT))
    pygame.draw.line(SCREEN, GRAY, (GAME_WIDTH, 0), (GAME_WIDTH, GAME_HEIGHT), 2)

    score_surf = font_small.render("СЧЕТ:", True, WHITE)
    score_val = font_large.render(str(game.score), True, (0, 255, 200))
    level_surf = font_small.render("УРОВЕНЬ:", True, WHITE)
    level_val = font_large.render(str(game.level), True, (255, 200, 0))
    lines_surf = font_small.render(f"ЛИНИИ: {game.lines_cleared}", True, WHITE)
    next_surf = font_small.render("ДАЛЕЕ:", True, WHITE)

    SCREEN.blit(score_surf, (GAME_WIDTH + 15, 15))
    SCREEN.blit(score_val, (GAME_WIDTH + 15, 35))
    SCREEN.blit(level_surf, (GAME_WIDTH + 15, 80))
    SCREEN.blit(level_val, (GAME_WIDTH + 15, 100))
    SCREEN.blit(lines_surf, (GAME_WIDTH + 15, 145))
    SCREEN.blit(next_surf, (GAME_WIDTH + 15, 185))

    next_shape = SHAPES[game.next_shape_idx]
    next_color = game.next_shape_idx + 1
    for r_idx, row in enumerate(next_shape):
        for c_idx, val in enumerate(row):
            if val:
                pygame.draw.rect(SCREEN, COLORS[next_color - 1], (GAME_WIDTH + 15 + c_idx * 18, 215 + r_idx * 18, 16, 16))

    # Нижняя панель управления
    pygame.draw.rect(SCREEN, PANEL_BG, (0, GAME_HEIGHT, WIDTH, CONTROL_PANEL_HEIGHT))
    pygame.draw.line(SCREEN, GRAY, (0, GAME_HEIGHT), (WIDTH, GAME_HEIGHT), 2)

    btn_labels = [
        ("left", "◄"),
        ("rotate", "↻ ПОВ."),
        ("right", "►"),
        ("pause", "⏸ ПАУЗА"),
        ("drop", "⬇ СБРОС")
    ]
    
    for key, text in btn_labels:
        rect = buttons[key]
        pygame.draw.rect(SCREEN, BTN_BG, rect, border_radius=6)
        pygame.draw.rect(SCREEN, GRAY, rect, 1, border_radius=6)
        txt_surf = font_small.render(text, True, WHITE)
        SCREEN.blit(txt_surf, (rect.x + (rect.width - txt_surf.get_width()) // 2, rect.y + (rect.height - txt_surf.get_height()) // 2))

    # Инструкция по управлению на экране
    instr_text1 = "Управление: Клик по кнопкам или Клавиатура"
    instr_text2 = "ПК: Стрелки - движ., Стрелка вверх - пов., Пробел - сброс, P - пауза"
    
    i_surf1 = font_small.render(instr_text1, True, (170, 170, 170))
    i_surf2 = font_small.render(instr_text2, True, (130, 130, 130))
    SCREEN.blit(i_surf1, (WIDTH // 2 - i_surf1.get_width() // 2, GAME_HEIGHT + 65))
    SCREEN.blit(i_surf2, (WIDTH // 2 - i_surf2.get_width() // 2, GAME_HEIGHT + 90))

    # Экран Паузы
    if game.paused and not game.game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        SCREEN.blit(overlay, (0, 0))
        p_text = font_large.render("ПАУЗА", True, WHITE)
        SCREEN.blit(p_text, (WIDTH // 2 - p_text.get_width() // 2, HEIGHT // 2 - 20))

    # Экран Game Over
    if game.game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        SCREEN.blit(overlay, (0, 0))

        go_text = font_large.render("GAME OVER", True, (255, 50, 50))
        SCREEN.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 40))

        rect = buttons["restart"]
        pygame.draw.rect(SCREEN, (180, 50, 50), rect, border_radius=8)
        pygame.draw.rect(SCREEN, WHITE, rect, 1, border_radius=8)
        restart_surf = font_small.render("ЗАНОВО", True, WHITE)
        SCREEN.blit(restart_surf, (rect.x + (rect.width - restart_surf.get_width()) // 2, rect.y + (rect.height - restart_surf.get_height()) // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()