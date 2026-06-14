"""
Sound Effects Module - Generates chess game sounds using the webbrowser audio API.
Provides simple beeps and tones for move, capture, check, and game events.
"""

import threading
import struct
import math
import os

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


def _init_pygame():
    """Initialize pygame mixer for sound playback."""
    if _HAS_PYGAME:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            return True
        except Exception:
            return False
    return False


def _generate_tone(frequency: float, duration: float, volume: float = 0.3,
                   sample_rate: int = 44100) -> bytes:
    """Generate a simple tone as WAV bytes."""
    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        amplitude = int(volume * 32767 * math.sin(2 * math.pi * frequency * t))
        amplitude = max(-32768, min(32767, amplitude))
        samples.append(struct.pack('<h', amplitude))

    return b''.join(samples)


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


class SoundManager:
    """Manages chess game sound effects."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._pygame_initialized = False
        self._use_pygame = False

        if _HAS_PYGAME:
            self._pygame_initialized = _init_pygame()
            self._use_pygame = self._pygame_initialized

    def play_sound(self, sound_type: str = "move"):
        """Play a chess-related sound effect."""
        if not self.enabled:
            return

        def _play():
            if self._use_pygame and self._pygame_initialized:
                try:
                    wav_data = _generate_chess_sound(sound_type)
                    # Create a Sound object from the WAV data
                    import io
                    # Create minimal WAV header
                    wav_header = struct.pack('<4sl4s',
                                             b'RIFF', 36 + len(wav_data),
                                             b'WAVE', b'fmt ')
                    fmt_chunk = struct.pack('<HHLLHH', 1, 1, 44100, 44100 * 2, 2, 16)
                    data_chunk = struct.pack('<4sl', b'data', len(wav_data))
                    wav_bytes = wav_header + fmt_chunk + data_chunk + wav_data

                    import io
                    wave_file = io.BytesIO(wav_bytes)

                    import pygame.mixer
                    sound = pygame.mixer.Sound(stream=wave_file)
                    sound.play()
                except Exception:
                    pass
            else:
                # Fallback: silent mode - sounds are optional
                pass

        if self.enabled:
            threading.Thread(target=_play, daemon=True).start()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
