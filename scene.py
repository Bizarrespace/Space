import os
import random
import pygame
import assets
import player
import rgbcolors
import pickle
from animation import Explosion


class Scene:

    def __init__(self, screen, background_color, soundtrack=None):
        self._screen = screen
        self._background = pygame.Surface(self._screen.get_size())
        self._background.fill(background_color)
        self._frame_rate = 60
        self._is_valid = True
        self._soundtrack = soundtrack
        self._render_updates = None

    def draw(self):
        self._screen.blit(self._background, (0, 0))

    def process_event(self, event):
        if event.type == pygame.QUIT:
            print("Good Bye!")
            self._is_valid = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            print("Bye bye!")
            self._is_valid = False

    def is_valid(self):
        return self._is_valid

    def render_updates(self):
        """Render all sprite updates."""

    def update_scene(self):
        """Update the scene state."""

    def start_scene(self):
        """Start the scene."""
        if self._soundtrack:
            try:
                pygame.mixer.music.load(self._soundtrack)
                pygame.mixer.music.set_volume(0.5)
            except pygame.error as pygame_error:
                print("\n".join(pygame_error.args))
                raise SystemExit("broken!!") from pygame_error
            pygame.mixer.music.play(-1)

    def end_scene(self):
        if self._soundtrack and pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(500)
            pygame.mixer.music.stop()

    def frame_rate(self):
        return self._frame_rate


class PressAnyKeyToExitScene(Scene):
    def process_event(self, event):
        """Process game events."""
        super().process_event(event)
        if event.type == pygame.KEYDOWN:
            self._is_valid = False

class SceneManager:
    def __init__(self):
        self.scenes = {}
        self.current_scene_key = None
        self.next_scene_key = None

    def add_scene(self, key, scene):
        self.scenes[key] = scene

    def set_scene(self, key):
        self.next_scene_key = key

    def is_valid(self):
        return self.current_scene_key is not None

    def update_scene(self):
        if self.next_scene_key is not None:
            if self.current_scene_key is not None:
                self.scenes[self.current_scene_key].end_scene()
            self.current_scene_key = self.next_scene_key
            self.next_scene_key = None
            self.scenes[self.current_scene_key].start_scene()

    @property
    def current_scene(self):
        if self.current_scene_key is not None:
            return self.scenes[self.current_scene_key]
        return None

    def update_current_scene(self):
        if self.current_scene:
            self.current_scene.update_scene()

    def process_event(self, event):
        if self.current_scene:
            self.current_scene.process_event(event)

    def draw_current_scene(self):
        if self.current_scene:
            self.current_scene.draw()




class ShootingScene(PressAnyKeyToExitScene):
    def __init__(self, screen, score=0, lives = 3):
        super().__init__(screen, rgbcolors.black, assets.get('soundtrack'))
        self._explosion_sound = pygame.mixer.Sound(assets.get('soundfx'))
        self.obstacles = []
        self._aliens = None
        self._alien_direction = 1  # Initial direction of aliens' movement (1 = right, -1 = left)
        self.delta_time = 0
        self._bullets = []
        self._lives = lives  # Add the lives attribute
        (width, height) = self._screen.get_size()
        self._player = player.Player(pygame.math.Vector2(width // 2, height - 100))
        self._score = score
        self.make_obstacles()
        self.make_aliens()
        self._render_updates = pygame.sprite.RenderUpdates()
        Explosion.containers = self._render_updates
        self._alien_fire_timer = 0
        self._alien_cooldown = 2000

    def load_game_data(self, score, lives):
        try:
            data = load_data("game_data.pickle")
        except FileNotFoundError:
            data = (0, 3)  # Default values if the file doesn't exist
        return data
    
    def make_obstacles(self):
        (width, height) = self._screen.get_size()
        obstacle_width = 50
        obstacle_height = 30
        num_obstacles = 4

        # Calculate the total width of the obstacles and the spacing between them
        total_obstacles_width = obstacle_width * num_obstacles
        spacing = max((width - total_obstacles_width) // (num_obstacles + 1), 10)

        # Calculate the x-coordinate for the first obstacle to be centered
        start_x_obstacles = (width - (total_obstacles_width + spacing * (num_obstacles - 1))) // 2

        # Create the obstacles
        self._obstacles = [
            Obstacle((start_x_obstacles + i * (obstacle_width + spacing), height - 200), obstacle_width, obstacle_height, rgbcolors.gray)
            for i in range(num_obstacles)
        ]

    def make_aliens(self):
        (width, height) = self._screen.get_size()


        # Adjust the alien_width, alien_radius, and gutter_width
        alien_width = width // 9
        alien_radius = alien_width // 2
        gutter_width = alien_width // 8
        alien_scale = .5  # Adjust the scale value as desired

        x_step = gutter_width + alien_width
        y_step = gutter_width + alien_width * alien_scale  # Adjust the y_step based on alien_scale

        # Set the number of rows and aliens per row
        num_rows = 1
        aliens_per_row = width // (alien_width + gutter_width) - 1

        # Calculate the total width and height needed for the grid
        total_width = (alien_width * aliens_per_row) + (gutter_width * (aliens_per_row - 1))
        total_height = (alien_width * alien_scale * num_rows) + (gutter_width * (num_rows - 1))

        # Calculate the starting x and y coordinates to keep the grid in the upper half of the screen
        start_x = ((width - total_width + gutter_width) // 2) - 50
        start_y = (height // 2 - total_height) // 2

        print(f"There will be {num_rows} rows and {aliens_per_row} aliens in each row.")
        self._aliens = [
            Alien(
                pygame.math.Vector2(start_x + x_step + (j * x_step), start_y + y_step + (i * y_step)),
                alien_radius,
                os.path.join(assets.data_dir, 'cow.png'),
                alien_scale,
                f"{i+1}, {j+1}",
            )
            for i in range(num_rows)
            for j in range(aliens_per_row)
        ]

    def update_aliens(self):
        current_time = pygame.time.get_ticks()
        if current_time >= self._alien_fire_timer:
            self.fire_alien_bullet()
            self._alien_fire_timer = current_time + self._alien_cooldown

        (screen_width, screen_height) = self._screen.get_size()

        if not self._aliens:
            # All aliens are destroyed
            self._is_valid = False
            return

        alien_width = self._aliens[0]._rect.width
        alien_height = self._aliens[0]._rect.height

        # Determine if any alien has reached the edge of the screen
        aliens_reached_edge = False
        for alien in self._aliens:
            if alien._rect.left <= 0 or alien._rect.right >= screen_width:
                aliens_reached_edge = True
                break

        if aliens_reached_edge:
            # Move the aliens down by their height
            for alien in self._aliens:
                alien._position.y += alien_height 
                alien._rect.center = alien._position

            # Reverse the direction after moving down
            self._alien_direction *= -1

        # Move the aliens horizontally
        for alien in self._aliens:
            alien._position.x += self._alien_direction
            alien._rect.center = alien._position

            # Check for collision with player
            if alien._rect.colliderect(self._player.rect):
                self._lives -= 1
                if self._lives <= 0:
                    self._is_valid = False

        self.update_bullets()
        self.check_collisions()

    def fire_alien_bullet(self):
        if self._aliens:
            random_alien = random.choice(self._aliens)
            bullet_target = self._player.position
            velocity = random.uniform(0.1, 0.5)
            self._bullets.append(AlienBullet(random_alien._position, bullet_target, velocity))

    def reset_scene(self):
        self._aliens.clear()
        self._bullets.clear()
        (width, height) = self._screen.get_size()
        self._player = player.Player(pygame.math.Vector2(width // 2, height - 100))
        self._score = 0
        self._lives = 3
        self.make_aliens()

    def update_scene(self):
        super().update_scene()
        self._player.update()
        self.update_aliens()
        self.update_bullets()
        self.check_collisions()
        

    def update_bullets(self):
        for bullet in self._bullets:
            bullet.update(self.delta_time)
            if bullet.should_die():
                self._bullets.remove(bullet)

    def check_collisions(self):
        player_hit = False
        bullets_to_remove = []
        collided_bullets = set()  # Track collided bullets to avoid duplicate removal

        for bullet in self._bullets.copy():
            if bullet in collided_bullets:
                continue

            if isinstance(bullet, AlienBullet):
                if bullet.rect.colliderect(self._player.rect):
                    player_hit = True
                    bullets_to_remove.append(bullet)
                    collided_bullets.add(bullet)
            elif isinstance(bullet, player.Bullet):
                index = bullet.rect.collidelist([c.rect for c in self._aliens])
                if index > -1 and self._aliens[index] != bullet._source:
                    Explosion(self._aliens[index])
                    self._aliens[index].is_exploding = True
                    self._aliens.remove(self._aliens[index])
                    self._explosion_sound.play()
                    bullets_to_remove.append(bullet)
                    collided_bullets.add(bullet)
                    self._score += 10
                    if self._score % 100 == 0:
                        self._lives += 1
                    print("Score", self._score)

            for obstacle in self._obstacles:
                if bullet.rect.colliderect(obstacle.rect):
                    bullets_to_remove.append(bullet)
                    collided_bullets.add(bullet)

        for bullet in bullets_to_remove:
            if bullet in self._bullets:
                self._bullets.remove(bullet)

        for obstacle in self._obstacles:
            if obstacle.rect.colliderect(self._player.rect):
                player_hit = True

        if player_hit:
            self._lives -= 1
            if self._lives <= 0:
                self._is_valid = False


    def process_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            (width, height) = self._screen.get_size()

            bullet_target = self._player.position - pygame.math.Vector2(0, height)
            velocity = random.uniform(0.1, 1.0)
            self._bullets.append(player.Bullet(self._player.position, bullet_target, velocity))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            self._player.move_left()
        elif event.type == pygame.KEYUP and event.key == pygame.K_LEFT:
            self._player.stop()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            self._player.move_right()
        elif event.type == pygame.KEYUP and event.key == pygame.K_RIGHT:
            self._player.stop()
        else:
            super().process_event(event)
        
    def render_updates(self):
        super().render_updates()
        self._render_updates.clear(self._screen, self._background)
        self._render_updates.update()
        dirty = self._render_updates.draw(self._screen)

    def draw(self):
        super().draw()
        
        #Set a font and then draw the score on the screen
        font = pygame.font.Font(None,36)
        text_score = font.render("Score: " + str(self._score), True, rgbcolors.white)
        self._screen.blit(text_score, (10, 10))

        #Draw lives
        text_lives = font.render("Lives: " + str(self._lives), True, rgbcolors.white)
        self._screen.blit(text_lives, (10, 50))
        for alien in self._aliens:
            if not alien.is_exploding:
                alien.draw(self._screen)
        for bullet in self._bullets:
            bullet.draw(self._screen)
        self._player.draw(self._screen)

        for obstacle in self._obstacles:
            obstacle.draw(self._screen)

class GameOverScene(PressAnyKeyToExitScene):
    def __init__(self, screen, scene_manager, background_color=rgbcolors.black, score=0):
        super().__init__(screen, background_color)
        self.scene_manager = scene_manager
        self._score = score

    def draw(self):
        super().draw()
        font = pygame.font.Font(None, 72)
        text = font.render("Game Over", True, rgbcolors.white)
        text_rect = text.get_rect(center=(self._screen.get_rect().center[0], self._screen.get_rect().center[1] - 50))
        self._screen.blit(text, text_rect)

        score_text = font.render(f"Score: {self._score}", True, rgbcolors.white)
        score_text_rect = score_text.get_rect(center=(self._screen.get_rect().center[0], self._screen.get_rect().center[1] + 50))
        self._screen.blit(score_text, score_text_rect)


class ContinueScreen(Scene):
    def __init__(self, screen, score, lives):
        super().__init__(screen, rgbcolors.black)
        self._selected_option = None
        self._score = score  
        self._lives = lives
        self._font = pygame.font.Font(None, 72)
        self._title_text = self._font.render("Continue Playing?", True, rgbcolors.white)
        self._title_rect = self._title_text.get_rect(center=(self._screen.get_rect().centerx, 200))
        self._option_yes_text = self._font.render("Yes", True, rgbcolors.white)
        self._option_yes_rect = self._option_yes_text.get_rect(center=(self._screen.get_rect().centerx - 100, 350))
        self._option_no_text = self._font.render("No", True, rgbcolors.white)
        self._option_no_rect = self._option_no_text.get_rect(center=(self._screen.get_rect().centerx + 100, 350))

    def update_score_and_lives(self, score, lives):
        self.score = score
        self.lives = lives
        
    def draw(self):
        super().draw()
        self._screen.blit(self._title_text, self._title_rect)
        self._screen.blit(self._option_yes_text, self._option_yes_rect)
        self._screen.blit(self._option_no_text, self._option_no_rect)

    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self._selected_option = "yes"  # Set the selected option to "yes"
            self_is_valid = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            self._selected_option = "no"  # Set the selected option to "no"
            self_is_valid = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._is_valid = False  # Mark the scene as invalid to move to the next scene

    def is_continue_selected(self):
        return self._selected_option == "yes"


class StartupScene(PressAnyKeyToExitScene):
    def __init__(self, screen, scene_manager, background_color=rgbcolors.black):
        super().__init__(screen, background_color)
        self.scene_manager = scene_manager

    def draw(self):
        super().draw()
        font = pygame.font.Font(None, 72)
        text = font.render("Press Spacebar to Start", True, rgbcolors.white)
        text_rect = text.get_rect(center=self._screen.get_rect().center)
        self._screen.blit(text, text_rect)

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.scene_manager.set_scene("shooting")



class Obstacle:
    def __init__(self, position, width, height, color):
        self._position = position
        self._width = width
        self._height = height
        self._color = color
        self._rect = pygame.Rect(self._position[0], self._position[1], self._width, self._height)

    @property
    def rect(self):
        return self._rect

    def draw(self, screen):
        pygame.draw.rect(screen, self._color, self._rect)

class Alien:
    def __init__(self, position, radius, image_path, scale=1.0, name="None"):
        self._position = position
        self._radius = radius
        self._image = pygame.image.load(image_path).convert_alpha()
        self._image = pygame.transform.scale(self._image, (int(self._radius * 2 * scale), int(self._radius * 2 * scale)))
        self._rect = self._image.get_rect(center=position)
        self._is_exploding = False
        self._name = name

    @property
    def rect(self):
        return self._rect

    @property
    def is_exploding(self):
        return self._is_exploding

    @is_exploding.setter
    def is_exploding(self, value):
        self._is_exploding = value

    def draw(self, screen):
        screen.blit(self._image, self._rect)

class AlienBullet(player.Bullet):
    def __init__(self, position, target_position, speed, source=None):
        super().__init__(position, target_position, speed, source)
        self._color = rgbcolors.red

def save_data(filename, data):
    with open(filename, 'wb') as file:
        pickle.dump(data, file)

# Load data from a file
def load_data(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    return data
