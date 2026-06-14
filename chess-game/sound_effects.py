"""
Sound Effects Module - Generates chess game sounds.
Tries pygame first, falls back to simple oscillator if unavailable.
"""

import threading
import struct
import math
import array


def _generate_tone(frequency: float, duration: float, volume: float = 0.3,
                   sample_rate: int = 44100) -> bytes:
    """Generate a simple tone as signed 16-bit PCM bytes."""
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        amp = int(volume * 32767 * math.sin(2 * math.pi * frequency * t))
        buf[i] = max(-32768, min(32767, amp))
    return buf.tobytes()


def _generate_chess_sound(sound_type: str = "move") -> bytes:
    """Generate a chess-related sound."""
    sounds = {
        "move": [(440, 0.08), (520, 0.06)],
        "capture": [(330, 0.1), (260, 0.08)],
        "check": [(660, 0.15), (880, 0.1)],
        "checkmate": [(523, 0.2), (659, 0.2), (784, 0.3)],
        "castling": [(523, 0.1), (659, 0.1)],
        "promotion": [(784, 0.15), (988, 0.2)],
        "invalid": [(200, 0.15)],
    }

    tones = sounds.get(sound_type, sounds["move"])
    result = b""
    for freq, dur in tones:
        result += _generate_tone(freq, dur)
    return result


def _play_with_pygame(sound_bytes: bytes):
    """Attempt to play sound via pygame.mixer."""
    try:
        import pygame.mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        import io
        wave_file = io.BytesIO(sound_bytes)
        sound = pygame.mixer.Sound(stream=wave_file)
        sound.play()
        return True
    except Exception:
        return False


def _play_oscillator(sound_bytes: bytes):
    """Fallback: play via a simple subprocess oscilloscope."""
    try:
        import subprocess
        import tempfile
        import os
        # Write raw PCM to a temp file and play with aplay
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            f.write(sound_bytes)
            path = f.name
        subprocess.Popen(
            ["aplay", "-f", "S16_LE", "-r", "44100", "-c", "1", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.unlink(path)
        return True
    except Exception:
        return False


class SoundManager:
    """Manages chess game sound effects."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._play_method = None
        self._try_init()

    def _try_init(self):
        """Try to find a working sound playback method."""
        sound = _generate_chess_sound()
        if _play_with_pygame(sound):
            self._play_method = _play_with_pygame
        elif _play_oscillator(sound):
            self._play_method = _play_oscillator
        else:
            self.enabled = False

    def play_sound(self, sound_type: str = "move"):
        """Play a chess-related sound effect."""
        if not self.enabled or self._play_method is None:
            return
        try:
            sound_bytes = _generate_chess_sound(sound_type)
            self._play_method(sound_bytes)
        except Exception:
            pass

    def enable(self):
        self.enabled = True
        self._try_init()

    def disable(self):
        self.enabled = False
