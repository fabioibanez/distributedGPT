from dataclasses import dataclass

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