import pygame
import math
import sys


# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Top-Down Car Simulation")

# Clock for FPS control
clock = pygame.time.Clock()

# Car settings
CAR_WIDTH, CAR_HEIGHT = 50, 20
MAX_SPEED = 2
ACCELERATION = 0.1
FRICTION = 0.05
TURN_SPEED = 0.5  # degrees per frame

# Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 90
        self.speed = 0
        self.image = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, RED, [(0, 0), (CAR_WIDTH, CAR_HEIGHT // 2), (0, CAR_HEIGHT)])
        self.original_image = self.image

    def update(self, commands):
        # Acceleration & braking
        if "UP" in commands:
            self.speed += ACCELERATION
        elif "DOWN" in commands:
            self.speed -= ACCELERATION
        elif "RESET" in commands:
            self.x = WIDTH/2
            self.y = HEIGHT/2
            self.speed = 0

        # Limit speed
        self.speed = max(-MAX_SPEED, min(self.speed, MAX_SPEED))

        # Apply friction
        if self.speed > 0:
            self.speed -= FRICTION
            if self.speed < 0:
                self.speed = 0
        elif self.speed < 0:
            self.speed += FRICTION
            if self.speed > 0:
                self.speed = 0

        # Steering
        if self.speed != 0:
            if "LEFT" in commands:
                self.angle += TURN_SPEED * (-1 if self.speed > 0 else 1)
            if "RIGHT" in commands:
                self.angle -= TURN_SPEED * (-1 if self.speed > 0 else 1)

        # Update position
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

    def draw(self, surface):
        rotated_image = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated_image.get_rect(center=(self.x, self.y))
        surface.blit(rotated_image, rect.topleft)

def main(control_func):
    car = Car(WIDTH // 2, HEIGHT // 2)

    while True:
        screen.fill(WHITE)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        commands = control_func()
        car.update(commands)
        car.draw(screen)

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

import controllers.keyboard as keyboard
import controllers.hands as hands

if __name__ == "__main__":
    main(hands.get_commands)
