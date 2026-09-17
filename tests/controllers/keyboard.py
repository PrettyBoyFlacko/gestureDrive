import pygame

def get_commands():
    commands = []
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        commands.append("UP")
    elif keys[pygame.K_DOWN]:
         commands.append("DOWN")
    elif keys[pygame.K_ESCAPE]:
        commands.append("RESET")

    if keys[pygame.K_RIGHT]:
        commands.append("RIGHT")
    elif keys[pygame.K_LEFT]:
        commands.append("LEFT")

    return commands
  