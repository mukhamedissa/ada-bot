import logging
import speech_recognition as sr
import pyaudio
from modules.base_module import BaseModule
from core.event_manager import EventType

logger = logging.getLogger(__name__)


class AudioModule(BaseModule):
    
    def __init__(self, config):
        super().__init__(config)
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.stop_listening_func = None
        self.device_index = getattr(self.config, "DEVICE_INDEX", 0)
        self.language = getattr(self.config, "LANGUAGE", "ru-RU")
    
    def get_name(self) -> str:
        return "audio"
    
    def initialize(self):
        logger.info("Initializing audio module")
        
        try:
            self.microphone = sr.Microphone()
            
            with self.microphone as source:
                logger.info("Calibrating background noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info(f"Calibration complete. Energy threshold: {self.recognizer.energy_threshold}")
            
            self.stop_listening_func = self.recognizer.listen_in_background(
                self.microphone, 
                self._recognition_callback, 
                phrase_time_limit=5
            )
            
            self._initialized = True
            logger.info("Audio module initialized and listening in background")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio module: {e}")
            self._initialized = False

    def _recognition_callback(self, recognizer, audio):
        if not self._initialized:
            return

        try:
            text = recognizer.recognize_google(audio)
            
            logger.info(f"Recognized speech: '{text}'")
            
            # if self.event_manager:
            #     self.event_manager.emit(
            #         EventType.AUDIO_DETECTED, 
            #         data={'text': text},
            #         source=self.get_name()
            #     )
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
    
    def update(self):
        pass
    
    def shutdown(self):
        logger.info("Shutting down audio module")
        if self.stop_listening_func:
            logger.info("Stopping background listener")
            self.stop_listening_func(wait_for_stop=False)
            self.stop_listening_func = None
        
        self.microphone = None
        self._initialized = False
        logger.info("Audio module shut down")
