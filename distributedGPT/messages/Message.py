from dataclasses import dataclass
import json


@dataclass
class Message:
    _raw: dict
    content: str
    
    @staticmethod
    def is_valid(raw):
        assert isinstance(raw, dict), "all messages must be dict-like"
        assert 'content' in raw, "all messages must have a `content` field for string content"
        
    @classmethod 
    def from_raw(cls, raw):
        Message.is_valid(raw)
        return cls(_raw = raw, content = raw['content'])
    
    def pprint_message(self) -> None:
        from pygments import highlight
        from pygments.formatters.terminal256 import Terminal256Formatter
        from pygments.lexers.web import JsonLexer
        json_str = json.dumps(self._raw, indent=2, sort_keys=True)
        colorful = highlight(json_str, lexer=JsonLexer(), formatter=Terminal256Formatter())
        print(colorful) 