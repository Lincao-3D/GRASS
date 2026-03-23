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
    """Load all SFX files once at startup and initialize volume."""
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
        button_hover_sound = None
        button_click_sound = None

    # Load volume from disk immediately after loading sounds
    apply_global_volume()

def apply_global_volume(vol_override=None, is_muted_override=None):
    """Updates the global audio state and applies it to music and loaded SFX objects."""
    global MASTER_VOLUME, IS_MUTED
    
    if vol_override is not None:
        MASTER_VOLUME = vol_override
    if is_muted_override is not None:
        IS_MUTED = is_muted_override

    # If no override, we might want to sync with disk, but for now let's use the provided logic:
    # "Note: Ensure Game.py and Options.py call apply_global_volume() without arguments when the slider changes, since get_current_volume now pulls the fresh JSON data automatically"
    
    if vol_override is None and is_muted_override is None:
        actual_vol = get_current_volume()
    else:
        actual_vol = 0.0 if IS_MUTED else MASTER_VOLUME

    if not pygame.mixer.get_init():
        return

    # 1. Update background music
    pygame.mixer.music.set_volume(actual_vol)
    
    # 2. Update loaded Sound objects
    if button_hover_sound: button_hover_sound.set_volume(actual_vol)
    if button_click_sound: button_click_sound.set_volume(actual_vol)

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

def typewriter_sound():
    """Generates a typewriter tick, scaled by master volume."""
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init():
        return

    SAMPLE_RATE = 44100
    TYPE_INTERNAL_VOL = 0.2 # Local balancing
    duration = random.uniform(0.01, 0.03)
    samples = int(SAMPLE_RATE * duration)

    # Generate noise and scale by volumes before int conversion
    noise = np.random.uniform(-1, 1, samples)
    envelope = np.linspace(1, 0, samples)
    wave = noise * envelope * TYPE_INTERNAL_VOL * vol
    
    # Convert to 16-bit integers for Pygame
    sound_array = (wave * 32767).astype(np.int16)
    sound_stereo = np.column_stack((sound_array, sound_array))
    
    sound = pygame.sndarray.make_sound(sound_stereo)
    sound.set_volume(vol) # Double safety scaling
    sound.play()

def play_retro_woosh(duration=0.3, rising=True):
    """Generates a retro woosh sweep, scaled by master volume."""
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init():
        return

    SAMPLE_RATE = 44100
    WOOSH_INTERNAL_VOL = 0.3
    samples = int(SAMPLE_RATE * duration)
    
    f_start, f_end = (100, 1000) if rising else (1000, 100)
    freqs = np.linspace(f_start, f_end, samples)
    phases = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
    wave = np.sin(phases)

    # Add retro noise/dirt
    noise = np.random.uniform(-0.2, 0.2, samples)
    
    # Scale by master volume here
    combined = (wave + noise) * WOOSH_INTERNAL_VOL * vol
    envelope = np.sin(np.pi * np.arange(samples) / samples)

    sound_array = (combined * envelope * 32767).astype(np.int16)
    sound_stereo = np.column_stack((sound_array, sound_array))
    
    sound = pygame.sndarray.make_sound(sound_stereo)
    sound.set_volume(vol)
    sound.play()

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
