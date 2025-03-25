from datetime import datetime, timedelta
import pytz
from functions.functioncallingbase import FunctionCallingBase
from services.google_calendar_service import GoogleCalendarService

class ListCalendarEvents(FunctionCallingBase):
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        super().__init__()

    def _get_function_definition(self):
        # Get current date and time in the specified timezone for examples
        now = datetime.now(pytz.timezone(self.calendar_service.timezone))
        week_later = now + timedelta(days=7)
        
        return {
            "name": "list_calendar_events",
            "description": f"Lists your upcoming calendar events. Current time reference: {now.isoformat()} ({self.calendar_service.timezone})",
            "operation_type": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default: 10)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    },
                    "time_min": {
                        "type": "string",
                        "description": f"Start of the search range in ISO format (YYYY-MM-DDTHH:MM:SS). Default: current time",
                        "example": now.isoformat()
                    },
                    "time_max": {
                        "type": "string",
                        "description": f"End of the search range in ISO format (YYYY-MM-DDTHH:MM:SS). Default: 7 days from now",
                        "example": week_later.isoformat()
                    },
                    "timezone": {
                        "type": "string",
                        "description": f"Timezone for the search (default: {self.calendar_service.timezone}). Use IANA timezone names (e.g., America/New_York, Europe/London)",
                        "default": self.calendar_service.timezone
                    }
                },
                "additionalProperties": False
            }
        }

    def execute(self, **kwargs):
        return self.calendar_service.list_events(
            max_results=kwargs.get('max_results', 10),
            time_min=kwargs.get('time_min'),
            time_max=kwargs.get('time_max'),
            timezone=kwargs.get('timezone', self.calendar_service.timezone)
        ) 