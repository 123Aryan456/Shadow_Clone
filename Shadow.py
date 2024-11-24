import pygame
import math
import random
from pygame import gfxdraw

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Self")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
PURPLE = (147, 0, 211)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Create more complex player shape
        size = 40
        self.original_image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(self.original_image, WHITE, [
            (size//2, 0), (size, size), (size//2, size*0.8), (0, size)
        ])
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 4, HEIGHT // 2)
        self.speed = 5
        self.angle = 0
        self.health = 100
        self.dash_cooldown = 0
        self.trail = []
        self.shield_active = False
        self.shield_cooldown = 0

    def dash(self):
        if self.dash_cooldown <= 0:
            self.speed = 15
            self.dash_cooldown = 60
            return True
        return False

    def update(self):
        # Store previous position for trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 10:
            self.trail.pop(0)

        keys = pygame.key.get_pressed()
        
        # Movement
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.rect.x += dx
        self.rect.y += dy
            
        # Dash ability
        if keys[pygame.K_SPACE]:
            if self.dash():
                for _ in range(20):
                    game.create_particles(self.rect.center, BLUE)

        # Shield ability
        if keys[pygame.K_LSHIFT] and self.shield_cooldown <= 0:
            self.shield_active = True
            self.shield_cooldown = 180

        # Update cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            if self.dash_cooldown == 0:
                self.speed = 5

        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
            if self.shield_cooldown == 0:
                self.shield_active = False
            
        # Keep player on screen
        self.rect.clamp_ip(screen.get_rect())
        
        # Rotate player
        self.angle += 2
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Shadow(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        size = 40
        self.original_image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(self.original_image, RED, [
            (size//2, 0), (size, size), (size//2, size*0.8), (0, size)
        ])
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH * 3 // 4, HEIGHT // 2)
        self.player = player
        self.speed = 4
        self.angle = 0
        self.trail = []
        self.attack_timer = 0
        
    def update(self):
        # Store previous position for trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 10:
            self.trail.pop(0)

        # Mirror player movements with slight delay
        dx = (WIDTH - self.player.rect.centerx) - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

        # Occasional attack burst
        self.attack_timer += 1
        if self.attack_timer >= 120:  # Attack every 2 seconds
            self.speed = 8
            game.create_particles(self.rect.center, RED)
            if self.attack_timer >= 150:
                self.speed = 4
                self.attack_timer = 0
            
        # Mirror player rotation
        self.angle = -self.player.angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Game:
    def __init__(self):
        self.player = Player()
        self.shadow = Shadow(self.player)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player, self.shadow)
        self.game_time = 180
        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.powerups = []
        self.powerup_timer = 180
        self.screen_shake = 0
        
    def create_particles(self, pos, color):
        for _ in range(5):
            particle = {
                'pos': list(pos),
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'timer': 20,
                'color': color,
                'size': random.randint(2, 4)
            }
            self.particles.append(particle)

    def spawn_powerup(self):
        x = random.randint(50, WIDTH-50)
        y = random.randint(50, HEIGHT-50)
        self.powerups.append({
            'pos': [x, y],
            'type': random.choice(['health', 'speed']),
            'timer': 300
        })
            
    def update_particles(self):
        for particle in self.particles[:]:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['timer'] -= 1
            if particle['timer'] <= 0:
                self.particles.remove(particle)

    def draw_trail(self, trail, color):
        if len(trail) > 1:
            pygame.draw.lines(screen, color, False, trail, 2)
                
    def draw_particles(self):
        for particle in self.particles:
            alpha = int((particle['timer'] / 20) * 255)
            size = particle['size']
            pos = [int(particle['pos'][0]), int(particle['pos'][1])]
            gfxdraw.filled_circle(screen, pos[0], pos[1], size, 
                                (*particle['color'], alpha))

    def draw_powerups(self):
        for powerup in self.powerups:
            color = BLUE if powerup['type'] == 'speed' else RED
            pygame.draw.circle(screen, color, 
                             [int(p) for p in powerup['pos']], 10)

    def apply_screen_shake(self):
        if self.screen_shake > 0:
            screen_offset = [random.randint(-2, 2), random.randint(-2, 2)]
            screen.blit(screen, screen_offset)
            self.screen_shake -= 1

    def run(self):
        running = True
        start_time = pygame.time.get_ticks()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
            # Update
            self.all_sprites.update()
            self.update_particles()
            
            # Powerup spawning and collection
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.spawn_powerup()
                self.powerup_timer = 180

            for powerup in self.powerups[:]:
                powerup['timer'] -= 1
                if powerup['timer'] <= 0:
                    self.powerups.remove(powerup)
                    continue

                if (abs(self.player.rect.centerx - powerup['pos'][0]) < 20 and
                    abs(self.player.rect.centery - powerup['pos'][1]) < 20):
                    if powerup['type'] == 'health':
                        self.player.health = min(100, self.player.health + 20)
                    else:
                        self.player.speed += 2
                    self.powerups.remove(powerup)
                    self.create_particles(powerup['pos'], PURPLE)
            
            # Check collisions
            if (pygame.sprite.collide_rect(self.player, self.shadow) and 
                not self.player.shield_active):
                self.player.health -= 1
                self.create_particles(self.player.rect.center, RED)
                self.screen_shake = 5
                
            # Calculate remaining time
            elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
            remaining_time = max(0, self.game_time - elapsed_time)
            
            if remaining_time <= 0 or self.player.health <= 0:
                running = False
            
            # Draw
            screen.fill(BLACK)
            
            # Draw trails
            self.draw_trail(self.player.trail, BLUE)
            self.draw_trail(self.shadow.trail, RED)
            
            self.all_sprites.draw(screen)
            self.draw_particles()
            self.draw_powerups()
            
            # Draw shield if active
            if self.player.shield_active:
                pygame.draw.circle(screen, BLUE, self.player.rect.center, 30, 2)
            
            # Draw HUD
            time_text = self.font.render(f"Time: {remaining_time}s", True, WHITE)
            health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
            dash_text = self.font.render(
                f"Dash Cooldown: {self.player.dash_cooldown//60}s", True, WHITE)
            shield_text = self.font.render(
                f"Shield Cooldown: {self.player.shield_cooldown//60}s", True, WHITE)
            
            screen.blit(time_text, (10, 10))
            screen.blit(health_text, (10, 50))
            screen.blit(dash_text, (10, 90))
            screen.blit(shield_text, (10, 130))
            
            self.apply_screen_shake()
            pygame.display.flip()
            self.clock.tick(60)

# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
