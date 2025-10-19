import pygame
import sys
import random
import os 

# Game settings
WIDTH, HEIGHT = 800, 600
FPS = 60

# Brick Breaker config
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_WIDTH = WIDTH // BRICK_COLS
BRICK_HEIGHT = 30
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 20
BALL_RADIUS = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (30, 30, 40)
BRICK_COLORS = [(255, 99, 71), (255, 215, 0), (50, 205, 50), (70, 130, 180), (138, 43, 226), (255, 105, 180)]
# Human character colors
SKIN_COLOR = (255, 220, 177)  # Skin tone
SHIRT_COLOR = (50, 150, 255)  # Blue shirt
PANTS_COLOR = (100, 50, 150)  # Purple pants
HAIR_COLOR = (139, 69, 19)    # Brown hair
SHOE_COLOR = (101, 67, 33)    # Brown shoes
PROJECTILE_COLOR = (255, 255, 0)  # Yellow projectiles
# Dinosaur boss colors
DINO_BODY_COLOR = (34, 139, 34)    # Forest green
DINO_BELLY_COLOR = (144, 238, 144)  # Light green
DINO_SPOTS_COLOR = (0, 100, 0)      # Dark green spots
DINO_EYE_COLOR = (255, 0, 0)        # Red eyes
DINO_TEETH_COLOR = (255, 255, 255)  # White teeth

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Human vs Dinosaur - Brick Shooter!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Segoe UI", 32, bold=True)
small_font = pygame.font.SysFont("Segoe UI", 18, bold=True)

base_path = os.path.dirname(__file__)

# Background music
music_path = os.path.join(base_path, "bg.mp3.mp3")
if os.path.exists(music_path):
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.1)

# Game Over sound
gameover_path = os.path.join(base_path, "gameover.wav.mp3")
if os.path.exists(gameover_path):
    gameover_sound = pygame.mixer.Sound(gameover_path)
else:
    gameover_sound = None
    
win_path = os.path.join(base_path, "win.wav.mp3")
if os.path.exists(win_path):
    win_sound = pygame.mixer.Sound(win_path)
else:
    win_sound = None    

# Brick Hit sound
brickshooting_path = os.path.join(base_path, "brickshooting.wav.wav")
brickhit_path = os.path.join(base_path, "brickhit.wav.wav")
selected_hit_path = None
if os.path.exists(brickshooting_path):
    selected_hit_path = brickshooting_path
elif os.path.exists(brickhit_path):
    selected_hit_path = brickhit_path

if selected_hit_path:
    brickhit_sound = pygame.mixer.Sound(selected_hit_path)
    brickhit_sound.set_volume(1.0)
else:
    brickhit_sound = None

# Powerup sounds
hit_sound_path = os.path.join(base_path, "hit.wav.mp3")
powerup_sound_path = os.path.join(base_path, "powerup.wav.mp3")
boss_sound_path = os.path.join(base_path, "bosshit.wav.mp3")

hit_sound = pygame.mixer.Sound(hit_sound_path) if os.path.exists(hit_sound_path) else None
powerup_sound = pygame.mixer.Sound(powerup_sound_path) if os.path.exists(powerup_sound_path) else None
boss_hit_sound = pygame.mixer.Sound(boss_sound_path) if os.path.exists(boss_sound_path) else None

# Background
bg_path = os.path.join(base_path, "background.jpg")
if os.path.exists(bg_path):
    bg_image = pygame.image.load(bg_path)
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
else:
    bg_image = None

# Level system
LEVEL = 1
FINAL_LEVEL = 5
BOSS_HP = 500

# Stars for background animation
STAR_COUNT = 80
stars = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), "speed": random.randint(1, 3)} for _ in range(STAR_COUNT)]
sparks = []
powerups = []
boss_projectiles = []
bricks = []  # moved global for boss shields
projectiles = []  # player projectiles

def draw_background(surface):
    if bg_image:
        surface.blit(bg_image, (0, 0))
    else:
        surface.fill(BG_COLOR)
        for star in stars:
            pygame.draw.circle(surface, WHITE, (star["x"], star["y"]), 2)
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

def draw_text(surface, text, font, color, x, y, center=True):
    txt = font.render(text, True, color)
    rect = txt.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    outline_color = BLACK if color != BLACK else WHITE
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        shadow = font.render(text, True, outline_color)
        surface.blit(shadow, rect.move(dx, dy))
    surface.blit(txt, rect)

class Character:
    def __init__(self, level=1):
        # Adjust character size based on difficulty (human proportions)
        if level == 1:  # Level 1 - Easy: larger hitbox
            width = 24
            height = 45
        elif level == 2:  # Level 2 - Medium: normal size
            width = 22
            height = 42
        elif level == 3:  # Level 3 - Hard: smaller size
            width = 20
            height = 40
        elif level == 4:  # Level 4 - Very Hard: much smaller
            width = 18
            height = 37
        else:  # Level 5 - Boss Fight: smallest hitbox
            width = 16
            height = 35
        
        self.rect = pygame.Rect(WIDTH//2 - width//2, HEIGHT - height - 10, width, height)
        self.speed = 10
        self.last_direction = 0  # Track movement direction for shooting angle
        self.shoot_timer = 0  # Timer for automatic firing rate
        self.animation_frame = 0  # For walking animation
        self.firing_multiplier = 1  # Default firing multiplier
        
    def move(self, dx):
        self.rect.x += dx * self.speed
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        # Track movement direction for angled shots
        if dx != 0:
            self.last_direction = dx
            self.animation_frame += 1  # Animate when moving
        
    def update(self):
        self.shoot_timer += 1
        # Slow down animation when not moving
        if self.animation_frame > 0:
            self.animation_frame += 0.2
            
    def can_shoot(self):
        # Allow shooting every 3 frames for rapid fire, adjust by firing_multiplier
        return self.shoot_timer >= max(1, 3 // self.firing_multiplier)
        
    def shoot(self, spread_shot=False):
        if self.can_shoot():
            self.shoot_timer = 0
            return True
        return False
        
    def draw(self, surface):
        center_x = self.rect.centerx
        bottom_y = self.rect.bottom
        
        # Character proportions
        head_radius = 8
        body_width = 12
        body_height = 16
        leg_width = 4
        leg_height = 10
        arm_width = 3
        arm_length = 12
        
        # Draw legs with simple walking animation
        import math
        walk_offset = int(math.sin(self.animation_frame * 0.3) * 2) if hasattr(self, 'animation_frame') else 0
        
        left_leg_x = center_x - 4
        right_leg_x = center_x + 4
        leg_y = bottom_y - leg_height
        
        # Animated leg positions
        left_leg_y = leg_y + walk_offset
        right_leg_y = leg_y - walk_offset
        
        pygame.draw.rect(surface, PANTS_COLOR, (left_leg_x - leg_width//2, left_leg_y, leg_width, leg_height - abs(walk_offset)))
        pygame.draw.rect(surface, PANTS_COLOR, (right_leg_x - leg_width//2, right_leg_y, leg_width, leg_height - abs(walk_offset)))
        
        # Draw shoes with animation
        pygame.draw.ellipse(surface, SHOE_COLOR, (left_leg_x - 3, bottom_y - 3 + walk_offset//2, 6, 4))
        pygame.draw.ellipse(surface, SHOE_COLOR, (right_leg_x - 3, bottom_y - 3 - walk_offset//2, 6, 4))
        
        # Draw body (torso)
        body_y = leg_y - body_height
        pygame.draw.rect(surface, SHIRT_COLOR, (center_x - body_width//2, body_y, body_width, body_height), border_radius=2)
        
        # Draw arms
        left_arm_x = center_x - body_width//2 - arm_width//2
        right_arm_x = center_x + body_width//2 + arm_width//2
        arm_y = body_y + 3
        
        # Arms holding gun upward
        pygame.draw.rect(surface, SKIN_COLOR, (left_arm_x - arm_width//2, arm_y, arm_width, arm_length))
        pygame.draw.rect(surface, SKIN_COLOR, (right_arm_x - arm_width//2, arm_y, arm_width, arm_length))
        
        # Draw head
        head_y = body_y - head_radius
        pygame.draw.circle(surface, SKIN_COLOR, (center_x, head_y), head_radius)
        
        # Draw hair
        pygame.draw.arc(surface, HAIR_COLOR, (center_x - head_radius, head_y - head_radius, head_radius * 2, head_radius * 2), 0, 3.14159, 3)
        
        # Draw face
        eye_y = head_y - 2
        pygame.draw.circle(surface, BLACK, (center_x - 3, eye_y), 1)  # Left eye
        pygame.draw.circle(surface, BLACK, (center_x + 3, eye_y), 1)  # Right eye
        
        # Draw mouth
        mouth_y = head_y + 2
        pygame.draw.arc(surface, BLACK, (center_x - 2, mouth_y - 1, 4, 3), 0, 3.14159, 1)
        
        # Draw gun
        gun_x = center_x
        gun_y = body_y - 5
        gun_rect = pygame.Rect(gun_x - 2, gun_y - 8, 4, 12)
        pygame.draw.rect(surface, BLACK, gun_rect)
        
        # Gun barrel
        pygame.draw.rect(surface, (64, 64, 64), (gun_x - 1, gun_y - 10, 2, 4))
        
        # Muzzle flash effect when shooting
        if hasattr(self, 'shoot_timer') and self.shoot_timer < 2:
            flash_colors = [(255, 255, 0), (255, 200, 0), (255, 150, 0)]
            for i, color in enumerate(flash_colors):
                flash_size = (3 - i) * 2
                pygame.draw.circle(surface, color, (gun_x, gun_y - 10), flash_size)

class Projectile:
    def __init__(self, x, y, level, angle=0, spread_type="normal"):
        self.x = x
        self.y = y
        self.angle = angle  # Shooting angle in degrees
        self.spread_type = spread_type
        self.set_speed(level)
        self.width = 6
        self.height = 12
        self.active = True
        
        # Calculate velocity components based on angle
        import math
        angle_rad = math.radians(angle)
        self.dx = math.sin(angle_rad) * self.speed * 0.3  # Horizontal component
        self.dy = -self.speed  # Vertical component (always upward)
        
    def set_speed(self, level):
        # Projectile speed based on difficulty
        if level == 1:  # Easy - slower projectiles, easier to aim
            self.speed = 10
        elif level == 2:  # Medium - normal speed
            self.speed = 14
        else:  # Hard - faster projectiles
            self.speed = 18
            
    def update(self, bricks, boss=None):
        # Update position with directional movement
        self.x += self.dx
        self.y += self.dy
        score = 0
        cleared = False
        
        # Remove if off screen (any direction)
        if (self.y < -self.height or self.x < -self.width or 
            self.x > WIDTH + self.width):
            self.active = False
            return score, cleared
            
        # Check brick collisions
        projectile_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        hit_index = self.collide_bricks(bricks, projectile_rect)
        if hit_index is not None:
            brick = bricks[hit_index]
            brick["hp"] -= 1
            self.active = False
            score += 10
            if brickhit_sound:
                brickhit_sound.play()
            if brick["hp"] <= 0:
                bricks.pop(hit_index)
                spawn_powerup(brick["rect"].centerx, brick["rect"].centery, LEVEL)
                make_sparks(brick["rect"].centerx, brick["rect"].centery)
            if not bricks:
                cleared = True
                
        # Check boss collision
        if boss and boss["rect"].colliderect(projectile_rect):
            boss["hp"] -= 1
            self.active = False
            score += 50
            if boss_hit_sound:
                boss_hit_sound.play()
            if boss["hp"] <= 0:
                cleared = True
                
        return score, cleared
        
    def collide_bricks(self, bricks, projectile_rect):
        for i, brick in enumerate(bricks):
            if brick["rect"].colliderect(projectile_rect):
                return i
        return None
        
    def draw(self, surface):
        # Draw projectile as a glowing bullet
        pygame.draw.ellipse(surface, PROJECTILE_COLOR, 
                          (self.x - self.width//2, self.y - self.height//2, self.width, self.height))
        # Add glow effect
        pygame.draw.ellipse(surface, WHITE, 
                          (self.x - self.width//4, self.y - self.height//4, self.width//2, self.height//2))

# Global projectiles list
projectiles = []

def spawn_powerup(x, y, level=1):
    # Adjust powerup spawn rate based on difficulty
    if level == 1:  # Easy - more powerups
        spawn_chance = 0.4
    elif level == 2:  # Medium - normal powerups
        spawn_chance = 0.25
    else:  # Hard - fewer powerups
        spawn_chance = 0.15
    
    if random.random() < spawn_chance:
        p_type = random.choice(["expand", "shrink", "slow", "fast", "score"])
        rect = pygame.Rect(x-10, y-10, 20, 20)
        # Slower fall speed and slight horizontal drift for better catchability
        dx = random.uniform(-1, 1)  # Small horizontal drift
        dy = random.uniform(1.5, 2.5)  # Slower, variable fall speed
        powerups.append({"rect": rect, "type": p_type, "dx": dx, "dy": dy})

def apply_powerup(character, p_type):
    global score
    # Set firing multiplier based on powerup type/color
    if p_type == "expand":
        character.rect.width = min(character.rect.width + 30, 180)
        character.firing_multiplier = 2  # Green particle
    elif p_type == "shrink":
        character.rect.width = max(character.rect.width - 20, 40)
        character.firing_multiplier = 1  # Red particle
    elif p_type == "slow":
        # Increase projectile spread (more bullets per shot)
        # This powerup now creates wider spread shots
        character.firing_multiplier = 3  # Blue particle
    elif p_type == "fast":
        # Increase movement speed
        character.speed = min(character.speed + 3, 18)
    elif p_type == "score":
        score += 100
    if powerup_sound:
        powerup_sound.play()

def make_sparks(x, y):
    for _ in range(20):
        sparks.append({
            "x": x, "y": y,
            "dx": random.uniform(-4, 4), "dy": random.uniform(0.5, 1.5),
            "life": random.randint(15, 25), "color": random.choice(BRICK_COLORS)
        })

def draw_sparks(surface):
    for spark in sparks[:]:
        spark["x"] += spark["dx"]
        spark["y"] += spark["dy"]
        spark["dy"] += 0.05
        spark["life"] -= 1
        if spark["life"] <= 0:
            sparks.remove(spark)
            continue
        alpha = max(50, min(255, spark["life"] * 12))
        radius = max(1, spark["life"] // 3)
        particle_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        r, g, b = spark.get("color", (255, 255, 100))
        pygame.draw.circle(particle_surface, (r, g, b, alpha), (radius, radius), radius)
        surface.blit(particle_surface, (spark["x"]-radius, spark["y"]-radius))

def create_bricks(level):
    bricks = []
    if level == 1:  # Level 1 - Easy: 3 rows, all 1-hit bricks
        rows = 3
        for row in range(rows):
            for col in range(BRICK_COLS):
                x = col * BRICK_WIDTH + 2
                y = row * BRICK_HEIGHT + 2 + 60
                rect = pygame.Rect(x, y, BRICK_WIDTH - 4, BRICK_HEIGHT - 4)
                bricks.append({"rect": rect, "hp": 1})
    elif level == 2:  # Level 2 - Medium: 4 rows, some 2-hit bricks
        rows = 4
        for row in range(rows):
            for col in range(BRICK_COLS):
                x = col * BRICK_WIDTH + 2
                y = row * BRICK_HEIGHT + 2 + 60
                rect = pygame.Rect(x, y, BRICK_WIDTH - 4, BRICK_HEIGHT - 4)
                hp = 2 if row < 2 else 1
                bricks.append({"rect": rect, "hp": hp})
    elif level == 3:  # Level 3 - Hard: 5 rows, more 2-hit bricks
        rows = 5
        for row in range(rows):
            for col in range(BRICK_COLS):
                x = col * BRICK_WIDTH + 2
                y = row * BRICK_HEIGHT + 2 + 60
                rect = pygame.Rect(x, y, BRICK_WIDTH - 4, BRICK_HEIGHT - 4)
                hp = 2 if row < 3 else 1
                bricks.append({"rect": rect, "hp": hp})
    elif level == 4:  # Level 4 - Very Hard: 6 rows, many 3-hit bricks
        rows = 6
    for row in range(rows):
        for col in range(BRICK_COLS):
            x = col * BRICK_WIDTH + 2
            y = row * BRICK_HEIGHT + 2 + 60
            rect = pygame.Rect(x, y, BRICK_WIDTH - 4, BRICK_HEIGHT - 4)
            if row < 2:
                hp = 3  # Top 2 rows are 3-hit bricks
            elif row < 4:
                hp = 2  # Next 2 rows are 2-hit bricks
            else:
                hp = 1  # Bottom rows are 1-hit bricks
            bricks.append({"rect": rect, "hp": hp})
    else:
        # Level 5 goes to boss fight
        return bricks
    return bricks

def draw_bricks(surface, bricks):
    for i, brick in enumerate(bricks):
        # Base color from brick colors array
        base_color = BRICK_COLORS[i // BRICK_COLS % len(BRICK_COLORS)]
        
        # Modify color based on HP (darker = stronger)
        hp = brick["hp"]
        if hp == 1:
            color = base_color  # Normal brightness
        elif hp == 2:
            # Darker for 2-hit bricks
            color = tuple(max(0, c - 50) for c in base_color)
        else:  # hp >= 3
            # Much darker for 3+ hit bricks
            color = tuple(max(0, c - 100) for c in base_color)
            
        pygame.draw.rect(surface, color, brick["rect"], border_radius=6)
        
        # Draw HP indicator
        if hp > 1:
            center_x = brick["rect"].centerx
            center_y = brick["rect"].centery
            draw_text(surface, str(hp), small_font, WHITE, center_x, center_y)

def create_boss():
    rect = pygame.Rect(WIDTH//2 - 150, 100, 300, 80)
    # Boss fight for Level 5 with full BOSS_HP
    return {"rect": rect, "hp": BOSS_HP, "dir": 4, "phase": 1, "max_hp": BOSS_HP}

def draw_boss(surface, boss):
    if boss:
        rect = boss["rect"]
        center_x = rect.centerx
        center_y = rect.centery
        
        # Dinosaur proportions
        head_width = 80
        head_height = 60
        body_width = rect.width
        body_height = rect.height
        
        # Draw dinosaur body (main torso)
        pygame.draw.ellipse(surface, DINO_BODY_COLOR, rect, width=0)
        
        # Draw belly
        belly_rect = pygame.Rect(rect.left + 20, rect.top + 15, rect.width - 40, rect.height - 25)
        pygame.draw.ellipse(surface, DINO_BELLY_COLOR, belly_rect, width=0)
        
        # Draw dinosaur head (left side)
        head_x = rect.left - 40
        head_y = rect.top + 10
        head_rect = pygame.Rect(head_x, head_y, head_width, head_height)
        pygame.draw.ellipse(surface, DINO_BODY_COLOR, head_rect, width=0)
        
        # Draw dinosaur snout
        snout_rect = pygame.Rect(head_x - 25, head_y + 20, 30, 20)
        pygame.draw.ellipse(surface, DINO_BODY_COLOR, snout_rect, width=0)
        
        # Draw dinosaur eye
        eye_x = head_x + 15
        eye_y = head_y + 15
        pygame.draw.circle(surface, WHITE, (eye_x, eye_y), 8)
        pygame.draw.circle(surface, DINO_EYE_COLOR, (eye_x, eye_y), 5)
        
        # Draw teeth
        for i in range(3):
            tooth_x = head_x - 20 + i * 8
            tooth_y = head_y + 35
            pygame.draw.polygon(surface, DINO_TEETH_COLOR, 
                              [(tooth_x, tooth_y), (tooth_x + 3, tooth_y - 8), (tooth_x + 6, tooth_y)])
        
        # Draw dinosaur tail (right side)
        tail_points = [
            (rect.right, rect.centery - 10),
            (rect.right + 60, rect.centery - 5),
            (rect.right + 80, rect.centery + 10),
            (rect.right + 60, rect.centery + 15),
            (rect.right, rect.centery + 10)
        ]
        pygame.draw.polygon(surface, DINO_BODY_COLOR, tail_points)
        
        # Draw legs
        leg_width = 15
        leg_height = 25
        leg_y = rect.bottom
        
        # Front legs
        front_leg1_x = rect.left + 30
        front_leg2_x = rect.left + 60
        pygame.draw.rect(surface, DINO_BODY_COLOR, (front_leg1_x, leg_y, leg_width, leg_height))
        pygame.draw.rect(surface, DINO_BODY_COLOR, (front_leg2_x, leg_y, leg_width, leg_height))
        
        # Back legs (bigger)
        back_leg1_x = rect.right - 60
        back_leg2_x = rect.right - 30
        pygame.draw.rect(surface, DINO_BODY_COLOR, (back_leg1_x, leg_y, leg_width + 5, leg_height))
        pygame.draw.rect(surface, DINO_BODY_COLOR, (back_leg2_x, leg_y, leg_width + 5, leg_height))
        
        # Draw spots on dinosaur
        spots = [
            (rect.left + 50, rect.top + 20),
            (rect.left + 120, rect.top + 30),
            (rect.left + 200, rect.top + 25),
            (rect.left + 80, rect.top + 50),
            (rect.left + 180, rect.top + 55)
        ]
        for spot_x, spot_y in spots:
            if rect.left <= spot_x <= rect.right and rect.top <= spot_y <= rect.bottom:
                pygame.draw.circle(surface, DINO_SPOTS_COLOR, (spot_x, spot_y), 8)
        
        # Draw HP bar
        draw_text(surface, f"Dinosaur Boss HP: {boss['hp']}", small_font, WHITE, WIDTH//2, rect.bottom + 40)

def update_boss(boss):
    max_hp = boss["max_hp"]
    
    # Phase changes based on HP percentage
    if boss["hp"] <= max_hp * 0.25 and boss["phase"] < 3:
        boss["phase"] = 3
        boss["dir"] = 8  # Faster movement in final phase
    elif boss["hp"] <= max_hp * 0.5 and boss["phase"] < 2:
        boss["phase"] = 2
        boss["dir"] = 6  # Increased speed in phase 2

    # Move boss
    boss["rect"].x += boss["dir"]
    if boss["rect"].left <= 0 or boss["rect"].right >= WIDTH:
        boss["dir"] *= -1

    # Increased fire rate per phase for hard difficulty
    if boss["phase"] == 1:
        fire_rate = 0.03
    elif boss["phase"] == 2:
        fire_rate = 0.06
    else:
        fire_rate = 0.1  # Much more aggressive in final phase

    if random.random() < fire_rate:
        # Multiple projectiles in later phases
        if boss["phase"] == 3:
            # Fire 3 projectiles in final phase
            for offset in [-20, 0, 20]:
                proj = pygame.Rect(boss["rect"].centerx + offset - 5, boss["rect"].bottom, 10, 20)
                boss_projectiles.append(proj)
        elif boss["phase"] == 2:
            # Fire 2 projectiles in phase 2
            for offset in [-10, 10]:
                proj = pygame.Rect(boss["rect"].centerx + offset - 5, boss["rect"].bottom, 10, 20)
                boss_projectiles.append(proj)
        else:
            # Single projectile in phase 1
            proj = pygame.Rect(boss["rect"].centerx - 5, boss["rect"].bottom, 10, 20)
            boss_projectiles.append(proj)

    # More frequent shield spawning in final phase
    if boss["phase"] == 3 and random.random() < 0.02:
        shield_x = random.randint(0, BRICK_COLS - 1) * BRICK_WIDTH + 2
        shield_y = random.randint(2, 4) * BRICK_HEIGHT + 60
        shield_rect = pygame.Rect(shield_x, shield_y, BRICK_WIDTH - 4, BRICK_HEIGHT - 4)
        bricks.append({"rect": shield_rect, "hp": 4})  # Stronger shields

def draw_projectiles(surface):
    for proj in boss_projectiles:
        # Draw dinosaur fireballs
        center_x = proj.centerx
        center_y = proj.centery
        
        # Outer fire effect
        pygame.draw.circle(surface, (255, 100, 0), (center_x, center_y), 8)  # Orange outer
        pygame.draw.circle(surface, (255, 200, 0), (center_x, center_y), 5)  # Yellow middle
        pygame.draw.circle(surface, (255, 255, 100), (center_x, center_y), 2)  # Bright center

def update_projectiles(character):
    global game_over
    for proj in boss_projectiles[:]:
        proj.y += 7  # Faster projectiles for hard difficulty
        if proj.colliderect(character.rect):
            game_over = True
            if hit_sound:
                hit_sound.play()
        if proj.top > HEIGHT:
            boss_projectiles.remove(proj)

def main():
    global LEVEL, score, game_over, bricks, projectiles
    character = Character(LEVEL)
    bricks = create_bricks(LEVEL)
    boss = None
    score = 0
    running = True
    game_over = False
    win = False
    gameover_sound_played = False
    while running:
        draw_background(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    # Shoot single normal projectile
                    if character.shoot():
                        proj = Projectile(character.rect.centerx, character.rect.top, LEVEL, 0)
                        projectiles.append(proj)
                if event.key == pygame.K_r and game_over:
                    LEVEL = 1
                    character = Character(LEVEL)
                    bricks = create_bricks(LEVEL)
                    boss = None
                    score = 0
                    game_over = False
                    win = False
                    gameover_sound_played = False
                    powerups.clear()
                    boss_projectiles.clear()
                    projectiles.clear()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: character.move(-1)
        if keys[pygame.K_RIGHT]: character.move(1)
        
        # Normal rapid fire when holding space
        if keys[pygame.K_SPACE] and not game_over:
            if character.shoot():
                # Single straight shot
                proj = Projectile(character.rect.centerx, character.rect.top, LEVEL, 0)
                projectiles.append(proj)
        if not game_over:
            character.update()
            # Update projectiles
            cleared = False  # Ensure cleared is always defined
            for proj in projectiles[:]:
                s, cleared = proj.update(bricks, boss)
                score += s
                if not proj.active:
                    projectiles.remove(proj)
                if cleared:
                    break
            for p in powerups[:]:
                # Update powerup position with both horizontal and vertical movement
                p["rect"].x += p["dx"]
                p["rect"].y += p["dy"]
                
                # Keep powerups within screen bounds horizontally
                if p["rect"].left < 0 or p["rect"].right > WIDTH:
                    p["dx"] *= -0.5  # Bounce back with reduced speed
                    p["rect"].x = max(0, min(WIDTH - p["rect"].width, p["rect"].x))
                
                if p["rect"].colliderect(character.rect):
                    apply_powerup(character, p["type"])
                    powerups.remove(p)
                elif p["rect"].top > HEIGHT:
                    powerups.remove(p)
            if boss:
                update_boss(boss)
                update_projectiles(character)
                
        # Check for level completion
        if cleared:
            LEVEL += 1
            if LEVEL == 5:  # Boss fight at level 5
                boss = create_boss()
                bricks = []
                character = Character(LEVEL)
            elif LEVEL <= FINAL_LEVEL:
                bricks = create_bricks(LEVEL)
                character = Character(LEVEL)
                boss = None

            if LEVEL > FINAL_LEVEL:
                win = True
                game_over = True

            if win_sound:
                win_sound.play()

            # Play game over sound once when the game ends
            if game_over and not gameover_sound_played and gameover_sound:
                gameover_sound.play()
                gameover_sound_played = True

            # Clear projectiles when advancing level
            projectiles.clear()
        character.draw(screen)
        
        # Draw projectiles
        for proj in projectiles:
            proj.draw(screen)
        draw_bricks(screen, bricks)
        for p in powerups:
            color = (0,255,0) if p["type"] in ["expand","slow","score"] else (255,0,0)
            pygame.draw.rect(screen, color, p["rect"])
        draw_sparks(screen)
        draw_boss(screen, boss)
        draw_projectiles(screen)
        draw_text(screen, f"Score: {score}", small_font, WHITE, 80, 30, center=False)
        # Display level with difficulty indicator
        difficulty_names = {
            1: "Level 1 (Easy)",
            2: "Level 2 (Medium)", 
            3: "Level 3 (Hard)",
            4: "Level 4 (Very Hard)",
            5: "Level 5 (Dinosaur Boss)"
        }
        level_text = difficulty_names.get(LEVEL, f"Level: {LEVEL}")
        draw_text(screen, level_text, small_font, WHITE, WIDTH - 150, 30, center=False)
        if not game_over:
            draw_text(screen, "Hold SPACE for rapid fire! Defeat the Dinosaur Boss!", small_font, WHITE, WIDTH//2, HEIGHT-20)
        if game_over:
            if win:
                draw_text(screen, "You Win!", font, (50, 205, 50), WIDTH//2, HEIGHT//2 - 40)
            else:
                draw_text(screen, "Game Over", font, (255, 99, 71), WIDTH//2, HEIGHT//2 - 40)
                if not gameover_sound_played and gameover_sound:
                    gameover_sound.play()
                    gameover_sound_played = True
            draw_text(screen, f"Final Score: {score}", small_font, WHITE, WIDTH//2, HEIGHT//2)
            draw_text(screen, "Press R to Restart", small_font, WHITE, WIDTH//2, HEIGHT//2 + 40)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
