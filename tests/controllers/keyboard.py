import pygame

def get_commands():
    commands = [0, 0]
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
         commands[0] = 1
    elif keys[pygame.K_DOWN]:
         commands[0] = -1

    if keys[pygame.K_RIGHT]:
        commands[1] = -1
    elif keys[pygame.K_LEFT]:
        commands[1] = 1

    return commands
  