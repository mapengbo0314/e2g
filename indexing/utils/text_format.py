"""Simple textproto parser for local bundle configuration."""

import re
from typing import Any, Type, TypeVar

T = TypeVar("T")

class ParseError(Exception):
    """Raised when textproto parsing fails."""

def Parse(text: str, message: T) -> T:
    """Parses a textproto string into a dataclass message.
    
    This is a simplified parser for the Glimpse bundle configuration subset.
    """
    lines = text.splitlines()
    _parse_recursive(lines, message, 0)
    return message

def _parse_recursive(lines: list[str], obj: Any, start_line: int) -> int:
    i = start_line
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        if line == "}":
            return i + 1
        
        # Match key: value or key: {
        match = re.match(r'^(\w+)\s*:\s*(.*)$', line)
        if not match:
            # Try key { (without colon)
            match = re.match(r'^(\w+)\s*\{(.*)$', line)
            if not match:
                i += 1
                continue
        
        key = match.group(1)
        value = match.group(2).strip()
        
        if not hasattr(obj, key):
            i += 1
            continue
            
        attr_type = type(getattr(obj, key))
        
        if value == "{":
            # Nested message
            field_val = getattr(obj, key)
            if isinstance(field_val, list):
                # repeated field
                # We need to know what type of items are in the list.
                # Since we are using dataclasses, we can look at __annotations__
                item_type = obj.__annotations__[key].__args__[0]
                new_item = item_type()
                i = _parse_recursive(lines, new_item, i + 1)
                field_val.append(new_item)
            else:
                i = _parse_recursive(lines, field_val, i + 1)
        else:
            # Scalar value
            # Strip quotes if string
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            field_val = getattr(obj, key)
            if isinstance(field_val, list):
                field_val.append(value)
            else:
                setattr(obj, key, value)
            i += 1
    return i
