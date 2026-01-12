import pygame
import sys
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS
from game.screens.home import HomeScreen
from game.screens.select import SongSelectScreen
from game.screens.gameplay import GameplayScreen
from game.screens.settings_screen import SettingsScreen
from game.screens.result import ResultScreen
from game.map_editor.map_select_screen import MapSelectScreen
from game.map_editor.editor_screen import EditorScreen



def main():
    pygame.init()
    pygame.font.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    
    # Init Screens
    screens = {
        'menu': HomeScreen(),
        'select': SongSelectScreen(),
        'settings': SettingsScreen(),
        'gameplay': None,
        'result': None,
        'map_select': MapSelectScreen(),
        'editor': None
    }


    
    current_screen_key = 'menu'
    current_screen = screens['menu']
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            result = current_screen.handle_event(event)
            if result == 'quit':
                running = False
        
        current_screen.update(dt)
        
        next_screen_key = current_screen.get_next_screen()
        
        args = None
        if isinstance(next_screen_key, tuple):
            next_screen_key, args = next_screen_key
            
        if next_screen_key:
            if next_screen_key == 'gameplay':
                screens['gameplay'] = GameplayScreen()
                current_screen_key = 'gameplay'
                current_screen = screens['gameplay']
                
            elif next_screen_key == 'result':
                screens['result'] = ResultScreen(args)
                current_screen_key = 'result'
                current_screen = screens['result']
                
            elif next_screen_key == 'editor':
                screens['editor'] = EditorScreen(args)
                current_screen_key = 'editor'
                current_screen = screens['editor']
                

            elif next_screen_key == 'select':
                if screens['select']: screens['select'].refresh_data()
                current_screen_key = 'select'
                current_screen = screens['select']
                
            elif next_screen_key in screens:
                current_screen_key = next_screen_key
                current_screen = screens[next_screen_key]
        
        # Draw
        current_screen.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
