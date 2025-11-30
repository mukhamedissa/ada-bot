import re
import logging
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandPattern:
    patterns: List[str]
    handler: Callable
    description: str
    command_name: str


class VoiceCommandDispatcher:
    
    def __init__(self):
        self.commands: List[CommandPattern] = []
        self._compiled_patterns: List[tuple] = []
        
    def register(self, patterns: List[str], command_name: str, description: str = ""):
        def decorator(handler: Callable):
            cmd = CommandPattern(patterns, handler, description, command_name)
            self.commands.append(cmd)
            
            compiled = [
                (re.compile(p, re.IGNORECASE), handler, command_name) 
                for p in patterns
            ]
            self._compiled_patterns.extend(compiled)
            
            logger.debug(f"Registered command '{command_name}' with {len(patterns)} patterns")
            return handler
        return decorator
    
    def dispatch(self, text: str) -> Optional[Dict[str, Any]]:
        text = text.lower().strip()
        
        for pattern, handler, command_name in self._compiled_patterns:
            match = pattern.search(text)
            if match:
                try:
                    result = handler(*match.groups())
                    
                    return {
                        'command': command_name,
                        'params': match.groups(),
                        'result': result,
                        'raw_text': text
                    }
                except Exception as e:
                    logger.error(f"Error executing command '{command_name}': {e}", exc_info=True)
                    return None
        
        return None
    
    def list_commands(self) -> List[Dict[str, str]]:
        return [
            {
                'name': cmd.command_name,
                'description': cmd.description,
                'patterns': cmd.patterns
            }
            for cmd in self.commands
        ]
