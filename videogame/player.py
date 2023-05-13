import math
import rgbcolors
import pygame

class Player:
    def __init__(self, position):
        self._position = position
        self._radius = 40
        self._color = rgbcolors.orange
        self._velocity = pygame.math.Vector2(0, 0)
        self._rect = pygame.Rect(position[0] - self._radius, position[1] - self._radius, self._radius * 2, self._radius * 2)

    def update(self):
        v = self._position.x + self._velocity.x
        if v > 0 and v < 800:
            self._position = self._position + self._velocity
            self._rect.x = self._position.x - self._radius
            self._rect.y = self._position.y - self._radius

    def die(self):
        print("You died")
    
    @property
    def position(self):
        return self._position

    @property
    def rect(self):
        return self._rect

    def stop(self):
        self._velocity = pygame.math.Vector2(0, 0)

    def move_left(self):
        self._velocity = pygame.math.Vector2(-10, 0)

    def move_right(self):
        self._velocity = pygame.math.Vector2(10, 0)

    def draw(self, screen):
        pygame.draw.circle(screen, self._color, self._position, self._radius)
        

class Bullet:
    def __init__(self, position, target_position, speed, source=None):
        self._position = pygame.math.Vector2(position)
        self._target_position = pygame.math.Vector2(target_position)
        self._speed = speed
        self._color = rgbcolors.mult_color(self._speed, rgbcolors.red)
        self._radius = 10
        self._source = source
    
    @property
    def rect(self):
        """Return bounding rect."""
        left = self._position.x - self._radius
        top = self._position.y - self._radius
        width = 2 * self._radius
        return pygame.Rect(left, top, width, width)
    
    def should_die(self):
        squared_distance = (self._position - self._target_position).length_squared()
        return math.isclose(squared_distance, 0.0, rel_tol=1e-01)
            
    def update(self, delta_time):
        self._position.move_towards_ip(self._target_position, self._speed * delta_time)
    
    def draw(self, screen):
        """Draw the circle to screen."""
        pygame.draw.circle(screen, self._color, self._position, self._radius)
    