import streamlit as st
import urllib.parse
import requests
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
        """Exchange authorization code for access token"""
        try:
            # Exchange authorization code for access token
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                'code': auth_code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Store credentials in session
                st.session_state.google_credentials = {
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in'),
                    'token_type': token_data.get('token_type', 'Bearer'),
                    'authenticated': True,
                    'timestamp': datetime.now().isoformat()
                }
                
                return True
            else:
                st.error(f"Failed to exchange token: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            st.error(f"Error exchanging code for token: {str(e)}")
            return False
    
    def get_calendar_events(self, days_ahead=7):
        """Fetch real calendar events from Google Calendar API"""
        try:
            if not self.is_authenticated():
                return None
            
            # Get access token
            access_token = st.session_state.google_credentials.get('access_token')
            
            if not access_token:
                st.error("No access token available")
                return None
            
            # Calculate time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Google Calendar API endpoint
            calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
            
            # Headers with authorization
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Accept': 'application/json'
            }
            
            # Parameters
            params = {
                'timeMin': time_min,
                'timeMax': time_max,
                'maxResults': 50,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            # Make API request
            response = requests.get(calendar_url, headers=headers, params=params)
            
            if response.status_code == 200:
                events_data = response.json()
                events = events_data.get('items', [])
                
                # Convert to our format
                calendar_events = []
                for event in events:
                    # Handle different date/time formats
                    start = event.get('start', {})
                    end = event.get('end', {})
                    
                    # Parse dates
                    if 'dateTime' in start:
                        start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                    elif 'date' in start:
                        # All-day event
                        start_dt = datetime.fromisoformat(start['date'] + 'T00:00:00')
                        end_dt = datetime.fromisoformat(end['date'] + 'T23:59:59')
                    else:
                        continue  # Skip events without proper time data
                    
                    # Extract attendees
                    attendees = event.get('attendees', [])
                    participants = len(attendees)
                    
                    calendar_events.append({
                        'id': event.get('id', ''),
                        'title': event.get('summary', 'No Title'),
                        'start_time': start_dt.isoformat(),
                        'end_time': end_dt.isoformat(),
                        'duration_minutes': int((end_dt - start_dt).total_seconds() / 60),
                        'location': event.get('location', ''),
                        'description': event.get('description', ''),
                        'attendees': participants,
                        'event_type': self._determine_event_type(event),
                        'participants': participants
                    })
                
                return calendar_events
                
            elif response.status_code == 401:
                st.error("Authentication expired. Please reconnect your Google Calendar.")
                self.logout()
                return None
            else:
                st.error(f"Failed to fetch events: {response.status_code} - {response.text}")
                return None
            
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
        elif any(keyword in title for keyword in ['call', 'standup', 'sync', 'meeting']):
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