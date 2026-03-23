import os
import random
import sys
import json
from typing import AnyStr

import numpy as np
import pygame

from src.constants import DEBUG

# --- Global Audio State ---
# These act as the "Source of Truth" for all sounds in the game
MASTER_VOLUME = 0.5
IS_MUTED = False

# Global SFX Variables (loaded once at startup)
button_hover_sound = None
button_click_sound = None

def get_assets_path() -> AnyStr:
    """Returns the absolute path to the assets folder, handling PyInstaller and Dev environments."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets")

    # DEV: Path based on the main file module
    try:
        main_file = sys.modules["__main__"].__file__
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(main_file)))
    except (KeyError, AttributeError):
        # Fallback if __main__ isn't available
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(project_root, "assets")

def get_current_volume():
    """Helper to dynamically fetch the exact volume from JSON right now."""
    try:
        # Guarantee we look at src/options.json
        opts_path = os.path.join(os.path.dirname(__file__), "options.json")
        with open(opts_path, "r") as f:
            opts = json.load(f)
        if opts.get("is_muted", False):
            return 0.0
        return opts.get("master_volume", 0.5)
    except Exception:
        return 0.5 # Safe fallback

def load_sfx():
    global button_hover_sound, button_click_sound
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    sfx_path = os.path.join(get_assets_path(), "sfx")
    try:
        button_hover_sound = pygame.mixer.Sound(os.path.join(sfx_path, "button_hover.mp3"))
        button_click_sound = pygame.mixer.Sound(os.path.join(sfx_path, "button_click.mp3"))
        print("[Audio] SFX loaded successfully")
    except Exception as e:
        print(f"[Audio] SFX loading warning: {e}")
        
    apply_global_volume() # Apply immediately upon loading

def apply_global_volume(vol_override=None):
    """Applies volume to Pygame mixer and cached Sound objects."""
    if not pygame.mixer.get_init(): return
    
    # If no override is provided, read straight from JSON
    vol = vol_override if vol_override is not None else get_current_volume()
    pygame.mixer.music.set_volume(vol)
    
    if button_hover_sound: button_hover_sound.set_volume(vol)
    if button_click_sound: button_click_sound.set_volume(vol)

def apply_volume():
    """Reads settings from options.json and triggers apply_global_volume."""
    apply_global_volume()

# --- Sound Triggers ---

def play_button_hover():
    if button_hover_sound:
        button_hover_sound.play()

def play_button_click():
    if button_click_sound:
        button_click_sound.play()

# --- Procedural Sounds (Updated Pipeline) ---

def play_retro_woosh():
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init(): return

    duration = 0.3
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq = np.linspace(800, 200, len(t))
    
    # Scale amplitude by volume!
    wave = 0.5 * vol * np.sin(2 * np.pi * freq * t) 
    audio_data = np.int16(wave * 32767)
    stereo_data = np.column_stack((audio_data, audio_data))
    
    try:
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.set_volume(vol)
        sound.play()
    except Exception:
        pass # Failsafe

def typewriter_sound():
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init(): return

    sample_rate = 44100
    duration = 0.02
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Scale amplitude by volume!
    wave = np.random.uniform(-1, 1, len(t)) * 0.1 * vol 
    audio_data = np.int16(wave * 32767)
    stereo_data = np.column_stack((audio_data, audio_data))
    
    try:
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.set_volume(vol)
        sound.play()
    except Exception:
        pass

# --- Utility Graphics/System Helpers ---

def get_default_font(size: int) -> pygame.font.Font:
    return pygame.font.Font(os.path.join(get_assets_path(), "font.ttf"), size)

def get_image(image: AnyStr) -> pygame.Surface:
    return pygame.image.load(os.path.join(get_assets_path(), image))

def print_debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_center_x(screen: pygame.Surface, image_width: int) -> int:
    return (screen.get_width() - image_width) // 2

def get_mod(attrib: int) -> int:
    return (attrib - 10) // 2

def grid_position(index, start_x, start_y, item_width, item_height, columns, h_spacing=20, v_spacing=8):
    col = index % columns
    row = index // columns
    x = start_x + col * (item_width + h_spacing)
    y = start_y + row * (item_height + v_spacing)
    return x, y

if __name__ == "__main__":
    pygame.init() 
    print(f"Asset Path: {get_assets_path()}")
    load_sfx()
    # Test procedurals
    typewriter_sound()
    play_retro_woosh()
