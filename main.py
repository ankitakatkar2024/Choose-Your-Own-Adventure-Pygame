
import pygame
import sys
import os
import math
import random
import wave
import struct

from settings import *
from game.buttons import Button


# ==================================================
# 1. INITIALIZATION
# ==================================================

pygame.init()

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)

clock = pygame.time.Clock()

title_font = pygame.font.SysFont("arial", 48, bold=True)
font = pygame.font.SysFont("arial", 25, bold=True)
small_font = pygame.font.SysFont("arial", 19)

# Audio channels
if SOUND_ENABLED:
    ambient_channel = pygame.mixer.Channel(0)
else:
    ambient_channel = None


# ==================================================
# 2. GAME STATES
# ==================================================

MENU = "menu"
ROAD = "road"
RIVER = "river"
BRIDGE = "bridge"
BRIDGE_CROSS = "bridge_cross"
STRANGER = "stranger"

RIVER_WALK = "river_walk"
RIVER_SWIM = "river_swim"

WIN = "win"
GAME_OVER = "game_over"

current_scene = MENU

player_name = ""
input_active = False

dialogue = ""
dialogue_start = 0
typing_speed = 32

scene_message = ""


# ==================================================
# 3. AUTOMATIC FOREST AMBIENCE GENERATOR
# ==================================================

def create_forest_ambience():

    path = os.path.join(SOUND_DIR, "forest.wav")

    if os.path.exists(path):
        return

    os.makedirs(SOUND_DIR, exist_ok=True)

    sample_rate = 22050
    duration = 5
    total_samples = sample_rate * duration

    random.seed(12)

    with wave.open(path, "wb") as audio:

        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)

        frames = bytearray()

        for i in range(total_samples):

            t = i / sample_rate

            wind = math.sin(2 * math.pi * 90 * t) * 0.10
            bird = math.sin(2 * math.pi * 1200 * t) * 0.025
            leaves = random.uniform(-0.08, 0.08)

            sample = wind + bird + leaves

            # Fade at both ends to reduce clicks when looping
            fade_length = sample_rate // 4
            fade_in = min(1, i / fade_length)
            fade_out = min(1, (total_samples - i) / fade_length)

            sample *= min(fade_in, fade_out)

            value = int(
                max(-1, min(1, sample)) * 32767
            )

            frames.extend(struct.pack("<h", value))

        audio.writeframes(frames)


if SOUND_ENABLED:
    create_forest_ambience()


# ==================================================
# 4. LOAD BACKGROUND IMAGES
# ==================================================

def load_image(filename):

    path = os.path.join(IMAGE_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing image: {path}"
        )

    image = pygame.image.load(path).convert()

    return pygame.transform.smoothscale(
        image,
        (WIDTH, HEIGHT)
    )


backgrounds = {
    ROAD: load_image("road.png"),
    RIVER: load_image("river.png"),
    BRIDGE: load_image("bridge.png"),
    STRANGER: load_image("stranger.png")
}


# ==================================================
# 5. LOAD SOUND EFFECTS
# ==================================================

def load_sound(filename):

    if not SOUND_ENABLED:
        return None

    path = os.path.join(SOUND_DIR, filename)

    if not os.path.exists(path):
        print("Missing sound:", filename)
        return None

    try:
        return pygame.mixer.Sound(path)

    except pygame.error:
        print("Could not load:", filename)
        return None


sounds = {
    "walk": load_sound("walk.wav"),
    "swim": load_sound("swim.wav"),
    "river": load_sound("river.wav"),
    "bridge": load_sound("bridge.wav"),
    "click": load_sound("click.wav"),
    "win": load_sound("win.wav"),
    "lose": load_sound("lose.wav"),
    "forest": load_sound("forest.wav")
}


def play_sound(name):

    sound = sounds.get(name)

    if sound:
        sound.play()


def stop_ambience():

    if ambient_channel:
        ambient_channel.fadeout(400)


def set_ambience(name):

    if not SOUND_ENABLED or ambient_channel is None:
        return

    sound = sounds.get(name)

    if sound is None:
        ambient_channel.stop()
        return

    # Avoid restarting the same ambience unnecessarily
    if ambient_channel.get_busy():
        current = ambient_channel.get_sound()

        if current == sound:
            return

    ambient_channel.stop()
    ambient_channel.set_volume(0.25)
    ambient_channel.play(sound, loops=-1, fade_ms=700)


# ==================================================
# 6. BUTTONS
# ==================================================

start_button = Button(
    375, 420, 250, 60,
    "START GAME", GREEN
)

quit_button = Button(
    375, 500, 250, 55,
    "QUIT", RED
)

left_button = Button(
    200, 535, 250, 60,
    "GO LEFT", GREEN
)

right_button = Button(
    550, 535, 250, 60,
    "GO RIGHT", BLUE
)

walk_button = Button(
    200, 535, 250, 60,
    "WALK", GREEN
)

swim_button = Button(
    550, 535, 250, 60,
    "SWIM", BLUE
)

cross_button = Button(
    200, 535, 250, 60,
    "CROSS", GREEN
)

back_button = Button(
    550, 535, 250, 60,
    "GO BACK", RED
)

yes_button = Button(
    200, 535, 250, 60,
    "YES", GREEN
)

no_button = Button(
    550, 535, 250, 60,
    "NO", RED
)

restart_button = Button(
    200, 535, 250, 60,
    "PLAY AGAIN", GREEN
)

exit_button = Button(
    550, 535, 250, 60,
    "QUIT", RED
)


# ==================================================
# 7. PLAYER ANIMATION
# ==================================================

player_x = 500
player_y = 420

player_direction = 1
player_moving = False

animation_time = 0

PLAYER_WIDTH = 42
PLAYER_HEIGHT = 78


def draw_player(x, y, moving=False, direction=1):

    global animation_time

    animation_time += 0.12

    swing = math.sin(animation_time * 8) * 9 if moving else 0

    # Character shadow
    pygame.draw.ellipse(
        screen,
        (20, 35, 20),
        (x - 22, y + 65, 44, 12)
    )

    # Legs
    leg_offset = int(swing)

    pygame.draw.rect(
        screen,
        (45, 55, 85),
        (x - 13, y + 43, 11, 25 + leg_offset)
    )

    pygame.draw.rect(
        screen,
        (45, 55, 85),
        (x + 2, y + 43, 11, 25 - leg_offset)
    )

    # Shoes
    pygame.draw.rect(
        screen,
        (75, 40, 25),
        (x - 16, y + 64 + leg_offset, 17, 9)
    )

    pygame.draw.rect(
        screen,
        (75, 40, 25),
        (x + 1, y + 64 - leg_offset, 17, 9)
    )

    # Body / red jacket
    pygame.draw.rect(
        screen,
        (185, 55, 45),
        (x - 16, y + 16, 32, 31),
        border_radius=5
    )

    # Arms
    pygame.draw.line(
        screen,
        (35, 110, 110),
        (x - 15, y + 22),
        (x - 23, y + 39 + int(swing)),
        8
    )

    pygame.draw.line(
        screen,
        (35, 110, 110),
        (x + 15, y + 22),
        (x + 23, y + 39 - int(swing)),
        8
    )

    # Head
    pygame.draw.circle(
        screen,
        (190, 125, 80),
        (x, y + 7),
        15
    )

    # Hair
    pygame.draw.arc(
        screen,
        (65, 35, 25),
        (x - 16, y - 10, 32, 30),
        math.pi,
        math.pi * 2,
        8
    )

    # Direction marker
    if direction < 0:
        pygame.draw.circle(
            screen,
            GOLD,
            (x - 5, y + 7),
            2
        )

# ==================================================
# DRAW BACKGROUND
# ==================================================

def draw_background(scene):
    screen.blit(backgrounds[scene], (0, 0))
    
# ==================================================
# 8. TEXT AND DIALOGUE
# ==================================================

def draw_text(text, font_object, color, x, y):

    surface = font_object.render(
        text,
        True,
        color
    )

    rect = surface.get_rect(
        center=(x, y)
    )

    screen.blit(surface, rect)


def set_dialogue(message):

    global dialogue, dialogue_start

    dialogue = message
    dialogue_start = pygame.time.get_ticks()


def draw_dialogue():

    panel = pygame.Rect(
        75, 420, 850, 85
    )

    pygame.draw.rect(
        screen,
        DARK_PANEL,
        panel,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        GOLD,
        panel,
        3,
        border_radius=14
    )

    elapsed = (
        pygame.time.get_ticks() - dialogue_start
    )

    visible_characters = int(
        elapsed / typing_speed
    )

    visible_text = dialogue[:visible_characters]

    # Wrap long text into two lines
    words = visible_text.split()
    lines = []
    current_line = ""

    for word in words:

        test_line = (
            current_line + " " + word
        ).strip()

        if font.size(test_line)[0] > 800:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)

    for index, line in enumerate(lines[:2]):

        draw_text(
            line,
            small_font,
            WHITE,
            WIDTH // 2,
            447 + index * 28
        )


# ==================================================
# 9. WATER ANIMATION
# ==================================================

def draw_water_animation():

    current_time = pygame.time.get_ticks()

    for i in range(12):

        x = (i * 97 + current_time // 35) % WIDTH
        y = 300 + (i * 37) % 180

        width = 15 + int(
            abs(math.sin(current_time / 400 + i)) * 18
        )

        pygame.draw.ellipse(
            screen,
            (130, 225, 245),
            (x, y, width, 4)
        )


# ==================================================
# 10. SCENE MANAGEMENT
# ==================================================

def change_scene(scene, message):

    global current_scene

    current_scene = scene
    set_dialogue(message)

    if scene == RIVER:
        set_ambience("river")

    elif scene in (ROAD, BRIDGE, STRANGER):
        set_ambience("forest")

    elif scene in (WIN, GAME_OVER):
        stop_ambience()


def finish_game(won):

    if won:
        change_scene(
            WIN,
            "You reached the nearest town safely!"
        )
        play_sound("win")

    else:
        change_scene(
            GAME_OVER,
            "Your adventure has come to an end."
        )
        play_sound("lose")


def reset_game():

    global player_name
    global player_x, player_y
    global input_active
    global animation_time

    player_name = ""
    player_x = 500
    player_y = 420
    input_active = False
    animation_time = 0

    change_scene(
        MENU,
        "Welcome to your adventure!"
    )


# ==================================================
# 11. MAIN MENU
# ==================================================

def draw_menu():

    # Illustrated road background
    draw_background(ROAD)

    # Dark overlay
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 125))
    screen.blit(overlay, (0, 0))

    # Menu panel
    panel = pygame.Rect(
        270, 90, 460, 480
    )

    pygame.draw.rect(
        screen,
        DARK_PANEL,
        panel,
        border_radius=25
    )

    pygame.draw.rect(
        screen,
        GOLD,
        panel,
        4,
        border_radius=25
    )

    draw_text(
        "CHOOSE YOUR OWN",
        title_font,
        WHITE,
        WIDTH // 2,
        165
    )

    draw_text(
        "ADVENTURE",
        title_font,
        GOLD,
        WIDTH // 2,
        225
    )

    draw_text(
        "Enter your name:",
        font,
        WHITE,
        WIDTH // 2,
        310
    )

    name_box = pygame.Rect(
        350, 340, 300, 50
    )

    pygame.draw.rect(
        screen,
        WHITE,
        name_box,
        border_radius=8
    )

    name_surface = font.render(
        player_name,
        True,
        BLACK
    )

    screen.blit(
        name_surface,
        (name_box.x + 10, name_box.y + 10)
    )

    start_button.draw(screen, font)
    quit_button.draw(screen, font)


# ==================================================
# 12. END SCREEN
# ==================================================

def draw_end_screen(won):

    if won:
        screen.blit(
            backgrounds[ROAD],
            (0, 0)
        )

        draw_text(
            "YOU WIN!",
            title_font,
            GOLD,
            WIDTH // 2,
            220
        )

    else:
        screen.blit(
            backgrounds[STRANGER],
            (0, 0)
        )

        draw_text(
            "GAME OVER!",
            title_font,
            RED,
            WIDTH // 2,
            220
        )

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 115))
    screen.blit(overlay, (0, 0))

    draw_text(
        "YOU WIN!" if won else "GAME OVER!",
        title_font,
        GOLD if won else RED,
        WIDTH // 2,
        260
    )

    draw_dialogue()

    restart_button.draw(screen, font)
    exit_button.draw(screen, font)


# ==================================================
# 13. ANIMATION VARIABLES
# ==================================================

movement_start = 0
movement_duration = 1800

movement_from = 0
movement_to = 0

river_animation_start = 0


def start_movement(scene, start_x, end_x, message):

    global movement_start
    global movement_from
    global movement_to
    global player_x

    movement_from = start_x
    movement_to = end_x

    player_x = start_x
    movement_start = pygame.time.get_ticks()

    change_scene(scene, message)


def update_movement():

    global player_x
    global current_scene

    elapsed = (
        pygame.time.get_ticks() - movement_start
    )

    progress = min(
        elapsed / movement_duration,
        1
    )

    # Smooth movement
    progress = (
        progress * progress * (3 - 2 * progress)
    )

    player_x = (
        movement_from
        + (movement_to - movement_from) * progress
    )

    if progress >= 1:

        if current_scene == BRIDGE_CROSS:

            change_scene(
                STRANGER,
                "You crossed the bridge and met a stranger. Talk to them?"
            )

        elif current_scene == RIVER_WALK:

            finish_game(False)

        elif current_scene == RIVER_SWIM:

            finish_game(False)


# ==================================================
# 14. GAME LOOP
# ==================================================

running = True

set_dialogue("Enter your name to begin.")

while running:

    delta_time = clock.tick(FPS) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ---------------- MENU ----------------

        if current_scene == MENU:

            if event.type == pygame.MOUSEBUTTONDOWN:

                name_box = pygame.Rect(
                    350, 340, 300, 50
                )

                input_active = name_box.collidepoint(
                    event.pos
                )

            if event.type == pygame.KEYDOWN and input_active:

                if event.key == pygame.K_BACKSPACE:

                    player_name = player_name[:-1]

                elif event.key == pygame.K_RETURN:

                    if player_name.strip():
                        change_scene(
                            ROAD,
                            f"Welcome {player_name}! You are standing on a dirt road. Choose a direction."
                        )

                elif event.unicode.isprintable():

                    if len(player_name) < 18:
                        player_name += event.unicode

            if start_button.is_clicked(event):

                if player_name.strip():

                    play_sound("click")

                    change_scene(
                        ROAD,
                        f"Welcome {player_name}! You are standing on a dirt road. Choose a direction."
                    )

            if quit_button.is_clicked(event):
                running = False

        # ---------------- ROAD ----------------

        elif current_scene == ROAD:

            if left_button.is_clicked(event):

                play_sound("click")

                player_direction = -1

                change_scene(
                    RIVER,
                    "You reached a river. Do you want to walk or swim?"
                )

            elif right_button.is_clicked(event):

                play_sound("click")

                player_direction = 1

                change_scene(
                    BRIDGE,
                    "You reached a wobbly bridge. Do you want to cross it or go back?"
                )

        # ---------------- RIVER ----------------

        elif current_scene == RIVER:

            if walk_button.is_clicked(event):

                play_sound("walk")

                start_movement(
                    RIVER_WALK,
                    350,
                    180,
                    "You are walking along the river bank..."
                )

            elif swim_button.is_clicked(event):

                play_sound("swim")

                start_movement(
                    RIVER_SWIM,
                    350,
                    800,
                    "You are swimming across the river..."
                )

        # ---------------- BRIDGE ----------------

        elif current_scene == BRIDGE:

            if cross_button.is_clicked(event):

                play_sound("bridge")

                start_movement(
                    BRIDGE_CROSS,
                    250,
                    750,
                    "You are carefully crossing the bridge..."
                )

            elif back_button.is_clicked(event):

                play_sound("walk")
                finish_game(False)

        # ---------------- STRANGER ----------------

        elif current_scene == STRANGER:

            if yes_button.is_clicked(event):

                finish_game(True)

            elif no_button.is_clicked(event):

                finish_game(False)

        # ---------------- END SCREENS ----------------

        elif current_scene in (WIN, GAME_OVER):

            if restart_button.is_clicked(event):

                play_sound("click")
                reset_game()

            elif exit_button.is_clicked(event):

                running = False

    # ==================================================
    # UPDATE ANIMATIONS
    # ==================================================

    if current_scene in (
        BRIDGE_CROSS,
        RIVER_WALK,
        RIVER_SWIM
    ):

        update_movement()

    # ==================================================
    # DRAW SCENES
    # ==================================================

    if current_scene == MENU:

        draw_menu()

    elif current_scene == ROAD:

        draw_background(ROAD)

        draw_player(
            player_x,
            player_y,
            moving=False,
            direction=player_direction
        )

        draw_dialogue()

        left_button.draw(screen, font)
        right_button.draw(screen, font)

    elif current_scene == RIVER:

        draw_background(RIVER)
        draw_water_animation()

        draw_dialogue()

        walk_button.draw(screen, font)
        swim_button.draw(screen, font)

    elif current_scene == RIVER_WALK:

        draw_background(RIVER)
        draw_water_animation()

        draw_player(
            player_x,
            420,
            moving=True,
            direction=-1
        )

        draw_dialogue()

    elif current_scene == RIVER_SWIM:

        draw_background(RIVER)
        draw_water_animation()

        # Swimming character
        pygame.draw.ellipse(
            screen,
            (45, 110, 190),
            (int(player_x) - 18, 390, 40, 22)
        )

        pygame.draw.circle(
            screen,
            (190, 125, 80),
            (int(player_x), 382),
            12
        )

        draw_dialogue()

    elif current_scene == BRIDGE:

        draw_background(BRIDGE)

        draw_player(
            250,
            360,
            moving=False
        )

        draw_dialogue()

        cross_button.draw(screen, font)
        back_button.draw(screen, font)

    elif current_scene == BRIDGE_CROSS:

        draw_background(BRIDGE)

        draw_player(
            int(player_x),
            360,
            moving=True
        )

        draw_dialogue()

    elif current_scene == STRANGER:

        draw_background(STRANGER)
        draw_dialogue()

        yes_button.draw(screen, font)
        no_button.draw(screen, font)

    elif current_scene == WIN:

        draw_end_screen(True)

    elif current_scene == GAME_OVER:

        draw_end_screen(False)

    pygame.display.flip()


# ==================================================
# 15. CLOSE GAME
# ==================================================

stop_ambience()

pygame.quit()
sys.exit()
