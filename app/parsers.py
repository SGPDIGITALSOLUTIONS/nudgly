"""Text parsing functionality for natural language reminders."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
import dateparser
import pytz
from openai import OpenAI

from .settings import OPENAI_API_KEY, TZ, REMINDER_KEYWORDS, LIST_KEYWORDS, DONE_KEYWORDS, CANCEL_KEYWORDS


@dataclass
class ParsedReminder:
    """Parsed reminder data."""
    text: str
    due_at: Optional[datetime] = None
    recurrence: Optional[str] = None
    command_type: str = "reminder"  # reminder, list, done, cancel


class MessageParser:
    """Parser for natural language reminder messages."""
    
    def __init__(self):
        # Handle invalid timezone in serverless environment
        try:
            self.timezone = pytz.timezone(TZ)
        except:
            self.timezone = pytz.UTC  # Fallback to UTC
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    
    def parse_message(self, message: str) -> ParsedReminder:
        """Parse a message and extract reminder information."""
        message = message.strip()
        
        # Detect command type first
        command_type = self._detect_command_type(message)
        
        if command_type == "list":
            return ParsedReminder(text=message, command_type="list")
        elif command_type in ["done", "cancel"]:
            return ParsedReminder(text=message, command_type=command_type)
        
        # Parse reminder
        return self._parse_reminder(message)
    
    def _detect_command_type(self, message: str) -> str:
        """Detect the type of command from the message."""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in LIST_KEYWORDS):
            return "list"
        elif any(keyword in message_lower for keyword in DONE_KEYWORDS):
            return "done"
        elif any(keyword in message_lower for keyword in CANCEL_KEYWORDS):
            return "cancel"
        
        return "reminder"
    
    def _parse_reminder(self, message: str) -> ParsedReminder:
        """Parse a reminder message to extract task and timing."""
        # Clean up common reminder prefixes
        clean_message = self._clean_reminder_prefix(message)
        
        # Try to extract time/date information using dateparser
        due_at, cleaned_text = self._extract_datetime(clean_message)
        
        # If dateparser failed, try GPT as fallback
        if not due_at and self.openai_client:
            due_at, cleaned_text = self._gpt_parse_fallback(clean_message)
        
        # If still no date/time, default to current time + 1 hour
        if not due_at:
            due_at = datetime.now(self.timezone) + timedelta(hours=1)
            cleaned_text = clean_message
        
        return ParsedReminder(
            text=cleaned_text.strip(),
            due_at=due_at,
            command_type="reminder"
        )
    
    def _clean_reminder_prefix(self, message: str) -> str:
        """Remove common reminder prefixes."""
        message_lower = message.lower()
        
        for keyword in REMINDER_KEYWORDS:
            if message_lower.startswith(keyword):
                # Remove the keyword and any following colon or "to"
                remaining = message[len(keyword):].strip()
                if remaining.startswith(":"):
                    remaining = remaining[1:].strip()
                elif remaining.lower().startswith("to "):
                    remaining = remaining[3:].strip()
                return remaining
        
        return message
    
    def _extract_datetime(self, text: str) -> Tuple[Optional[datetime], str]:
        """Extract datetime from text using dateparser."""
        # Common time patterns to try
        patterns = [
            r'\b(?:at\s+)?(\d{1,2}(?::\d{2})?(?:\s*(?:am|pm))?)\b',
            r'\b(tomorrow|today|tonight)\b',
            r'\b(in\s+\d+\s+(?:minutes?|hours?|days?))\b',
            r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b',
        ]
        
        # Try to parse the entire text first
        parsed_date = dateparser.parse(
            text, 
            settings={
                'PREFER_DATES_FROM': 'future',
                'TIMEZONE': TZ,
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )
        
        if parsed_date:
            # Try to find what part was the date/time and remove it
            words = text.split()
            cleaned_words = []
            
            for word in words:
                word_date = dateparser.parse(word, settings={'TIMEZONE': TZ})
                if not word_date:
                    cleaned_words.append(word)
            
            cleaned_text = ' '.join(cleaned_words)
            return parsed_date, cleaned_text
        
        # If full text parsing failed, try to find time patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_part = match.group(1)
                parsed_date = dateparser.parse(
                    time_part,
                    settings={
                        'PREFER_DATES_FROM': 'future',
                        'TIMEZONE': TZ,
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                if parsed_date:
                    # Remove the matched time part from text
                    cleaned_text = text.replace(match.group(0), '').strip()
                    return parsed_date, cleaned_text
        
        return None, text
    
    def _gpt_parse_fallback(self, text: str) -> Tuple[Optional[datetime], str]:
        """Use GPT to parse ambiguous date/time expressions."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a helpful assistant that extracts reminder information.
                        Current timezone: {TZ}
                        Current time: {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M')}
                        
                        Extract the task and when it should happen from the user's message.
                        Respond with JSON format:
                        {{"task": "cleaned task text", "when": "ISO datetime or null"}}
                        
                        If no clear time is mentioned, return null for "when".
                        """
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            task = result.get("task", text)
            when_str = result.get("when")
            
            if when_str:
                when_dt = datetime.fromisoformat(when_str.replace('Z', '+00:00'))
                # Convert to local timezone
                when_dt = when_dt.astimezone(self.timezone)
                return when_dt, task
            
        except Exception as e:
            print(f"GPT parsing failed: {e}")
        
        return None, text


# Global parser instance
parser = MessageParser()


def parse_text(message: str) -> ParsedReminder:
    """Parse a text message into a structured reminder."""
    return parser.parse_message(message)

