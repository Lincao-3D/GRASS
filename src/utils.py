import os
import random
import sys
from typing import AnyStr

import numpy as np
import pygame

import json

from src.constants import DEBUG



def get_assets_path() -> AnyStr:
    # PyInstaller
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets")

    # DEV: caminho baseado no arquivo principal, não no cwd
    main_file = sys.modules["__main__"].__file__
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(main_file)))

    return os.path.join(project_root, "assets")

def get_default_font(size:int) -> pygame.font.Font:
    return pygame.font.Font(os.path.join(get_assets_path(), "font.ttf"), size)

def get_image(image:AnyStr)-> pygame.Surface:
    return pygame.image.load(os.path.join(get_assets_path(), image))

def print_debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def clear_console():
    # Check the operating system name
    if os.name == 'nt':
        # Command for Windows
        _ = os.system('cls')
    else:
        # Command for macOS/Linux (posix)
        _ = os.system('clear')

def get_center_x(screen: pygame.Surface, image_width: int) -> int:
    screen_width = screen.get_width()
    return (screen_width - image_width) // 2

def get_mod(attrib: int) -> int:
    return (attrib - 10) // 2

def grid_position(
        index: int,
        start_x: int,
        start_y: int,
        item_width: int,
        item_height: int,
        columns: int,
        h_spacing: int = 20,
        v_spacing: int = 8
):
    col = index % columns
    row = index // columns

    x = start_x + col * (item_width + h_spacing)
    y = start_y + row * (item_height + v_spacing)

    return x, y

def apply_volume():
    # Dynamically find the path to src/options.json based on utils.py's location
    current_dir = os.path.dirname(__file__)
    options_path = os.path.join(current_dir, "options.json")
    
    try:
        with open(options_path, "r") as f:
            opts = json.load(f)

        vol = 0.0 if opts.get("is_muted", False) else opts.get("master_volume", 0.5)

        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(vol)
            
    except FileNotFoundError:
        print(f"[Audio] No options file found at {options_path}. Using defaults.")
    except json.decoder.JSONDecodeError as e:
        print(f"[Audio] Broken JSON in {options_path}. Ignoring: {e}")

def typewriter_sound():
    SAMPLE_RATE = 44100
    TYPE_VOLUME = 0.4

    duration = random.uniform(0.01, 0.03)
    samples = int(SAMPLE_RATE * duration)

    # ruído branco
    noise = np.random.uniform(-1, 1, samples)

    # envelope de ataque rápido
    envelope = np.linspace(1, 0, samples)

    sound = noise * envelope
    sound = (sound * 32767 * TYPE_VOLUME).astype(np.int16)
    sound_stereo = np.column_stack((sound, sound))
    pygame.sndarray.make_sound(sound_stereo).play()

def play_retro_woosh(duration=0.2, rising=True):
    SAMPLE_RATE = 44100
    VOLUME = 0.3
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples)

    # 1. Definição de Frequência (o "sweep")
    # Para um woosh de transição, vamos de 100Hz a 1000Hz (ou vice-versa)
    f_start, f_end = (100, 1000) if rising else (1000, 100)
    
    # Criando uma rampa de frequência (Chirp signal)
    freqs = np.linspace(f_start, f_end, samples)
    phases = 2 * np.pi * np.cumsum(freqs) / SAMPLE_RATE
    wave = np.sin(phases)

    # 2. Adicionar um pouco de "sujeira" retrô (ruído suave)
    noise = np.random.uniform(-0.2, 0.2, samples)
    combined = wave + noise

    # 3. Envelope de Amplitude (Fade in e Fade out suave para não estalar)
    envelope = np.sin(np.pi * np.arange(samples) / samples) # Formato de arco

    # 4. Finalização
    sound_array = (combined * envelope * 32767 * VOLUME).astype(np.int16)
    sound_stereo = np.column_stack((sound_array, sound_array))
    
    pygame.sndarray.make_sound(sound_stereo).play()

# Exemplo de uso para o dado:
# play_retro_woosh(duration=0.15, rising=True)


if __name__ == "__main__":
    print(get_assets_path())