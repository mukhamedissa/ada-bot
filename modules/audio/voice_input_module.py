import logging
import speech_recognition as sr
import pyaudio
from modules.base_module import BaseModule
from modules.audio.voice_command_dispatcher import VoiceCommandDispatcher
from core.event_manager import EventType

logger = logging.getLogger(__name__)


class VoiceInputModule(BaseModule):
    
    def __init__(self, config):
        super().__init__(config)
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.stop_listening_func = None

        self.command_dispatcher = VoiceCommandDispatcher()
        self._register_commands()
    
    def get_name(self) -> str:
        return "voice_input"
    
    def initialize(self):
        logger.info("Initializing voice input module")
        
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
            logger.info("Voice input module initialized and listening in background")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice input module: {e}")
            self._initialized = False

    def _recognition_callback(self, recognizer, audio):
        if not self._initialized:
            return

        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            
            logger.info(f"Recognized speech: '{text}'")
            
            command_result = self.command_dispatcher.dispatch(text)
            if command_result:
                logger.info(f"Command recognized: {command_result['command']}")

                if self.event_manager:
                    self.event_manager.emit(
                        EventType.COMMAND_RECOGNIZED,
                        data=command_result,
                        source=self.get_name()
                    )
            else:
                logger.debug(f"No command matched for: '{text}'")
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
    
    def update(self):
        pass
    
    def shutdown(self):
        logger.info("Shutting down voice input module")
        if self.stop_listening_func:
            logger.info("Stopping background listener")
            self.stop_listening_func(wait_for_stop=False)
            self.stop_listening_func = None
        
        self.microphone = None
        self._initialized = False
        logger.info("Voice input module shut down")

    def _register_commands(self):
        @self.command_dispatcher.register(
            patterns=[
                r"эйда",
                r"эй да",
                r"аида"
            ],
            command_name="respond_to_name",
            description="Откликнуться на имя"
        )
        def cmd_ada():
            logger.info("Command: Ada")
            return {
                'action': 'emotion',
                'name': 'smile'
            }
        @self.command_dispatcher.register(
            patterns=[
                r"привет",
                r"здравствуй(?:те)?",
                r"добр(?:ый день|ое утро|ый вечер)",
                r"здорово"
            ],
            command_name="greeting",
            description="Приветствие"
        )
        def cmd_greeting():
            logger.info("Command: Greeting detected")
            return {'action': 'greeting', 'response': 'Привет! Я тебя слышу'}
        
        @self.command_dispatcher.register(
            patterns=[
                r"ты меня слышишь",
                r"слышишь (?:ли )?меня",
                r"меня слышно"
            ],
            command_name="can_you_hear_me",
            description="Проверка связи"
        )
        def cmd_can_you_hear_me():
            logger.info("Command: Can you hear me?")
            return {'action': 'confirm_hearing', 'response': 'Да, я тебя слышу'}
        
        @self.command_dispatcher.register(
            patterns=[
                r"скажи да",
                r"ответь да",
                r"говори да"
            ],
            command_name="say_yes",
            description="Сказать 'да'"
        )
        def cmd_say_yes():
            logger.info("Command: Say YES")
            return {'action': 'say', 'text': 'Да'}
        
        @self.command_dispatcher.register(
            patterns=[
                r"скажи нет",
                r"ответь нет",
                r"говори нет"
            ],
            command_name="say_no",
            description="Сказать 'нет'"
        )
        def cmd_say_no():
            logger.info("Command: Say NO")
            return {'action': 'say', 'text': 'Нет'}

        @self.command_dispatcher.register(
            patterns=[
                r"покажи (?:мой )?ранг (?:в )?(?:валорант|вал|вало|valo|valor)",
                r"какой (?:у меня )?ранг (?:в )?(?:валорант|вал|вало|valo|valor)",
                r"мой ранг (?:в )?(?:валорант|вал|вало|valo|valor)",
                r"ранг (?:валорант|вал|вало|valo|valor)",
                r"(?:валорант|вал|вало|valo|valor) ранг"
            ],
            command_name="show_valorant_rank",
            description="Показать ранг в Valorant"
        )
        def cmd_show_valorant_rank():
            logger.info("Command: Show Valorant rank")
            return {'action': 'valorant_info', 'info_type': 'rank'}
        
        @self.command_dispatcher.register(
            patterns=[
                r"улыбнись",
                r"улыбка",
                r"улыбнись мне",
                r"сделай улыбку"
            ],
            command_name="smile",
            description="Показать улыбку"
        )
        def cmd_smile():
            logger.info("Command: Smile")
            return {
                'action': 'emotion',
                'name': 'smile'
            }
        
        logger.info(f"Registered {len(self.command_dispatcher.commands)} voice commands")

