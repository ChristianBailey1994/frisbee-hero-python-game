"""
CS 1400 Final Project
Names: Christian Bailey & Thomas Frank
Game: FrisbeeHero

- Player stays near the bottom of the screen
- Player moves left and right
- Enemies enter from the top and snake downward
- Player shoots frisbees towards location of mouse
- If enemies hit the player or reach the bottom, the player loses
"""

import sys
import os
import pygame
from pygame import Vector2
import random

# if verbose is true, print some debug messages, otherwise "silence"
VERBOSE = False

"""setup"""

# NOTE:
# Some of the features in this file are more advanced than a normal CS 1400 project.
# AI was used to help get parts of the enemy spawning, power-up system,
# scoreboard placement, and death screen timing implemented.
WIDTH = 1200
HEIGHT = 900
FPS = 60

PLAYER_SPEED = 7
PLAYER_FRISBEE_SPEED = 12
ENEMY_SPEED = 3
ENEMY_DROP_DISTANCE = 40

BACKGROUND_FILES = ["summer.png", "winter.png", "fall.png", "spring.png"]

PLAYER_SIZE = 80
NORMAL_ENEMY_SIZE = 60
CLUSTER_SIZE = 120
BOSS_SIZE = 150

NORMAL_HEALTH = 1
CLUSTER_HEALTH = 4
BOSS_HEALTH = 10

DROPPED_SIZE = 45
TROPHY_SIZE = 45
POWERUP_FALL_SPEED = 2
DROPPED_DROP_CHANCE = 0.20
TROPHY_DROP_CHANCE = 0.05

THROW_FRAMES = 10
SPAWN_PADDING = 18

SCOREBOARD_WIDTH = 420
SCOREBOARD_HEIGHT = 220
DEATHSCREEN_DELAY_MS = 2000

FORMATION_PATTERNS = [
    [(0, 0)],
    [(-95, 0), (95, 0)],
    [(0, -70), (0, 70)],
    [(-100, 0), (0, 0), (100, 0)],
    [(0, -90), (-90, 50), (90, 50)],
    [(-110, -60), (0, 0), (110, 60)],
    [(-110, -70), (110, -70), (-110, 70), (110, 70)],
]


"""helper functions"""


def pixel_collision(item1, item2): #Given by instructor
    """
    check to see if two items collide
    Param: game object as item1
    Param: a different game object as item2
    Return true if two game objects overlap using mask collision
    """
    pos1 = item1["pos"]
    pos2 = item2["pos"]
    mask1 = item1["mask"]
    mask2 = item2["mask"]

    #shift images back to 0,0 for collision detection
    pos1_temp = pos1 - Vector2(mask1.get_size()) / 2
    pos2_temp = pos2 - Vector2(mask2.get_size()) / 2
    offset = pos2_temp - pos1_temp

    overlap = mask1.overlap(mask2, offset)
    return overlap is not None



def draw_image_centered(screen, image, pos):
    """
    Draw an image centered on pos.
    """
    rect = image.get_rect()
    screen.blit(image, (pos.x - rect.width // 2, pos.y - rect.height // 2))



def load_scaled_image(filename, width, height):
    """
    Load an image from the assets folder and scale it.
    Received help from AI to get file pathing correct
    """
    image = pygame.image.load(os.path.join("assets", filename)).convert_alpha()
    return pygame.transform.smoothscale(image, (width, height))



def make_game_object(name, image, x, y):
    """
    Create a dictionary representing one game object.
    """
    return {
        "name": name,
        "pos": Vector2(x, y),
        "image": image,
        "mask": pygame.mask.from_surface(image),
        "visible": True,
    }



# NOTE: This enemy spawn placement logic is more advanced than normal CS 1400 work.
# AI was used to help get this section implemented.
def clamp_spawn_position(x, y, image):
    """
    Keep a spawned object on the screen.
    """
    half_width = image.get_width() // 2
    half_height = image.get_height() // 2

    min_x = half_width + 20
    max_x = WIDTH - half_width - 20
    min_y = half_height + 20
    max_y = int(HEIGHT * 0.34) - half_height

    x = max(min_x, min(x, max_x))
    y = max(min_y, min(y, max_y))

    return x, y



def objects_overlap(x, y, image, other_object, padding=0):
    """
    Return True if a new object overlaps another object.
    """
    rect = image.get_rect(center=(x, y))
    if padding > 0:
        rect.inflate_ip(padding * 2, padding * 2)

    other_rect = other_object["image"].get_rect(
        center=(other_object["pos"].x, other_object["pos"].y)
    )
    return rect.colliderect(other_rect)



def is_spawn_clear(x, y, image, existing_objects, padding=SPAWN_PADDING):
    """
    Return True if a new object does not overlap existing objects.
    """
    for other in existing_objects:
        if objects_overlap(x, y, image, other, padding):
            return False
    return True



def make_typed_enemy(enemy_type, image, x, y):
    """
    Create an enemy and give it health and score values.
    """
    enemy = make_game_object(enemy_type, image, x, y)

    if enemy_type == "boss":
        enemy["health"] = BOSS_HEALTH
        enemy["points"] = 1000
    elif enemy_type == "cluster":
        enemy["health"] = CLUSTER_HEALTH
        enemy["points"] = 400
    else:
        enemy["health"] = NORMAL_HEALTH
        enemy["points"] = 100

    return enemy



def choose_regular_enemy_type(level, remaining_difficulty):
    """
    Choose whether to make a normal enemy or a cluster enemy.
    """
    cluster_chance = min(0.08 + level * 0.015, 0.18)

    if remaining_difficulty >= CLUSTER_HEALTH and random.random() < cluster_chance:
        return "cluster"

    return "enemy"



# NOTE: The power-up drop system is more advanced than normal CS 1400 work.
# AI was used to help get this section implemented.
def choose_powerup_drop():
    """
    Randomly choose whether an enemy drops a power-up.
    """
    roll = random.random()

    if roll < TROPHY_DROP_CHANCE:
        return "trophy"
    if roll < TROPHY_DROP_CHANCE + DROPPED_DROP_CHANCE:
        return "dropped"
    return None



def spawn_powerup(powerup_type, image, x, y):
    """
    Create one falling power-up object.
    """
    powerup = make_game_object(powerup_type, image, x, y)
    powerup["y_speed"] = POWERUP_FALL_SPEED
    return powerup



def make_frisbee(player, frisbee_image, direction, is_piercing=False):
    """
    Create one frisbee traveling in a direction.
    """
    frisbee = make_game_object(
        "player_frisbee", frisbee_image, player["pos"].x, player["pos"].y)
    frisbee["x_speed"] = direction.x * PLAYER_FRISBEE_SPEED
    frisbee["y_speed"] = direction.y * PLAYER_FRISBEE_SPEED
    frisbee["piercing"] = is_piercing
    return frisbee



def rotate_vector(direction, degrees):
    """
    Rotate a direction vector by a small angle.
    """
    return direction.rotate(degrees)



def update_player_appearance(player):
    """
    Show the correct player image based on what the player is doing.
    """
    if not player["is_alive"]:
        player["image"] = player["heartbroken_image"]
        player["mask"] = pygame.mask.from_surface(player["image"])
        return

    if player["throw_timer"] > 0:
        player["throw_timer"] -= 1
        player["image"] = player["throw_image"]
    else:
        player["image"] = player["normal_image"]

    player["mask"] = pygame.mask.from_surface(player["image"])


#------------------------------------------
# SETUP FUNCTIONS


def create_player():
    """
    Create the player near the bottom of the screen.
    """
    normal_image = load_scaled_image("player.png", PLAYER_SIZE, PLAYER_SIZE)
    throw_image = load_scaled_image("throw.png", PLAYER_SIZE, PLAYER_SIZE)
    heartbroken_image = load_scaled_image("heartbroken.png", PLAYER_SIZE, PLAYER_SIZE)

    player = make_game_object("player", normal_image, WIDTH // 2, HEIGHT - 80)
    player["normal_image"] = normal_image
    player["throw_image"] = throw_image
    player["heartbroken_image"] = heartbroken_image
    player["is_alive"] = True
    player["cooldown"] = 0
    player["throw_timer"] = 0
    return player



def try_spawn_enemy(enemy_type, image, spawn_x, spawn_y, existing_enemies):
    """
    Try to place one enemy without stacking it on another enemy.
    """
    spawn_x, spawn_y = clamp_spawn_position(spawn_x, spawn_y, image)
    if is_spawn_clear(spawn_x, spawn_y, image, existing_enemies):
        return make_typed_enemy(enemy_type, image, spawn_x, spawn_y)
    return None



# NOTE: The random formations, boss spawning, and no-stacking logic
# are more advanced than normal CS 1400 work. AI was used to help
# get this section implemented.
def create_enemy_wave(level):
    """
    Create enemies based on the current level.
    """
    enemy_image = load_scaled_image("enemy.png", NORMAL_ENEMY_SIZE, NORMAL_ENEMY_SIZE)
    cluster_image = load_scaled_image("cluster.png", CLUSTER_SIZE, CLUSTER_SIZE)
    boss_image = load_scaled_image("boss.png", BOSS_SIZE, BOSS_SIZE)

    images = {
        "enemy": enemy_image,
        "cluster": cluster_image,
        "boss": boss_image,
    }

    enemies = []
    total_difficulty = min(10 + level * 2, 24)
    remaining_difficulty = total_difficulty

    if level >= 3 and level % 3 == 0:
        boss_spawned = False
        for _ in range(40):
            boss_x = random.randint(260, WIDTH - 260)
            boss_y = random.randint(90, int(HEIGHT * 0.20))
            boss = try_spawn_enemy("boss", boss_image, boss_x, boss_y, enemies)
            if boss is not None:
                enemies.append(boss)
                remaining_difficulty -= BOSS_HEALTH
                boss_spawned = True
                break
        if not boss_spawned:
            boss_x = WIDTH // 2
            boss_y = 120
            enemies.append(make_typed_enemy("boss", boss_image, boss_x, boss_y))
            remaining_difficulty -= BOSS_HEALTH

    attempts = 0
    while remaining_difficulty > 0 and attempts < 250:
        attempts += 1
        pattern = random.choice(FORMATION_PATTERNS)
        base_x = random.randint(180, WIDTH - 180)
        base_y = random.randint(70, int(HEIGHT * 0.24))
        new_enemies = []

        for offset_x, offset_y in pattern:
            if remaining_difficulty <= 0:
                break

            enemy_type = choose_regular_enemy_type(level, remaining_difficulty)
            image = images[enemy_type]
            spawn_x = base_x + offset_x
            spawn_y = base_y + offset_y

            candidate = try_spawn_enemy(
                enemy_type, image, spawn_x, spawn_y, enemies + new_enemies
            )
            if candidate is None:
                continue

            new_enemies.append(candidate)

            if enemy_type == "cluster":
                remaining_difficulty -= CLUSTER_HEALTH
            else:
                remaining_difficulty -= NORMAL_HEALTH

        enemies.extend(new_enemies)

    return enemies



def create_background():
    """
    Load the background image.
    """
    filename = random.choice(BACKGROUND_FILES)
    return load_scaled_image(filename, WIDTH, HEIGHT)


"""Frisbee throws to kill enemies"""


def throw_player_frisbee(
    player,
    frisbee_image,
    frisbees,
    target_pos,
    multishot_active,
    piercing_active,
):
    """
    Create frisbees that travel from the player toward the mouse click.
    """
    mouse_x, mouse_y = target_pos

    dx = mouse_x - player["pos"].x
    dy = mouse_y - player["pos"].y

    direction = Vector2(dx, dy)

    if direction.length() == 0:
        return

    direction = direction.normalize()

    frisbee_count = 1
    if multishot_active:
        frisbee_count = random.randint(2, 4)

    player["throw_timer"] = THROW_FRAMES

    frisbees.append(make_frisbee(player, frisbee_image, direction, piercing_active))

    for _ in range(frisbee_count - 1):
        angle_offset = random.uniform(-5, 5)
        extra_direction = rotate_vector(direction, angle_offset)
        extra_direction = extra_direction.normalize()
        frisbees.append(make_frisbee(player, frisbee_image, extra_direction, piercing_active))



def update_player_frisbees(frisbees):
    """
    Move frisbees toward their assigned direction and remove off-screen frisbees.
    """
    remaining_frisbees = []

    for frisbee in frisbees:
        frisbee["pos"].x += frisbee["x_speed"]
        frisbee["pos"].y += frisbee["y_speed"]

        if -50 <= frisbee["pos"].x <= WIDTH + 50 and -50 <= frisbee["pos"].y <= HEIGHT + 50:
            remaining_frisbees.append(frisbee)

    return remaining_frisbees



def update_powerups(powerups):
    """
    Move power-ups and remove off-screen ones.
    """
    remaining_powerups = []

    for powerup in powerups:
        powerup["pos"].y += powerup["y_speed"]
        if powerup["pos"].y <= HEIGHT + 50:
            remaining_powerups.append(powerup)

    return remaining_powerups


#------------------------------------------
# ENEMY FUNCTIONS


def update_enemies(enemies, direction, level):
    """
    Move enemies left/right. If they hit an edge, reverse and move down.
    """
    enemy_speed = ENEMY_SPEED + min((level - 1) * 0.10, 1.25)
    hit_edge = False

    for enemy in enemies:
        enemy["pos"].x += enemy_speed * direction

        half_width = enemy["image"].get_width() // 2

        if enemy["pos"].x >= WIDTH - half_width:
            hit_edge = True
        if enemy["pos"].x <= half_width:
            hit_edge = True

    if hit_edge:
        direction *= -1
        for enemy in enemies:
            enemy["pos"].y += ENEMY_DROP_DISTANCE

    return direction



def enemy_reached_bottom(enemies):
    """
    Return True if any enemy has reached the bottom danger zone.
    """
    for enemy in enemies:
        if enemy["pos"].y >= HEIGHT - 120:
            return True
    return False


#------------------------------------------
# COLLISION FUNCTIONS


# NOTE: The piercing frisbee, enemy health, and drop handling logic
# are more advanced than normal CS 1400 work. AI was used to help
# get this section implemented.
def handle_frisbee_enemy_collisions(frisbees, enemies, powerups, score, powerup_images):
    """
    Handle collisions between frisbees and enemies. Update score and drops.
    """
    remaining_frisbees = []

    for frisbee in frisbees:
        frisbee_hit = False

        if frisbee.get("piercing", False):
            for enemy in enemies:
                if enemy["visible"] and pixel_collision(frisbee, enemy):
                    enemy["visible"] = False
                    score += enemy["points"]
                    frisbee_hit = True

                    drop_type = choose_powerup_drop()
                    if drop_type is not None:
                        powerups.append(
                            spawn_powerup(
                                drop_type,
                                powerup_images[drop_type],
                                enemy["pos"].x,
                                enemy["pos"].y,
                            )
                        )

            remaining_frisbees.append(frisbee)
        else:
            for enemy in enemies:
                if enemy["visible"] and pixel_collision(frisbee, enemy):
                    enemy["health"] -= 1
                    frisbee_hit = True

                    if enemy["health"] <= 0:
                        enemy["visible"] = False
                        score += enemy["points"]

                        drop_type = choose_powerup_drop()
                        if drop_type is not None:
                            powerups.append(
                                spawn_powerup(
                                    drop_type,
                                    powerup_images[drop_type],
                                    enemy["pos"].x,
                                    enemy["pos"].y,
                                )
                            )
                    break

            if not frisbee_hit:
                remaining_frisbees.append(frisbee)

    remaining_enemies = []
    for enemy in enemies:
        if enemy["visible"]:
            remaining_enemies.append(enemy)

    return remaining_frisbees, remaining_enemies, powerups, score



def handle_frisbee_powerup_collisions(
    frisbees, powerups, multishot_active, piercing_active
):
    """
    Handle collisions between frisbees and falling power-ups.
    """
    remaining_frisbees = []

    for frisbee in frisbees:
        collected_any = False

        for powerup in powerups:
            if powerup["visible"] and pixel_collision(frisbee, powerup):
                powerup["visible"] = False
                collected_any = True

                if powerup["name"] == "dropped":
                    multishot_active = True
                elif powerup["name"] == "trophy":
                    piercing_active = True

                if not frisbee.get("piercing", False):
                    break

        if frisbee.get("piercing", False):
            remaining_frisbees.append(frisbee)
        elif not collected_any:
            remaining_frisbees.append(frisbee)

    remaining_powerups = []
    for powerup in powerups:
        if powerup["visible"]:
            remaining_powerups.append(powerup)

    return remaining_frisbees, remaining_powerups, multishot_active, piercing_active



def player_hit_enemy(player, enemies):
    """
    Return True if any enemy touches the player.
    """
    for enemy in enemies:
        if pixel_collision(player, enemy):
            return True
    return False


#------------------------------------------
# DRAW FUNCTIONS


def draw_text(screen, font, text, x, y, color=(255, 255, 0)):
    """
    Draw text on the screen.
    """
    label = font.render(text, True, color)
    screen.blit(label, (x, y))



# NOTE: The scoreboard image placement and text overlay positioning
# are more advanced than normal CS 1400 work. AI was used to help
# get this section implemented.
def draw_game(screen,background,scoreboard_image,player,enemies,frisbees,powerups,font,score,level,game_message,multishot_active,piercing_active):
    """
    Draw the current state of the game.
    """
    screen.blit(background, (0, 0))

    if player["visible"]:
        draw_image_centered(screen, player["image"], player["pos"])

    for enemy in enemies:
        if enemy["visible"]:
            draw_image_centered(screen, enemy["image"], enemy["pos"])

    for powerup in powerups:
        if powerup["visible"]:
            draw_image_centered(screen, powerup["image"], powerup["pos"])

    for frisbee in frisbees:
        if frisbee["visible"]:
            draw_image_centered(screen, frisbee["image"], frisbee["pos"])

    scoreboard_x = WIDTH // 2 - scoreboard_image.get_width() // 2 - 450
    scoreboard_y = 0
    screen.blit(scoreboard_image, (scoreboard_x, scoreboard_y))

    number_font = pygame.font.SysFont("monospace", 30, bold=True)
    status_font = pygame.font.SysFont("monospace", 24, bold=True)

    score_text = number_font.render(str(score), True, (255, 255, 255))
    level_text = number_font.render(str(level), True, (255, 255, 255))

    score_x = scoreboard_x + 200
    score_y = scoreboard_y + 85
    level_x = scoreboard_x + 250
    level_y = scoreboard_y + 115

    screen.blit(score_text, (score_x, score_y))
    screen.blit(level_text, (level_x, level_y))

    draw_text(screen, status_font, game_message, 20, HEIGHT - 40)


#------------------------------------------
# MAIN GAME


def main():
    """
    Main game function.
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Frisbee Hero")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 28)

    #------------------------------------------
    # GAME STATE VARIABLES

    running = True
    started = False
    game_over = False
    deathscreen_active = False
    death_time = 0

    score = 0
    level = 1
    enemy_direction = 1
    multishot_active = False
    piercing_active = False
    message_to_player = f"Click anywhere to start level {level}"

    #------------------------------------------
    # LOAD GAME OBJECTS

    background = create_background()
    deathscreen = load_scaled_image("deathscreen.png", WIDTH, HEIGHT)
    scoreboard_image = load_scaled_image(
        "scoreboard.png", SCOREBOARD_WIDTH, SCOREBOARD_HEIGHT)
    player = create_player()
    enemies = create_enemy_wave(level)
    frisbee_image = load_scaled_image("frisbee.png", 20, 40)
    powerup_images = {
        "dropped": load_scaled_image("dropped.png", DROPPED_SIZE, DROPPED_SIZE),
        "trophy": load_scaled_image("trophy.png", TROPHY_SIZE, TROPHY_SIZE),}
    frisbees = []
    powerups = []

    #------------------------------------------
    # MAIN LOOP

    while running:
        #------------------------------------------
        # 1. EVENT HANDLING

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and not game_over:

                # cheat code to move to the next level
                if event.key == pygame.K_KP_PLUS or event.unicode == "+":
                    level += 1
                    background = create_background()
                    enemies = create_enemy_wave(level)
                    frisbees = []
                    powerups = []
                    enemy_direction = 1
                    multishot_active = False
                    piercing_active = False
                    started = False
                    player["throw_timer"] = 0
                    message_to_player = f"Level {level} ready! Click anywhere to start"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not started and not game_over:
                    started = True
                    message_to_player = f"Take out all them Cougars"
                elif started and not game_over:
                    throw_player_frisbee(player,frisbee_image,frisbees,event.pos,multishot_active,piercing_active,)

        keys = pygame.key.get_pressed()

        #------------------------------------------
        # 2. GAME LOGIC

        if started and not game_over:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player["pos"].x -= PLAYER_SPEED

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player["pos"].x += PLAYER_SPEED

            half_width = player["image"].get_width() // 2
            if player["pos"].x < half_width:
                player["pos"].x = half_width
            if player["pos"].x > WIDTH - half_width:
                player["pos"].x = WIDTH - half_width

            frisbees = update_player_frisbees(frisbees)
            powerups = update_powerups(powerups)
            enemy_direction = update_enemies(enemies, enemy_direction, level)
            frisbees, enemies, powerups, score = handle_frisbee_enemy_collisions(
                frisbees, enemies, powerups, score, powerup_images)
            frisbees, powerups, multishot_active, piercing_active = handle_frisbee_powerup_collisions(
                frisbees, powerups, multishot_active, piercing_active)

            if player_hit_enemy(player, enemies):
                game_over = True
                deathscreen_active = False
                death_time = pygame.time.get_ticks()
                player["is_alive"] = False
                player["throw_timer"] = 0
                message_to_player = "Them Cougars got ya!."

            if enemy_reached_bottom(enemies):
                game_over = True
                deathscreen_active = False
                death_time = pygame.time.get_ticks()
                player["is_alive"] = False
                player["throw_timer"] = 0
                message_to_player = "Game Over! Them nasty Cougars Won."

            if len(enemies) == 0:
                level += 1
                background = create_background()
                enemies = create_enemy_wave(level)
                frisbees = []
                powerups = []
                enemy_direction = 1
                multishot_active = False
                piercing_active = False
                started = False
                player["throw_timer"] = 0
                message_to_player = f"Level {level} ready! Click anywhere to start"

        # NOTE: This delayed death screen timing is a little beyond normal
        # CS 1400 work. AI was used to help get this section implemented.
        if game_over and not deathscreen_active:
            if pygame.time.get_ticks() - death_time >= DEATHSCREEN_DELAY_MS:
                deathscreen_active = True

        update_player_appearance(player)

        #------------------------------------------
        # 3. DRAW

        if deathscreen_active:
            screen.blit(deathscreen, (0, 0))
        else:
            draw_game(screen, background, scoreboard_image, player, enemies, frisbees, powerups, font, score, level, message_to_player, multishot_active, piercing_active)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


main()
