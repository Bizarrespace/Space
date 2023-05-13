import warnings
import pygame
import rgbcolors
import pickle
from scene import (
    SceneManager,
    ShootingScene,
    GameOverScene,
    ContinueScreen,
    StartupScene
)


def display_info():
    print(f'The display is using the "{pygame.display.get_driver()}" driver.')
    print("Video Info:")
    print(pygame.display.Info())


class VideoGame:
    def __init__(
        self,
        window_width=800,
        window_height=600,
        window_title="My Awesome Game",
    ):
        pygame.init()
        self._window_size = (window_width, window_height)
        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(self._window_size)
        self._title = window_title
        pygame.display.set_caption(self._title)
        self._game_is_over = False
        if not pygame.font:
            warnings.warn("Fonts disabled.", RuntimeWarning)
        if not pygame.mixer:
            warnings.warn("Sound disabled.", RuntimeWarning)
        self._scene_manager = SceneManager()
        self.build_scene_graph()

    def build_scene_graph(self):
        raise NotImplementedError

    def run(self):
        self._scene_manager.set_scene("startup")  # Start with the startup scene

        while not self._game_is_over:
            self._scene_manager.update_scene()  # Update the scene before starting
            current_scene = self._scene_manager.current_scene
            current_scene.start_scene()
            current_scene.delta_time = self._clock.tick(current_scene.frame_rate())

            for event in pygame.event.get():
                self._scene_manager.process_event(event)

            self._scene_manager.update_current_scene()
            self._scene_manager.draw_current_scene()
            pygame.display.update()

            if not self._scene_manager.is_valid():
                if self._scene_manager.current_scene_key == "startup":
                    self._scene_manager.set_scene("shooting")
                elif self._scene_manager.current_scene_key == "shooting":
                    if len(self._scene_manager.scenes["shooting"]._aliens) == 0:
                        continue_scene = self._scene_manager.scenes["continue"]
                        score, lives = self.load_game_data()
                        continue_scene.update_score_and_lives(score, lives)
                        self._scene_manager.set_scene("continue")
                    else:
                        self._scene_manager.set_scene("game_over")
                elif self._scene_manager.current_scene_key == "game_over":
                    self._scene_manager.set_scene("startup")
                elif self._scene_manager.current_scene_key == "continue":
                    continue_scene = self._scene_manager.scenes["continue"]
                    if continue_scene.is_continue_selected() == "yes":
                        self.reset_game_state()
                        self._scene_manager.set_scene("shooting")
                        self._scene_manager.scenes["shooting"].load_game_data(*self.load_game_data())
                    else:
                        self._game_is_over = True
                else:
                    pass

        current_scene.end_scene()
        pygame.quit()
        return 0






class ShootingDemo(VideoGame):
    def __init__(self):
        super().__init__(window_title="Sprite Demo")

    def build_scene_graph(self):
        self._scene_manager.add_scene("startup", StartupScene(self._screen, self._scene_manager))
        self._scene_manager.add_scene("shooting", ShootingScene(self._screen, self._scene_manager))
        self._scene_manager.add_scene("game_over", GameOverScene(self._screen, self._scene_manager))
        self._scene_manager.add_scene(
            "continue",
            ContinueScreen(
                self._screen,
                score=self.load_game_data()[0],
                lives=self.load_game_data()[1],
            )
        )


    def reset_game_state(self):
        self._scene_manager.scenes["shooting"].reset_scene()

    def load_game_data(self):
        try:
            data = load_data("game_data.pickle")
        except FileNotFoundError:
            data = (0, 3)  # Default values if the file doesn't exist
        return data

    def save_game_data(self, score, lives):
        data = (score, lives)
        save_data("game_data.pickle", data)

    def run(self):
        super().run()


def save_data(filename, data):
    with open(filename, 'wb') as file:
        pickle.dump(data, file)


def load_data(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    return data
