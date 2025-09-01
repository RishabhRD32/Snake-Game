import pygame
import random
import sys
import os
import math
import wave
import struct
from typing import List, Tuple
from math import degrees, atan2  # Added degrees import

# Constants
ASSETS_DIR = "assets"
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# AudioManager class
class AudioManager:
    """
    Generates tiny WAV tones at runtime so audio always works without internet.
    """
    def __init__(self):
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception:
            pass

        self._init_ok = False
        self.sounds = {"eat": None, "power": None, "over": None}

    def init(self):
        try:
            if not pygame.get_init():
                pygame.init()
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._init_ok = True
        except Exception as e:
            print(f"[Audio] Mixer unavailable: {e}")
            self._init_ok = False

        self._prepare_sounds()

    def _prepare_sounds(self):
        tones = {
            "eat": [(880, 0.08)],
            "power": [(660, 0.08), (990, 0.08)],
            "over": [(330, 0.25), (247, 0.25), (196, 0.25)]
        }
        for key, seq in tones.items():
            path = os.path.join(ASSETS_DIR, f"{key}.wav")
            self._synthesize_sequence(path, seq)
            if self._init_ok:
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"[Audio] Load failed for {key}: {e}")
                    self.sounds[key] = None

    @staticmethod
    def _synthesize_sequence(path: str, sequence: List[Tuple[float, float]], volume: float = 0.35):
        fr = 44100
        amp = int(32767 * volume)
        samples = []

        for freq, dur in sequence:
            n = int(fr * dur)
            for i in range(n):
                t = i / fr
                s = int(amp * math.sin(2 * math.pi * freq * t))
                samples.append(s)

        stereo = []
        for s in samples:
            stereo.append(s)
            stereo.append(s)

        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(fr)
            wf.writeframes(b"".join(struct.pack("<h", v) for v in stereo))

    def play(self, key: str):
        snd = self.sounds.get(key)
        if self._init_ok and snd is not None:
            try:
                snd.play()
            except Exception as e:
                print(f"[Audio] Play failed for {key}: {e}")

# Initialize Pygame and Audio
audio_manager = AudioManager()
audio_manager.init()

# Set up display
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BORDER_COLOR = (255, 165, 0)
GRAY = (100, 100, 100)

# Fonts
FONT = pygame.font.SysFont("comicsansms", 35)
SMALL_FONT = pygame.font.SysFont("comicsansms", 20)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
PAUSED = 3
NEW_GAME = 4
COLOR_SELECT = 5
MODE_SELECT = 6

# Power-up types
GHOST = 0
SPEED = 1
SCORE_MULTIPLIER = 2

class Snake:
    def __init__(self, start_pos, color, controls="user"):
        self.body = [start_pos]
        self.direction = RIGHT
        self.color = color
        self.score = 0
        self.controls = controls
        self.power_up = None
        self.power_up_timer = 0

    def move(self, direction, food, obstacles, other_snake, game):
        try:
            self.direction = direction
            head = self.body[0]
            new_head = (head[0] + direction[0], head[1] + direction[1])

            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or
                new_head in obstacles or
                (other_snake and new_head in other_snake.body and self.power_up != GHOST and (other_snake.power_up != GHOST if other_snake else True))):
                audio_manager.play("over")
                return True

            if self.power_up != GHOST and new_head in self.body[1:]:
                audio_manager.play("over")
                return True

            self.body.insert(0, new_head)

            multiplier = 2 if self.power_up == SCORE_MULTIPLIER else 1
            if new_head == food:
                self.score += 10 * game.level * multiplier
                audio_manager.play("eat")
                return False
            else:
                self.body.pop()

            if game.power_up and new_head == game.power_up:
                self.power_up = random.choice([GHOST, SPEED, SCORE_MULTIPLIER])
                self.power_up_timer = pygame.time.get_ticks() + 5000
                audio_manager.play("power")
                game.power_up = None

            if self.power_up and pygame.time.get_ticks() > self.power_up_timer:
                self.power_up = None

            return False
        except Exception as e:
            print(f"Error in snake move: {e}")
            return True

    def ai_move(self, food, obstacles, other_snake):
        try:
            head = self.body[0]
            directions = [UP, DOWN, LEFT, RIGHT]
            safe_directions = []

            for d in directions:
                new_head = (head[0] + d[0], head[1] + d[1])
                if (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT and
                    new_head not in obstacles and new_head not in self.body[1:] and
                    (not other_snake or new_head not in other_snake.body or self.power_up == GHOST or (other_snake.power_up == GHOST if other_snake else True))):
                    safe_directions.append(d)

            if not safe_directions:
                return self.direction

            dx = food[0] - head[0]
            dy = food[1] - head[1]
            angle = degrees(atan2(dy, dx))
            if -45 <= angle < 45:
                preferred = RIGHT
            elif 45 <= angle < 135:
                preferred = DOWN
            elif 135 <= angle or angle < -135:
                preferred = LEFT
            else:
                preferred = UP

            if preferred in safe_directions and preferred != (-self.direction[0], -self.direction[1]):
                return preferred
            return random.choice(safe_directions) if safe_directions else self.direction
        except Exception as e:
            print(f"Error in AI move: {e}")
            return self.direction

class SnakeGame:
    def __init__(self):
        self.state = MENU
        self.high_score = 0
        self.level = 1
        self.speed = 5
        self.player1_color = GREEN
        self.player2_color = BLUE
        self.obstacles = []
        self.is_multiplayer = False
        self.reset()

    def reset(self):
        try:
            # P1 is AI, P2 is user in multiplayer mode
            self.snake1 = Snake((GRID_WIDTH // 2, GRID_HEIGHT // 2), self.player1_color, "ai" if self.is_multiplayer else "user")
            self.snake2 = Snake((GRID_WIDTH // 4, GRID_HEIGHT // 4), self.player2_color, "user") if self.is_multiplayer else None
            self.obstacles = self.generate_obstacles()
            self.food = self.generate_food()
            self.power_up = None
            self.speed = 5 + (self.level - 1)
            self.bg_color = BLACK
            self.bg_timer = pygame.time.get_ticks()
        except Exception as e:
            print(f"Error in reset: {e}")
            self.state = MENU

    def generate_food(self):
        try:
            while True:
                food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                if (food not in self.snake1.body and
                    (not self.snake2 or food not in self.snake2.body) and
                    food not in self.obstacles):
                    return food
        except Exception as e:
            print(f"Error generating food: {e}")
            return (GRID_WIDTH // 2, GRID_HEIGHT // 2)

    def generate_power_up(self):
        try:
            if random.random() < 0.15:
                while True:
                    power_up = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                    if (power_up not in self.snake1.body and
                        (not self.snake2 or power_up not in self.snake2.body) and
                        power_up != self.food and power_up not in self.obstacles):
                        return power_up
            return None
        except Exception as e:
            print(f"Error generating power-up: {e}")
            return None

    def generate_obstacles(self):
        try:
            obstacles = []
            for _ in range(self.level):
                while True:
                    obs = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                    if (obs not in self.snake1.body and
                        (not self.snake2 or obs not in self.snake2.body) and
                        (not hasattr(self, 'food') or obs != self.food)):
                        obstacles.append(obs)
                        break
            return obstacles
        except Exception as e:
            print(f"Error generating obstacles: {e}")
            return []

    def move(self):
        try:
            game_over = False
            if self.is_multiplayer:
                ai_direction = self.snake1.ai_move(self.food, self.obstacles, self.snake2)
                game_over |= self.snake1.move(ai_direction, self.food, self.obstacles, self.snake2, self)
                game_over |= self.snake2.move(self.snake2.direction, self.food, self.obstacles, self.snake1, self)
            else:
                game_over |= self.snake1.move(self.snake1.direction, self.food, self.obstacles, None, self)

            if self.food in [self.snake1.body[0]] or (self.is_multiplayer and self.snake2 and self.food in [self.snake2.body[0]]):
                self.food = self.generate_food()
                self.power_up = self.generate_power_up()
                if len(self.snake1.body) % 5 == 0 or (self.is_multiplayer and self.snake2 and len(self.snake2.body) % 5 == 0):
                    self.level += 1
                    self.speed += 1
                    self.obstacles = self.generate_obstacles()

            return game_over
        except Exception as e:
            print(f"Error in move: {e}")
            return True

    def draw(self):
        try:
            if pygame.time.get_ticks() - self.bg_timer > 100:
                r = (pygame.time.get_ticks() // 10) % 255
                self.bg_color = (r // 5, r // 10, r // 5)
                self.bg_timer = pygame.time.get_ticks()
            SCREEN.fill(self.bg_color)

            border_width = 5 + (pygame.time.get_ticks() // 500 % 2) * 2
            pygame.draw.rect(SCREEN, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), border_width)

            for x in range(0, WIDTH, GRID_SIZE):
                pygame.draw.line(SCREEN, (50, 50, 50), (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, GRID_SIZE):
                pygame.draw.line(SCREEN, (50, 50, 50), (0, y), (WIDTH, y))

            for i, segment in enumerate(self.snake1.body):
                color = self.snake1.color if self.snake1.power_up != GHOST else YELLOW
                pygame.draw.rect(SCREEN, color, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            if self.is_multiplayer and self.snake2:
                for i, segment in enumerate(self.snake2.body):
                    color = self.snake2.color if self.snake2.power_up != GHOST else YELLOW
                    pygame.draw.rect(SCREEN, color, (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

            pygame.draw.rect(SCREEN, RED, (self.food[0] * GRID_SIZE, self.food[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

            if self.power_up:
                color = {GHOST: YELLOW, SPEED: (0, 255, 255), SCORE_MULTIPLIER: PURPLE}.get(self.snake1.power_up or (self.snake2.power_up if self.is_multiplayer and self.snake2 else None), YELLOW)
                pygame.draw.rect(SCREEN, color, (self.power_up[0] * GRID_SIZE, self.power_up[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

            for obs in self.obstacles:
                pygame.draw.rect(SCREEN, PURPLE, (obs[0] * GRID_SIZE, obs[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

            score_text = SMALL_FONT.render(f"P1: {self.snake1.score}" + (f"  P2: {self.snake2.score}" if self.is_multiplayer and self.snake2 else "") + f"  Level: {self.level}", True, WHITE)
            SCREEN.blit(score_text, (10, 10))

            if self.state == PLAYING:
                pause_text = SMALL_FONT.render("Pause", True, WHITE)
                pygame.draw.rect(SCREEN, GRAY, (WIDTH - 100, 10, 80, 30))
                SCREEN.blit(pause_text, (WIDTH - 90, 15))

            if self.state == MENU:
                self.draw_menu()
            elif self.state == GAME_OVER:
                self.draw_game_over()
            elif self.state == PAUSED:
                self.draw_paused()
            elif self.state == NEW_GAME:
                self.draw_level_select()
            elif self.state == COLOR_SELECT:
                self.draw_color_select()
            elif self.state == MODE_SELECT:
                self.draw_mode_select()
        except Exception as e:
            print(f"Error in draw: {e}")

    def draw_menu(self):
        title = FONT.render("Snake Game", True, GREEN)
        play = SMALL_FONT.render("Play", True, WHITE)
        new_game = SMALL_FONT.render("New Game", True, WHITE)
        mode_select = SMALL_FONT.render("Game Mode", True, WHITE)
        color_select = SMALL_FONT.render("Adjust Colors", True, WHITE)
        exit_game = SMALL_FONT.render("Exit", True, WHITE)
        high = SMALL_FONT.render(f"High Score: {self.high_score}", True, WHITE)

        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40))
        SCREEN.blit(play, (WIDTH // 2 - play.get_width() // 2, HEIGHT // 2 - 10))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 + 30, 200, 40))
        SCREEN.blit(new_game, (WIDTH // 2 - new_game.get_width() // 2, HEIGHT // 2 + 40))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 40))
        SCREEN.blit(mode_select, (WIDTH // 2 - mode_select.get_width() // 2, HEIGHT // 2 + 90))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 + 130, 200, 40))
        SCREEN.blit(color_select, (WIDTH // 2 - color_select.get_width() // 2, HEIGHT // 2 + 140))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 + 180, 200, 40))
        SCREEN.blit(exit_game, (WIDTH // 2 - exit_game.get_width() // 2, HEIGHT // 2 + 190))
        SCREEN.blit(high, (WIDTH // 2 - high.get_width() // 2, HEIGHT // 2 + 240))

    def draw_mode_select(self):
        title = FONT.render("Select Game Mode", True, GREEN)
        single = SMALL_FONT.render("Single Player", True, WHITE)
        multi = SMALL_FONT.render("Multiplayer", True, WHITE)

        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40))
        SCREEN.blit(single, (WIDTH // 2 - single.get_width() // 2, HEIGHT // 2 - 10))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 + 30, 200, 40))
        SCREEN.blit(multi, (WIDTH // 2 - multi.get_width() // 2, HEIGHT // 2 + 40))

    def draw_level_select(self):
        title = FONT.render("Select Level", True, GREEN)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        for i in range(1, 6):
            level_text = SMALL_FONT.render(f"Level {i}", True, WHITE)
            pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 100, HEIGHT // 2 - 50 + i * 50, 200, 40))
            SCREEN.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 2 - 40 + i * 50))

    def draw_color_select(self):
        title = FONT.render("Adjust Snake Colors", True, GREEN)
        p1 = SMALL_FONT.render("Player 1", True, self.player1_color)
        p2 = SMALL_FONT.render("Player 2", True, self.player2_color)
        done = SMALL_FONT.render("Done", True, WHITE)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        SCREEN.blit(p1, (WIDTH // 4 - p1.get_width() // 2, HEIGHT // 2 - 50))
        if self.is_multiplayer:
            SCREEN.blit(p2, (3 * WIDTH // 4 - p2.get_width() // 2, HEIGHT // 2 - 50))
        for i, color in enumerate(colors):
            pygame.draw.rect(SCREEN, color, (WIDTH // 4 - 50 + i * 30, HEIGHT // 2, 25, 25))
            if self.is_multiplayer:
                pygame.draw.rect(SCREEN, color, (3 * WIDTH // 4 - 50 + i * 30, HEIGHT // 2, 25, 25))
        pygame.draw.rect(SCREEN, GRAY, (WIDTH // 2 - 50, HEIGHT // 2 + 100, 100, 40))
        SCREEN.blit(done, (WIDTH // 2 - done.get_width() // 2, HEIGHT // 2 + 110))

    def draw_game_over(self):
        over = FONT.render("Game Over", True, RED)
        score1 = SMALL_FONT.render(f"Player 1: {self.snake1.score}", True, WHITE)
        score2 = SMALL_FONT.render(f"Player 2: {self.snake2.score}", True, WHITE) if self.is_multiplayer and self.snake2 else None
        restart = SMALL_FONT.render("Press R to Restart", True, WHITE)
        menu = SMALL_FONT.render("Press M for Menu", True, WHITE)

        SCREEN.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 4))
        SCREEN.blit(score1, (WIDTH // 2 - score1.get_width() // 2, HEIGHT // 2))
        if score2:
            SCREEN.blit(score2, (WIDTH // 2 - score2.get_width() // 2, HEIGHT // 2 + 30))
        SCREEN.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + (60 if score2 else 30)))
        SCREEN.blit(menu, (WIDTH // 2 - menu.get_width() // 2, HEIGHT // 2 + (90 if score2 else 60)))

    def draw_paused(self):
        paused = FONT.render("Paused", True, BLUE)
        resume = SMALL_FONT.render("Press P to Resume", True, WHITE)
        SCREEN.blit(paused, (WIDTH // 2 - paused.get_width() // 2, HEIGHT // 3))
        SCREEN.blit(resume, (WIDTH // 2 - resume.get_width() // 2, HEIGHT // 2))

    def handle_input(self, event):
        try:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                print(f"Key pressed: {pygame.key.name(event.key)}")  # Debug key input
                if self.state == PLAYING:
                    if self.is_multiplayer:
                        # Control P2 (snake2) with arrow keys
                        if event.key == pygame.K_UP and self.snake2.direction != DOWN:
                            self.snake2.direction = UP
                        elif event.key == pygame.K_DOWN and self.snake2.direction != UP:
                            self.snake2.direction = DOWN
                        elif event.key == pygame.K_LEFT and self.snake2.direction != RIGHT:
                            self.snake2.direction = LEFT
                        elif event.key == pygame.K_RIGHT and self.snake2.direction != LEFT:
                            self.snake2.direction = RIGHT
                    else:
                        # Control P1 (snake1) in single-player
                        if event.key == pygame.K_UP and self.snake1.direction != DOWN:
                            self.snake1.direction = UP
                        elif event.key == pygame.K_DOWN and self.snake1.direction != UP:
                            self.snake1.direction = DOWN
                        elif event.key == pygame.K_LEFT and self.snake1.direction != RIGHT:
                            self.snake1.direction = LEFT
                        elif event.key == pygame.K_RIGHT and self.snake1.direction != LEFT:
                            self.snake1.direction = RIGHT
                    if event.key == pygame.K_p:
                        self.state = PAUSED
                    elif event.key == pygame.K_ESCAPE:
                        self.state = MENU
                elif self.state == MENU:
                    if event.key == pygame.K_SPACE:
                        self.reset()
                        self.state = PLAYING
                elif self.state == GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset()
                        self.state = PLAYING
                    elif event.key == pygame.K_m:
                        self.state = MENU
                elif self.state == PAUSED:
                    if event.key == pygame.K_p:
                        self.state = PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                print(f"Mouse clicked at: {pos}")
                if self.state == PLAYING:
                    if WIDTH - 100 <= pos[0] <= WIDTH - 20 and 10 <= pos[1] <= 40:
                        self.state = PAUSED
                elif self.state == MENU:
                    if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100:
                        if HEIGHT // 2 - 20 <= pos[1] <= HEIGHT // 2 + 20:
                            self.reset()
                            self.state = PLAYING
                        elif HEIGHT // 2 + 30 <= pos[1] <= HEIGHT // 2 + 70:
                            self.state = NEW_GAME
                        elif HEIGHT // 2 + 80 <= pos[1] <= HEIGHT // 2 + 120:
                            self.state = MODE_SELECT
                        elif HEIGHT // 2 + 130 <= pos[1] <= HEIGHT // 2 + 170:
                            self.state = COLOR_SELECT
                        elif HEIGHT // 2 + 180 <= pos[1] <= HEIGHT // 2 + 220:
                            pygame.quit()
                            sys.exit()
                elif self.state == NEW_GAME:
                    for i in range(1, 6):
                        if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100 and HEIGHT // 2 - 50 + i * 50 <= pos[1] <= HEIGHT // 2 - 10 + i * 50:
                            self.level = i
                            self.reset()
                            self.state = PLAYING
                elif self.state == MODE_SELECT:
                    if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100:
                        if HEIGHT // 2 - 20 <= pos[1] <= HEIGHT // 2 + 20:
                            self.is_multiplayer = False
                            self.reset()
                            self.state = PLAYING
                        elif HEIGHT // 2 + 30 <= pos[1] <= HEIGHT // 2 + 70:
                            self.is_multiplayer = True
                            self.reset()
                            self.state = PLAYING
                elif self.state == COLOR_SELECT:
                    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
                    for i in range(5):
                        if WIDTH // 4 - 50 + i * 30 <= pos[0] <= WIDTH // 4 - 25 + i * 30 and HEIGHT // 2 <= pos[1] <= HEIGHT // 2 + 25:
                            self.player1_color = colors[i]
                            self.snake1.color = colors[i]
                        if self.is_multiplayer and 3 * WIDTH // 4 - 50 + i * 30 <= pos[0] <= 3 * WIDTH // 4 - 25 + i * 30 and HEIGHT // 2 <= pos[1] <= HEIGHT // 2 + 25:
                            self.player2_color = colors[i]
                            if self.snake2:
                                self.snake2.color = colors[i]
                    if WIDTH // 2 - 50 <= pos[0] <= WIDTH // 2 + 50 and HEIGHT // 2 + 100 <= pos[1] <= HEIGHT // 2 + 140:
                        self.state = MENU
        except Exception as e:
            print(f"Error in handle_input: {e}")

def main():
    try:
        game = SnakeGame()
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                game.handle_input(event)

            if game.state == PLAYING:
                if (game.snake1.power_up == SPEED or (game.is_multiplayer and game.snake2 and game.snake2.power_up == SPEED)):
                    game.speed = 8 + (game.level - 1)
                else:
                    game.speed = 5 + (game.level - 1)
                if game.move():
                    if game.snake1.score > game.high_score or (game.is_multiplayer and game.snake2 and game.snake2.score > game.high_score):
                        game.high_score = max(game.snake1.score, game.snake2.score if game.is_multiplayer and game.snake2 else 0)
                    game.state = GAME_OVER

            game.draw()
            pygame.display.flip()
            clock.tick(game.speed if game.state == PLAYING else 60)
    except Exception as e:
        print(f"Error in main loop: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
