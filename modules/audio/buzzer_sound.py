import pygame
import numpy as np
import logging
import threading
from time import sleep

logger = logging.getLogger(__name__)

NOTE_A0 = 27
NOTE_B0 = 31
NOTE_C1 = 33
NOTE_E1 = 41
NOTE_G2 = 98
NOTE_A2 = 110
NOTE_C4 = 262
NOTE_D4 = 294
NOTE_E4 = 330
NOTE_A4 = 440
NOTE_B4 = 494
NOTE_C5 = 523
NOTE_D5 = 587
NOTE_E5 = 659
NOTE_F5 = 698
NOTE_G5 = 784
NOTE_A5 = 880
NOTE_B5 = 988
NOTE_C6 = 1047
NOTE_D6 = 1175
NOTE_E6 = 1319
NOTE_F6 = 1397
NOTE_G6 = 1568
NOTE_A6 = 1760
NOTE_B6 = 1976
NOTE_C7 = 2093
NOTE_D7 = 2349
NOTE_E7 = 2637

class BuzzerSound:
    def __init__(self, sample_rate=22050, volume=0.15):
        pygame.mixer.pre_init(sample_rate, -16, 1, 512)
        self.sample_rate = sample_rate
        self.volume = volume
        self.is_playing = False

    def generate_tone(self, frequency, duration, volume=None):
        if volume is None:
            volume = self.volume
        n_samples = int(round(duration * self.sample_rate))
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_sample = 2**(16-1) - 1
        
        for s in range(n_samples):
            t = float(s) / self.sample_rate
            buf[s][0] = int(round(max_sample * volume * np.sin(2*np.pi*frequency*t)))
            buf[s][1] = buf[s][0]
        
        return pygame.sndarray.make_sound(buf)

    def _play_tone_non_blocking(self, frequency, note_duration, silence_duration):
        tone = self.generate_tone(frequency, note_duration / 1000.0)
        tone.play()
        pygame.time.wait(int(note_duration + silence_duration))

    def _bend_notes_non_blocking(self, start_freq, end_freq, proportion, note_duration, silence_duration):
        frequencies = []
        if start_freq <= end_freq:
            frequency = start_freq
            while frequency < end_freq:
                frequencies.append((frequency, note_duration, silence_duration))
                frequency *= proportion
        else:
            frequency = start_freq
            while frequency > end_freq:
                frequencies.append((frequency, note_duration, silence_duration))
                frequency /= proportion
        return frequencies

    def play_emotion_non_blocking(self, emotion):
        if self.is_playing:
            logger.debug("Sound already playing, skipping")
            return
        
        self.is_playing = True
        
        def _play_emotion():
            try:
                if emotion == 'happy':
                    bend1 = self._bend_notes_non_blocking(NOTE_F6, NOTE_D7, 1.05, 25, 0)
                    bend2 = self._bend_notes_non_blocking(NOTE_D7, NOTE_F6, 1.05, 30, 0)
                    for freq, dur, sil in bend1 + bend2:
                        self._play_tone_non_blocking(freq, dur, sil)
                
                elif emotion == 'cute':
                    bend1 = self._bend_notes_non_blocking(NOTE_F6, NOTE_C7, 1.05, 20, 15)
                    pygame.time.wait(10)
                    bend2 = self._bend_notes_non_blocking(NOTE_B6, NOTE_E7, 1.05, 20, 15)
                    for freq, dur, sil in bend1 + bend2:
                        self._play_tone_non_blocking(freq, dur, sil)
                
                elif emotion == 'surprised':
                    bend1 = self._bend_notes_non_blocking(NOTE_G5, NOTE_C7, 1.02, 40, 4)
                    bend2 = self._bend_notes_non_blocking(NOTE_C7, NOTE_G5, 1.03, 30, 4)
                    for freq, dur, sil in bend1 + bend2:
                        self._play_tone_non_blocking(freq, dur, sil)
                
                elif emotion == 'yes':
                    self._play_tone_non_blocking(NOTE_C6, 80, 20)
                    self._play_tone_non_blocking(NOTE_E6, 100, 0)

                elif emotion == 'yes_excited':
                    bend1 = self._bend_notes_non_blocking(NOTE_C6, NOTE_G6, 1.08, 10, 5)
                    for freq, dur, sil in bend1:
                        self._play_tone_non_blocking(freq, dur, sil)
                    self._play_tone_non_blocking(NOTE_C7, 100, 0)
                
                elif emotion == 'no':
                    self._play_tone_non_blocking(NOTE_G6, 80, 20)
                    self._play_tone_non_blocking(NOTE_C6, 100, 0)
                
                elif emotion == 'maybe':
                    self._play_tone_non_blocking(NOTE_D6, 70, 20)
                    self._play_tone_non_blocking(NOTE_E6, 70, 20)
                    self._play_tone_non_blocking(NOTE_D6, 70, 0)
                
                else:
                    for i in range(3):
                        self._play_tone_non_blocking(NOTE_A5, 50, 30)
                        self._play_tone_non_blocking(NOTE_C6, 50, 30)
                
                self.is_playing = False
            except Exception as e:
                logger.error(f"Emotion playback error: {e}")
                self.is_playing = False
        
        thread = threading.Thread(target=_play_emotion, daemon=True)
        thread.start()
        logger.debug(f"Started non-blocking {emotion} emotion")

    def play_animation_sound(self, animation_type: str):
        sound_map = {
            'smile': 'cute',
            'shake': 'no',
            'nod': 'yes', 
            'blink': 'maybe',
            'respond': 'yes_excited'
        }
        emotion = sound_map.get(animation_type, 'thinking')
        self.play_emotion_non_blocking(emotion)
