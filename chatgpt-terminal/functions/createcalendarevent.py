from datetime import datetime, timedelta
import pytz
from functions.functioncallingbase import FunctionCallingBase
from services.google_calendar_service import GoogleCalendarService

class CreateCalendarEvent(FunctionCallingBase):
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        super().__init__()

    def _get_function_definition(self):
        # Get current date and time in the specified timezone for examples
        now = datetime.now(pytz.timezone(self.calendar_service.timezone))
        current_time = now.strftime("%Y-%m-%dT%H:%M:%S")
        one_hour_later = (now.replace(minute=0, second=0, microsecond=0) + 
                         timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        
        return {
            "name": "create_calendar_event",
            "description": f"Creates an event in the calendar of the user. Current time reference: {current_time} ({self.calendar_service.timezone})",
            "operation_type": "write",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Title of the event"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the event"
                    },
                    "start_time": {
                        "type": "string",
                        "description": f"Start time in ISO format (YYYY-MM-DDTHH:MM:SS). Example for now: {current_time}",
                        "example": current_time
                    },
                    "end_time": {
                        "type": "string",
                        "description": f"End time in ISO format (YYYY-MM-DDTHH:MM:SS). Example for 2 hours from now: {one_hour_later}",
                        "example": one_hour_later
                    },
                    "timezone": {
                        "type": "string",
                        "description": f"Timezone for the event (default: {self.calendar_service.timezone}). Use IANA timezone names (e.g., America/New_York, Europe/London)",
                        "default": self.calendar_service.timezone
                    },
                    "attendees": {
                        "type": "array",
                        "description": "List of attendee email addresses",
                        "items": {
                            "type": "string",
                            "format": "email"
                        }
                    },
                    "add_conference": {
                        "type": "boolean",
                        "description": "Whether to add a Google Meet conference to the event. If not mentioned, it must be set to False",
                        "default": False
                    },
                    "recurrence": {
                        "type": "array",
                        "description": "RRULE strings for recurring events (e.g., ['RRULE:FREQ=DAILY;COUNT=2'])",
                        "items": {
                            "type": "string"
                        }
                    },
                    "send_updates": {
                        "type": "string",
                        "description": "Whether to send notifications about the creation of the event. If not mentioned, it will be set to 'none'",
                        "enum": ["all", "externalOnly", "none"],
                        "default": "none"
                    }
                },
                "required": ["summary", "start_time", "end_time"],
                "additionalProperties": False
            }
        }

    def execute(self, **kwargs):
        return self.calendar_service.create_event(
            summary=kwargs.get('summary'),
            description=kwargs.get('description', ''),
            start_time=kwargs.get('start_time'),
            end_time=kwargs.get('end_time'),
            timezone=kwargs.get('timezone', self.calendar_service.timezone),
            attendees=kwargs.get('attendees', []),
            add_conference=kwargs.get('add_conference', False),
            recurrence=kwargs.get('recurrence', []),
            send_updates=kwargs.get('send_updates', 'none')
        ) 