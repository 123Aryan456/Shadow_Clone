import pygame
import math
import random
import os
from pathlib import Path

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Self")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Load explosion frames
EXPLOSION_FRAMES = []
try:
    for i in range(8):
        frame = pygame.image.load(f"assets/explosion_{i}.png").convert_alpha()
        EXPLOSION_FRAMES.append(frame)
except Exception as e:
    # Create default explosion frames if loading fails
    for i in range(8):
        size = 64
        frame = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = int(size/2 * ((i+1)/8))
        pygame.draw.circle(frame, (255, 200, 50, 200), (size//2, size//2), radius)
        pygame.draw.circle(frame, (255, 100, 0, 200), (size//2, size//2), radius//2)
        EXPLOSION_FRAMES.append(frame)

# Load assets
def load_image(name, scale=1):
    try:
        image = pygame.image.load(os.path.join("assets", name))
        return pygame.transform.scale(image, 
                                   (image.get_width() * scale, 
                                    image.get_height() * scale))
    except:
        surface = pygame.Surface((30, 30))
        surface.fill(WHITE)
        return surface

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        self.image = load_image(f"{type}_powerup.png")
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 300  # 5 seconds at 60 FPS

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.lifetime = 30

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class AttackIndicator(pygame.sprite.Sprite):
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        self.lifetime = 30  # Half second at 60 FPS
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.update_position()
        
    def update(self):
        self.update_position()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
    
    def update_position(self):
        # Calculate direction from source to target
        dx = self.target.rect.centerx - self.source.rect.centerx
        dy = self.target.rect.centery - self.source.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))
        
        # Create arrow shape
        points = [
            (0, 0),      # Tip
            (-10, -5),   # Left wing
            (-7, 0),     # Left indent
            (-10, 5)     # Right wing
        ]
        
        # Rotate points
        rotated_points = []
        for x, y in points:
            rad = math.radians(-angle)
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            rotated_points.append((rx + self.source.rect.centerx, 
                                 ry + self.source.rect.centery))
        
        # Draw arrow
        self.image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        color = (255, 255, 0) if isinstance(self.source, Shadow) else (255, 0, 0)
        pygame.draw.polygon(self.image, color, rotated_points)
        self.rect = self.image.get_rect()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, angle=0):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        # Red for player, yellow for shadow
        self.image.fill(RED if direction == 1 else YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 7
        self.direction = direction
        self.angle = math.radians(angle)
        
    def update(self):
        # Move with angle
        self.rect.x += self.speed * self.direction * math.cos(self.angle)
        self.rect.y += self.speed * math.sin(self.angle)
        if self.rect.right < 0 or self.rect.left > WIDTH or \
           self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = load_image("player.png", 0.5)
        if self.original_image.get_width() == 30:  # If default surface was created
            self.original_image = pygame.Surface((30, 30))
            self.original_image.fill(WHITE)
        self.image = self.original_image.copy()  # Create a copy for rotation
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 4, HEIGHT // 2)
        self.speed = 5
        self.base_speed = 5
        self.angle = 0
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.projectiles = pygame.sprite.Group()
        self.speed_boost_timer = 0
        self.invulnerable_timer = 0
        self.dash_cooldown = 0
        self.dash_energy_cost = 30
        self.score = 0
        self.shield = 0
        self.damage_multiplier = 1
        self.level_progress = 0  # For tutorial progression
        self.upgrades = {
            "max_health": 0,
            "max_energy": 0,
            "speed": 0,
            "damage": 0
        }

    def update(self):
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.rect.x += dx
        self.rect.y += dy
        
        # Dash mechanic
        if keys[pygame.K_LSHIFT] and self.dash_cooldown <= 0 and self.energy >= self.dash_energy_cost:
            self.dash(dx, dy)
        
        # Shoot projectile
        if keys[pygame.K_SPACE] and self.energy >= 20:
            self.shoot()
            self.energy -= 20
            
        # Update timers and status effects
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed = self.base_speed

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            
        # Energy regeneration
        if self.energy < self.max_energy:
            self.energy += 0.5
            
        # Keep player on screen
        self.rect.clamp_ip(screen.get_rect())
        
        # Update projectiles
        self.projectiles.update()
        
        # Mouse-based rotation
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.rect.centerx
        dy = mouse_y - self.rect.centery
        self.angle = math.degrees(math.atan2(-dy, dx))
        
        # Rotate image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def dash(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        self.energy -= self.dash_energy_cost
        self.invulnerable_timer = 20
        self.dash_cooldown = 60
        # Dash in movement direction
        self.rect.x += dx * 5
        self.rect.y += dy * 5
        
    def shoot(self):
        if hasattr(self.game, 'sounds') and 'shoot' in self.game.sounds:
            self.game.sounds['shoot'].play()
        angles = [-10, 0, 10] if self.energy >= 60 else [0]
        for angle in angles:
            projectile = Projectile(self.rect.centerx, self.rect.centery, 1, angle)
            self.projectiles.add(projectile)

    def apply_powerup(self, type):
        if type == "health":
            self.health = min(self.max_health, self.health + 30)
        elif type == "energy":
            self.energy = self.max_energy
        elif type == "speed":
            self.speed = self.base_speed * 1.5
            self.speed_boost_timer = 180
        elif type == "shield":
            self.shield = 100
        elif type == "damage":
            self.damage_multiplier = 2

    def upgrade(self, stat):
        if self.upgrades[stat] < 5:  # Max 5 upgrades per stat
            self.upgrades[stat] += 1
            if stat == "max_health":
                self.max_health += 20
                self.health = self.max_health
            elif stat == "max_energy":
                self.max_energy += 20
                self.energy = self.max_energy
            elif stat == "speed":
                self.base_speed += 0.5
                self.speed = self.base_speed
            elif stat == "damage":
                self.damage_multiplier += 0.2

class Shadow(pygame.sprite.Sprite):
    def __init__(self, player, level):
        super().__init__()
        self.image = load_image("shadow.png", 0.5)
        if self.image.get_width() == 30:  # If default surface was created
            self.image = pygame.Surface((30, 30))
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH * 3 // 4, HEIGHT // 2)
        self.player = player
        self.speed = 4 + level * 0.5
        self.health = 100 + level * 20
        self.max_health = self.health
        self.projectiles = pygame.sprite.Group()
        self.shoot_delay = max(30 - level * 5, 10)
        self.shoot_timer = 0
        self.attack_pattern = 0
        self.pattern_timer = 0
        
    def update(self):
        self.pattern_timer += 1
        if self.pattern_timer >= 180:  # Change pattern every 3 seconds
            self.attack_pattern = (self.attack_pattern + 1) % 3
            self.pattern_timer = 0

        if self.attack_pattern == 0:
            self.mirror_movement()
        elif self.attack_pattern == 1:
            self.circle_player()
        else:
            self.aggressive_chase()
            
        # Shooting logic
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot()
            self.shoot_timer = 0
            
        self.projectiles.update()

    def mirror_movement(self):
        dx = (WIDTH - self.player.rect.centerx) - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def circle_player(self):
        angle = self.pattern_timer * 0.05
        center_x = self.player.rect.centerx
        center_y = self.player.rect.centery
        radius = 150
        self.rect.centerx = center_x + math.cos(angle) * radius
        self.rect.centery = center_y + math.sin(angle) * radius

    def aggressive_chase(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self.rect.x += (dx / dist) * (self.speed * 1.5)
            self.rect.y += (dy / dist) * (self.speed * 1.5)
        
    def shoot(self):
        # Create attack indicator before shooting
        self.game.indicators.add(AttackIndicator(self, self.player))
        
        if self.attack_pattern == 0:
            # Single shot
            projectile = Projectile(self.rect.centerx, self.rect.centery, -1)
            self.projectiles.add(projectile)
        elif self.attack_pattern == 1:
            # Spread shot
            for angle in range(-30, 31, 30):
                projectile = Projectile(self.rect.centerx, self.rect.centery, -1, angle)
                self.projectiles.add(projectile)
        else:
            # Aimed shot
            dx = self.player.rect.centerx - self.rect.centerx
            dy = self.player.rect.centery - self.rect.centery
            angle = math.degrees(math.atan2(dy, dx))
            projectile = Projectile(self.rect.centerx, self.rect.centery, -1, angle)
            self.projectiles.add(projectile)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = EXPLOSION_FRAMES
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.animation_speed = 2
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter >= self.animation_speed:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.index]

class Game:
    def __init__(self):
        # Initialize sprite groups first
        self.particles = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.indicators = pygame.sprite.Group()
        
        # Then initialize other attributes
        self.level = 1
        self.high_score = self.load_high_score()
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 74)
        self.clock = pygame.time.Clock()
        self.state = "menu"  # "menu", "playing", "paused", "game_over"
        
        # Finally call reset_level
        self.reset_level()
        self.tutorial_messages = [
            "Use WASD or Arrow Keys to move",
            "Left Click or SPACE to shoot",
            "SHIFT to dash",
            "Collect powerups to get stronger",
            "Defeat your shadow to progress"
        ]
        self.tutorial_index = 0
        self.show_tutorial = True
        
        # Initialize sound system
        if not os.path.exists("sounds"):
            os.makedirs("sounds")
            
        # Load sounds with error handling
        self.sounds = {}
        try:
            self.sounds = {
                'shoot': pygame.mixer.Sound('sounds/shoot.wav'),
                'hit': pygame.mixer.Sound('sounds/hit.wav'),
                'powerup': pygame.mixer.Sound('sounds/powerup.wav'),
                'explosion': pygame.mixer.Sound('sounds/explosion.wav')
            }
            
            # Set volume for sound effects
            for sound in self.sounds.values():
                sound.set_volume(0.3)  # 30% volume
                
            # Load and play background music
            pygame.mixer.music.load('sounds/background.wav')
            pygame.mixer.music.set_volume(0.5)  # 50% volume
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            
        except Exception as e:
            print(f"Error loading sounds: {e}")

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as file:
                return int(file.read())
        except:
            return 0

    def save_high_score(self):
        with open("highscore.txt", "w") as file:
            file.write(str(max(self.high_score, self.player.score)))

    def reset_level(self):
        # Clear all sprite groups
        self.all_sprites.empty()
        self.powerups.empty()
        self.particles.empty()
        
        # Create new instances
        self.player = Player()
        self.player.game = self
        self.shadow = Shadow(self.player, self.level)
        self.shadow.game = self
        
        # Get level configuration
        config = self.get_level_config()
        
        # Apply level configuration
        self.shadow.health = config["shadow_health"]
        self.shadow.max_health = config["shadow_health"]
        self.shadow.speed = config["shadow_speed"]
        self.game_time = config["time_limit"]
        
        # Add sprites to group
        self.all_sprites.add(self.player, self.shadow)
        
        # Reset time tracking
        self.start_time = pygame.time.get_ticks()

    def spawn_powerup(self):
        config = self.get_level_config()
        if random.random() < config["powerup_frequency"]:
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            type = random.choice(["health", "energy", "speed", "shield", "damage"])
            self.powerups.add(PowerUp(x, y, type))

    def create_particles(self, x, y, color, amount=5):
        for _ in range(amount):
            self.particles.add(Particle(x, y, color))

    def show_menu(self):
        screen.fill(BLACK)
        title = self.title_font.render("Shadow Self", True, WHITE)
        start_text = self.font.render("Press ENTER to Start", True, WHITE)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
        
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2))
        screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT*2//3))
        
        pygame.display.flip()

    def run(self):
        running = True
        
        while running:
            if self.state == "menu":
                self.show_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = "playing"
                            self.reset_level()
                            
            elif self.state == "playing":
                running = self.game_loop()
                
            elif self.state == "paused":
                self.show_pause_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.state = "playing"
                        if event.key == pygame.K_q:
                            running = False

            self.clock.tick(60)

        pygame.quit()

    def game_loop(self):
        # Move time tracking outside the loop
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.start_time) // 1000 if hasattr(self, 'start_time') else 0
        
        if not hasattr(self, 'start_time'):
            self.start_time = current_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = "paused"
                    return True
                # Progress tutorial on spacebar
                if event.key == pygame.K_SPACE and self.show_tutorial:
                    self.tutorial_index = min(self.tutorial_index + 1, len(self.tutorial_messages) - 1)
                if event.key == pygame.K_m:  # 'M' key toggles sound
                    self.toggle_sound()
        
        # Update
        self.all_sprites.update()
        self.powerups.update()
        self.particles.update()
        self.explosions.update()
        self.indicators.update()
        self.spawn_powerup()
        
        # Collision detection
        self.handle_collisions()
        
        # Calculate remaining time
        remaining_time = max(0, self.game_time - elapsed_time)
        
        # Draw
        self.draw_game(remaining_time)
        
        # Level completion check
        if self.shadow.health <= 0:
            self.level += 1
            self.player.score += 1000 * self.level
            # Show upgrade menu before resetting level
            if not self.show_upgrade_menu():
                return False
            self.reset_level()
            self.start_time = pygame.time.get_ticks()
            
            # Disable tutorial after first level
            if self.level > 1:
                self.show_tutorial = False
        
        # Game over check
        if self.player.health <= 0 or remaining_time <= 0:
            self.show_game_over()
            self.save_high_score()
            self.state = "menu"
            
        return True

    def handle_collisions(self):
        # Projectile collisions
        for projectile in self.player.projectiles:
            if pygame.sprite.collide_rect(projectile, self.shadow):
                if 'hit' in self.sounds:
                    self.sounds['hit'].play()
                damage = 10 * self.player.damage_multiplier
                self.shadow.health -= damage
                self.create_explosion(projectile.rect.centerx, projectile.rect.centery)
                self.create_particles(projectile.rect.centerx, projectile.rect.centery, RED, 10)
                self.create_screen_shake()
                projectile.kill()
                self.player.score += 50
                
        for projectile in self.shadow.projectiles:
            if pygame.sprite.collide_rect(projectile, self.player):
                if self.player.invulnerable_timer <= 0:
                    if self.player.shield > 0:
                        self.player.shield -= 5
                    else:
                        self.player.health -= 5
                    self.create_particles(projectile.rect.centerx, projectile.rect.centery, WHITE)
                projectile.kill()
        
        # Power-up collisions
        for powerup in pygame.sprite.spritecollide(self.player, self.powerups, True):
            if 'powerup' in self.sounds:
                self.sounds['powerup'].play()
            if powerup.type == "health":
                self.player.health = min(self.player.max_health, self.player.health + 30)
            elif powerup.type == "energy":
                self.player.energy = self.player.max_energy
            elif powerup.type == "speed":
                self.player.speed = self.player.base_speed * 1.5
                self.player.speed_boost_timer = 180
            self.create_particles(powerup.rect.centerx, powerup.rect.centery, BLUE)
            self.player.score += 100
        
        # Direct collision
        if pygame.sprite.collide_rect(self.player, self.shadow) and self.player.invulnerable_timer <= 0:
            self.player.health -= 1
            self.create_particles(self.player.rect.centerx, self.player.rect.centery, RED)

    def draw_game(self, remaining_time):
        # Create a temporary surface for screen shake
        temp_surface = pygame.Surface((WIDTH, HEIGHT))
        temp_surface.fill(BLACK)
        
        # Draw trails
        if hasattr(self.player, 'rect'):
            self.create_trail(self.player.rect.center, (100, 150, 255))
            if self.player.dash_cooldown > 40:
                for _ in range(5):
                    self.create_trail(self.player.rect.center, (200, 220, 255))
        
        # Draw all sprites
        self.all_sprites.draw(temp_surface)
        self.player.projectiles.draw(temp_surface)
        self.shadow.projectiles.draw(temp_surface)
        self.powerups.draw(temp_surface)
        self.particles.draw(temp_surface)
        self.explosions.draw(temp_surface)
        self.indicators.draw(temp_surface)
        
        # Draw health bars and HUD
        self.draw_health_bars(temp_surface)
        self.draw_hud(temp_surface, remaining_time)
        
        # Apply screen shake
        final_surface, offset = self.apply_screen_shake(temp_surface)
        screen.blit(final_surface, offset)
        
        pygame.display.flip()

    def draw_health_bars(self, surface):
        # Player health bar
        self.draw_health_bar(surface, self.player.rect.centerx, 
                            self.player.rect.top - 10,
                            self.player.health, self.player.max_health, GREEN)
        
        # Shadow health bar
        self.draw_health_bar(surface, self.shadow.rect.centerx,
                            self.shadow.rect.top - 10,
                            self.shadow.health, self.shadow.max_health, RED)

    def draw_health_bar(self, surface, x, y, health, max_health, color):
        bar_width = 50
        bar_height = 5
        fill = (health / max_health) * bar_width
        outline_rect = pygame.Rect(x - bar_width//2, y, bar_width, bar_height)
        fill_rect = pygame.Rect(x - bar_width//2, y, fill, bar_height)
        pygame.draw.rect(surface, color, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 1)

    def draw_hud(self, surface, remaining_time):
        # Time
        time_text = self.font.render(f"Time: {remaining_time}s", True, WHITE)
        surface.blit(time_text, (10, 10))
        
        # Score
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (WIDTH - 150, 10))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        surface.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 10))
        
        # Energy bar
        energy_width = 200
        energy_height = 20
        energy_fill = (self.player.energy / self.player.max_energy) * energy_width
        pygame.draw.rect(surface, BLUE, (10, HEIGHT - 30, energy_fill, energy_height))
        pygame.draw.rect(surface, WHITE, (10, HEIGHT - 30, energy_width, energy_height), 2)
        
        # Shield bar if active
        if self.player.shield > 0:
            shield_width = 200
            shield_height = 10
            shield_fill = (self.player.shield / 100) * shield_width
            pygame.draw.rect(surface, PURPLE, (10, HEIGHT - 50, shield_fill, shield_height))
            pygame.draw.rect(surface, WHITE, (10, HEIGHT - 50, shield_width, shield_height), 2)

        # Tutorial message
        if self.show_tutorial and self.level == 1:
            tutorial_text = self.font.render(
                self.tutorial_messages[self.tutorial_index], True, WHITE)
            surface.blit(tutorial_text, 
                        (WIDTH//2 - tutorial_text.get_width()//2, 50))

    def show_game_over(self):
        screen.fill(BLACK)
        game_over_text = self.title_font.render("Game Over!", True, WHITE)
        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        level_text = self.font.render(f"Final Level: {self.level}", True, WHITE)
        
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//3))
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
        screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT*2//3))
        
        pygame.display.flip()
        pygame.time.wait(2000)

    def show_pause_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))
        
        pause_text = self.title_font.render("PAUSED", True, WHITE)
        continue_text = self.font.render("Press P to Continue", True, WHITE)
        quit_text = self.font.render("Press Q to Quit", True, WHITE)
        
        screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//3))
        screen.blit(continue_text, (WIDTH//2 - continue_text.get_width()//2, HEIGHT//2))
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, HEIGHT*2//3))
        
        pygame.display.flip()

    def get_level_config(self):
        """Return configuration for current level"""
        if self.level == 1:  # Tutorial level
            return {
                "shadow_health": 50,
                "shadow_speed": 2,
                "shadow_damage": 3,
                "time_limit": 240,
                "powerup_frequency": 0.005
            }
        elif self.level == 2:
            return {
                "shadow_health": 100,
                "shadow_speed": 3,
                "shadow_damage": 5,
                "time_limit": 180,
                "powerup_frequency": 0.01
            }
        else:
            return {
                "shadow_health": 100 + (self.level - 2) * 30,
                "shadow_speed": 3 + (self.level - 2) * 0.3,
                "shadow_damage": 5 + (self.level - 2) * 1,
                "time_limit": max(120, 180 - (self.level - 2) * 10),
                "powerup_frequency": min(0.02, 0.01 + (self.level - 2) * 0.002)
            }

    def show_upgrade_menu(self):
        choosing = True
        while choosing:
            screen.fill(BLACK)
            
            title = self.title_font.render(f"Level {self.level} Complete!", True, WHITE)
            subtitle = self.font.render("Choose an upgrade:", True, WHITE)
            
            options = [
                f"Max Health (+20) [Level {self.player.upgrades['max_health']}/5]",
                f"Max Energy (+20) [Level {self.player.upgrades['max_energy']}/5]",
                f"Speed (+0.5) [Level {self.player.upgrades['speed']}/5]",
                f"Damage (+20%) [Level {self.player.upgrades['damage']}/5]"
            ]
            
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 200))
            
            for i, text in enumerate(options):
                color = WHITE if self.player.upgrades[list(self.player.upgrades.keys())[i]] < 5 else RED
                option_text = self.font.render(text, True, color)
                screen.blit(option_text, (WIDTH//2 - option_text.get_width()//2, 300 + i * 50))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        stat = list(self.player.upgrades.keys())[event.key - pygame.K_1]
                        if self.player.upgrades[stat] < 5:
                            self.player.upgrade(stat)
                            choosing = False
                            return True
        return True

    def create_screen_shake(self):
        self.screen_shake = 20  # Duration of shake
        self.shake_intensity = 5  # Maximum pixel offset

    def apply_screen_shake(self, surface):
        if hasattr(self, 'screen_shake') and self.screen_shake > 0:
            self.screen_shake -= 1
            intensity = self.shake_intensity * (self.screen_shake / 20)
            offset_x = random.randint(-int(intensity), int(intensity))
            offset_y = random.randint(-int(intensity), int(intensity))
            return surface.copy(), (offset_x, offset_y)
        return surface, (0, 0)

    def create_trail(self, pos, color):
        for _ in range(3):
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            particle = Particle(pos[0] + offset_x, pos[1] + offset_y, color)
            particle.velocity = [x * 0.5 for x in particle.velocity]
            self.particles.add(particle)

    def create_explosion(self, x, y):
        if 'explosion' in self.sounds:
            self.sounds['explosion'].play()
        self.explosions.add(Explosion(x, y))

    def set_volume(self, volume):
        """Set volume for all sounds (0.0 to 1.0)"""
        try:
            for sound in self.sounds.values():
                sound.set_volume(volume)
            pygame.mixer.music.set_volume(volume)
        except:
            pass

    def toggle_sound(self):
        """Toggle all game sounds on/off"""
        try:
            if pygame.mixer.music.get_volume() > 0:
                self.set_volume(0.0)
            else:
                self.set_volume(0.5)
        except:
            pass

def create_game_sprites():
    """Create and save all game sprites"""
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    # Color definitions for sprites
    SPRITE_COLORS = {
        'player': {
            'primary': (64, 190, 255),    # Bright blue
            'secondary': (0, 128, 255),    # Deep blue
            'glow': (150, 220, 255),      # Light blue glow
            'core': (255, 255, 255)       # White core
        },
        'shadow': {
            'primary': (255, 40, 40),     # Bright red
            'secondary': (200, 0, 0),     # Deep red
            'glow': (255, 100, 100),      # Light red glow
            'core': (255, 200, 200)       # Light red core
        }
    }
    
    def create_crystal(size, colors, points=5):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Create glow
        for radius in range(size//2, 0, -2):
            alpha = int(150 * (radius/(size/2)))
            pygame.draw.circle(surface, (*colors['glow'], alpha), (center, center), radius)
        
        # Create crystal shape
        crystal_points = []
        for i in range(points):
            angle = i * (2 * math.pi / points) - math.pi/2
            radius = size//2 - 4
            x = center + math.cos(angle) * radius
            y = center + math.sin(angle) * radius
            crystal_points.append((x, y))
            
            # Add inner points for star shape
            inner_angle = angle + math.pi/points
            inner_radius = size//4
            x = center + math.cos(inner_angle) * inner_radius
            y = center + math.sin(inner_angle) * inner_radius
            crystal_points.append((x, y))
        
        # Draw crystal
        pygame.draw.polygon(surface, colors['primary'], crystal_points)
        
        # Add core
        pygame.draw.circle(surface, colors['core'], (center, center), size//6)
        
        return surface
    
    def create_projectile(size, color):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        points = [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)]
        pygame.draw.polygon(surface, color['primary'], points)
        return surface
    
    def create_powerup(size, color):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Outer glow
        for radius in range(size//2, 0, -2):
            alpha = int(100 * (radius/(size/2)))
            pygame.draw.circle(surface, (*color['glow'], alpha), (center, center), radius)
            
        # Core
        pygame.draw.circle(surface, color['primary'], (center, center), size//4)
        
        return surface
    
    def create_explosion_frame(i, total_frames):
        size = 64
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        progress = i / total_frames
        center = size // 2
        
        # Draw explosion rays
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            length = size//2 * progress
            end_x = center + math.cos(rad) * length
            end_y = center + math.sin(rad) * length
            pygame.draw.line(surface, (255, 200, 50), 
                           (center, center), (end_x, end_y), 
                           max(1, int(3 * (1-progress))))
        
        # Core
        radius = int(size//4 * (1-progress))
        if radius > 0:
            pygame.draw.circle(surface, (255, 100, 0), (center, center), radius)
        
        return surface
    
    # Create and save all sprites
    try:
        # Main sprites
        pygame.image.save(create_crystal(64, SPRITE_COLORS['player']), "assets/player.png")
        pygame.image.save(create_crystal(64, SPRITE_COLORS['shadow']), "assets/shadow.png")
        
        # Projectiles
        pygame.image.save(create_projectile(32, SPRITE_COLORS['player']), "assets/player_projectile.png")
        pygame.image.save(create_projectile(32, SPRITE_COLORS['shadow']), "assets/shadow_projectile.png")
        
        # Powerups
        powerup_colors = {
            'health': {'primary': (0, 255, 0), 'glow': (150, 255, 150)},
            'energy': {'primary': (0, 200, 255), 'glow': (150, 220, 255)},
            'speed': {'primary': (255, 255, 0), 'glow': (255, 255, 150)},
            'shield': {'primary': (148, 0, 211), 'glow': (230, 130, 255)},
            'damage': {'primary': (255, 69, 0), 'glow': (255, 150, 50)}
        }
        
        for name, colors in powerup_colors.items():
            pygame.image.save(create_powerup(48, colors), f"assets/{name}_powerup.png")
        
        # Explosion frames
        for i in range(8):
            pygame.image.save(create_explosion_frame(i, 8), f"assets/explosion_{i}.png")
            
        print("Game sprites created successfully!")
        
    except Exception as e:
        print(f"Error creating sprites: {e}")

if __name__ == "__main__":
    game = Game()
    game.run()
