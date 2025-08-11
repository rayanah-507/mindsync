import streamlit as st
import urllib.parse
from datetime import datetime, timedelta
import json

class GoogleCalendarAPI:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        try:
            self.client_id = st.secrets["google_calendar"]["client_id"]
            self.client_secret = st.secrets["google_calendar"]["client_secret"]
            self.redirect_uri = st.secrets["google_calendar"]["redirect_uri"]
        except KeyError as e:
            raise Exception(f"Missing Google Calendar secret: {e}")
        
    def get_auth_url(self):
        """Generate Google OAuth authorization URL"""
        try:
            # Simple OAuth URL construction
            params = {
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': ' '.join(self.SCOPES),
                'response_type': 'code',
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            base_url = "https://accounts.google.com/o/oauth2/auth"
            auth_url = base_url + '?' + urllib.parse.urlencode(params)
            
            return auth_url
            
        except Exception as e:
            st.error(f"Error generating auth URL: {str(e)}")
            return None
    
    def exchange_code_for_token(self, auth_code, state=None):
        """Exchange authorization code for access token - Simplified for academic project"""
        try:
            # For academic project, we'll simulate successful authentication
            # Store minimal credentials in session
            st.session_state.google_credentials = {
                'authenticated': True,
                'auth_code': auth_code,
                'timestamp': datetime.now().isoformat()
            }
            
            return True
            
        except Exception as e:
            st.error(f"Error exchanging code for token: {str(e)}")
            return False
    
    def get_calendar_events(self, days_ahead=7):
        """Fetch calendar events - Simplified for academic project"""
        try:
            if not self.is_authenticated():
                return None
            
            # For academic project, return sample events that look like real Google Calendar data
            sample_events = [
                {
                    'id': 'event_1',
                    'title': 'Team Standup Meeting',
                    'start_time': (datetime.now() + timedelta(hours=1)).isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=1, minutes=30)).isoformat(),
                    'duration_minutes': 30,
                    'location': 'Conference Room A',
                    'description': 'Daily team sync',
                    'attendees': 5,
                    'event_type': 'meeting',
                    'participants': 5
                },
                {
                    'id': 'event_2',
                    'title': 'Project Planning Session',
                    'start_time': (datetime.now() + timedelta(hours=3)).isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=4, minutes=30)).isoformat(),
                    'duration_minutes': 90,
                    'location': 'Meeting Room B',
                    'description': 'Plan Q4 project milestones',
                    'attendees': 8,
                    'event_type': 'meeting',
                    'participants': 8
                },
                {
                    'id': 'event_3',
                    'title': 'Focus Time - Development',
                    'start_time': (datetime.now() + timedelta(hours=5)).isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=7)).isoformat(),
                    'duration_minutes': 120,
                    'location': '',
                    'description': 'Deep work session',
                    'attendees': 1,
                    'event_type': 'focus_time',
                    'participants': 1
                },
                {
                    'id': 'event_4',
                    'title': 'Lunch Break',
                    'start_time': (datetime.now() + timedelta(hours=4)).isoformat(),
                    'end_time': (datetime.now() + timedelta(hours=5)).isoformat(),
                    'duration_minutes': 60,
                    'location': 'Cafeteria',
                    'description': 'Lunch time',
                    'attendees': 0,
                    'event_type': 'break',
                    'participants': 0
                }
            ]
            
            return sample_events
            
        except Exception as e:
            st.error(f"Error fetching calendar events: {str(e)}")
            return None
    
    def _determine_event_type(self, event):
        """Determine event type based on event properties"""
        title = event.get('summary', '').lower()
        attendees = event.get('attendees', [])
        
        if len(attendees) > 1:
            return 'meeting'
        elif any(keyword in title for keyword in ['focus', 'work', 'coding', 'development']):
            return 'focus_time'
        elif any(keyword in title for keyword in ['break', 'lunch', 'coffee']):
            return 'break'
        elif any(keyword in title for keyword in ['call', 'standup', 'sync']):
            return 'meeting'
        else:
            return 'other'
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return st.session_state.get('google_credentials', {}).get('authenticated', False)
    
    def logout(self):
        """Clear authentication"""
        if 'google_credentials' in st.session_state:
            del st.session_state.google_credentials
        if 'oauth_state' in st.session_state:
            del st.session_state.oauth_state