from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import pytz
from tzlocal import get_localzone

class GoogleCalendarService:
    def __init__(self):
        self.timezone = str(get_localzone())
        self.scopes = ['https://www.googleapis.com/auth/calendar']

    def _get_credentials(self):
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), '..', 'token.pickle')
        credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise Exception("credentials.json file not found. Please set up Google Calendar API credentials first.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def _format_datetime_for_google(self, dt_str, timezone_str):
        """Convert datetime string to RFC3339 format with Z timezone indicator"""
        try:
            # If datetime is already provided in ISO format
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # If datetime is None or invalid, return None
            return None

        # Convert to UTC
        tz = pytz.timezone(timezone_str)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        utc_dt = dt.astimezone(pytz.UTC)
        
        # Format in RFC3339 format
        return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def create_event(self, summary, start_time, end_time, description="", timezone=None, attendees=None, add_conference=False, recurrence=None, send_updates='none'):
        """Creates a calendar event"""
        timezone = timezone or self.timezone
        try:
            # Validate timezone
            pytz.timezone(timezone)
            
            # Format times in RFC3339
            start_time = self._format_datetime_for_google(start_time, timezone)
            end_time = self._format_datetime_for_google(end_time, timezone)
            
            creds = self._get_credentials()
            service = build('calendar', 'v3', credentials=creds)

            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': timezone,
                },
            }

            # Add attendees if provided
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            # Add conference data if requested
            if add_conference:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"{summary}-{start_time}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }

            # Add recurrence if provided
            if recurrence:
                event['recurrence'] = recurrence

            # Create event with additional parameters
            event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1 if add_conference else 0,
                sendUpdates=send_updates
            ).execute()

            return {
                "success": True,
                "message": f"Event created successfully in {timezone}. Event ID: {event.get('id')}",
                "event_link": event.get('htmlLink'),
                "conference_link": event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri') if add_conference else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create event: {str(e)}"
            }

    def list_events(self, max_results=10, time_min=None, time_max=None, timezone=None):
        """Lists upcoming calendar events"""
        timezone = timezone or self.timezone
        try:
            # Validate timezone
            tz = pytz.timezone(timezone)
            
            # Set default time range if not provided
            now = datetime.now(tz)
            if time_min is None:
                time_min = now
            if time_max is None:
                time_max = now + timedelta(days=7)

            # Format times in RFC3339
            time_min_str = self._format_datetime_for_google(time_min.isoformat() if isinstance(time_min, datetime) else time_min, timezone)
            time_max_str = self._format_datetime_for_google(time_max.isoformat() if isinstance(time_max, datetime) else time_max, timezone)

            creds = self._get_credentials()
            service = build('calendar', 'v3', credentials=creds)

            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return {
                    "success": True,
                    "message": "No upcoming events found.",
                    "events": []
                }

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                formatted_events.append({
                    "id": event['id'],
                    "summary": event.get('summary', 'No title'),
                    "description": event.get('description', ''),
                    "start": start,
                    "end": end,
                    "link": event.get('htmlLink')
                })

            return {
                "success": True,
                "message": f"Found {len(formatted_events)} events",
                "events": formatted_events
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list events: {str(e)}"
            } 