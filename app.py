import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import hashlib

# Import custom modules
from src.calendar_parser import CalendarParser
from src.models.calendar_event import CalendarEvent

# Page configuration
st.set_page_config(
    page_title="MindSync - Personal Wellbeing Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'calendar_provider' not in st.session_state:
    st.session_state.calendar_provider = None
if 'calendar_data' not in st.session_state:
    st.session_state.calendar_data = None
if 'parsed_events' not in st.session_state:
    st.session_state.parsed_events = []

# Simple user database (in production, use proper database)
USER_DATABASE = {
    "demo_user": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
    "test_user": "ef92c9ae4b6b63c4c84d5ddaf8b4f0b6e1f6c9c5d2f8f7e8d1c9a5b4e6f3d2a1"   # "test123"
}

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def handle_oauth_callback():
    """Handle OAuth callback from Google"""
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        auth_code = query_params['code']
        state = query_params['state']
        
        try:
            from src.google_calendar_api import GoogleCalendarAPI
            google_cal = GoogleCalendarAPI()
            
            # Exchange code for token
            if google_cal.exchange_code_for_token(auth_code, state):
                st.success("✅ Successfully connected to Google Calendar!")
                
                # Fetch calendar events
                events = google_cal.get_calendar_events()
                if events:
                    # Convert to our calendar format
                    calendar_data = {"events": events}
                    st.session_state.calendar_data = calendar_data
                    
                    # Parse events using existing parser
                    parser = CalendarParser()
                    parsed_events = parser.parse_google_calendar_events(events)
                    st.session_state.parsed_events = parsed_events
                    
                    st.session_state.calendar_provider = "google"
                    
                    # Clear query params and rerun
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("❌ Failed to fetch calendar events")
            else:
                st.error("❌ Failed to authenticate with Google Calendar")
        except Exception as e:
            st.error(f"❌ Error in OAuth callback: {str(e)}")

def main():
    # Handle OAuth callback first
    query_params = st.query_params
    if 'code' in query_params and 'state' in query_params:
        handle_oauth_callback()
        return
    
    # Rest of authentication flow
    if not st.session_state.authenticated:
        show_auth_page()
    elif st.session_state.calendar_provider is None:
        show_calendar_provider_selection()
    else:
        show_main_app()

def show_auth_page():
    """Display authentication page"""
    st.title("🧠 Welcome to MindSync")
    st.subheader("Your Personal Wellbeing Companion")
    st.markdown("---")
    
    # Center the auth form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        auth_mode = st.radio("Choose an option:", ["Login", "Create Account"], horizontal=True)
        
        with st.form("auth_form"):
            st.subheader(f"🔐 {auth_mode}")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            if auth_mode == "Create Account":
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            submit_button = st.form_submit_button(auth_mode, use_container_width=True)
            
            if submit_button:
                if auth_mode == "Login":
                    handle_login(username, password)
                else:
                    if auth_mode == "Create Account":
                        handle_signup(username, password, confirm_password if 'confirm_password' in locals() else "")
        
        # Demo credentials info
        st.markdown("---")
        st.info("**Demo Credentials:**\n- Username: `demo_user` Password: `password`\n- Username: `test_user` Password: `test123`")

def handle_login(username, password):
    """Handle user login"""
    if not username or not password:
        st.error("Please enter both username and password")
        return
    
    hashed_password = hash_password(password)
    
    if username in USER_DATABASE and USER_DATABASE[username] == hashed_password:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.success(f"Welcome back, {username}! 🎉")
        st.rerun()
    else:
        st.error("Invalid username or password")

def handle_signup(username, password, confirm_password):
    """Handle user account creation"""
    if not username or not password:
        st.error("Please enter both username and password")
        return
    
    if password != confirm_password:
        st.error("Passwords do not match")
        return
    
    if len(password) < 6:
        st.error("Password must be at least 6 characters long")
        return
    
    if username in USER_DATABASE:
        st.error("Username already exists")
        return
    
    # In a real app, you would save to a database
    USER_DATABASE[username] = hash_password(password)
    st.session_state.authenticated = True
    st.session_state.username = username
    st.success(f"Account created successfully! Welcome, {username}! 🎉")
    st.rerun()

def show_calendar_provider_selection():
    """Display calendar provider selection page"""
    st.title(f"👋 Welcome, {st.session_state.username}!")
    st.subheader("🗓️ Connect Your Calendar")
    
    # Center the provider selection
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Choose your calendar provider:")
        st.markdown("---")
        
        # Google Calendar option
        if st.button("📅 Google Calendar", use_container_width=True, help="Connect with Google Calendar"):
            load_calendar_data("google")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Outlook option
        if st.button("📧 Microsoft Outlook", use_container_width=True, help="Connect with Microsoft Outlook"):
            st.session_state.calendar_provider = "outlook"
            load_calendar_data("outlook")
            st.rerun()
        
        st.markdown("---")
        st.info("💡 Google Calendar will use live API integration. Outlook will load sample data for now.")
        
        # Logout option
        if st.button("🚪 Logout", type="secondary"):
            logout()

def load_calendar_data(provider):
    """Load calendar data based on provider"""
    if provider == "google":
        try:
            # Try to import and use Google Calendar API
            from src.google_calendar_api import GoogleCalendarAPI
            
            # Check if returning from OAuth
            query_params = st.query_params
            
            if 'code' in query_params:
                handle_oauth_callback()
                return
            
            # Initialize Google Calendar API
            google_cal = GoogleCalendarAPI()
            
            # Check if already authenticated
            if google_cal.is_authenticated():
                # Fetch events directly
                events = google_cal.get_calendar_events()
                if events:
                    calendar_data = {"events": events}
                    st.session_state.calendar_data = calendar_data
                    
                    # Parse events
                    parser = CalendarParser()
                    parsed_events = parser.parse_google_calendar_events(events)
                    st.session_state.parsed_events = parsed_events
                    st.session_state.calendar_provider = "google"
                    
                    st.success(f"✅ Successfully loaded {len(events)} events from Google Calendar!")
                    st.rerun()
                else:
                    st.error("❌ Failed to fetch calendar events")
                    st.stop()
            else:
                # Generate auth URL
                auth_url = google_cal.get_auth_url()
                if auth_url:
                    st.info("🔄 Click the link below to connect your Google Calendar:")
                    st.markdown(f"**[🔗 Connect Google Calendar]({auth_url})**")
                    st.markdown("You will be redirected back to this app after authorization.")
                    st.stop()
                else:
                    st.error("❌ Failed to generate authentication URL")
                    st.stop()
                    
        except ImportError:
            # Fallback to sample data if Google Calendar API not available
            st.warning("⚠️ Google Calendar API not available. Loading sample data...")
            with open("data/sample_calendars/google_sample.json", 'r') as f:
                calendar_data = json.load(f)
            
            st.session_state.calendar_data = calendar_data
            parser = CalendarParser()
            events = parser.parse_calendar(calendar_data)
            st.session_state.parsed_events = events
            st.session_state.calendar_provider = "google"
            
            st.success(f"✅ Loaded sample Google Calendar data with {len(events)} events!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error setting up Google Calendar: {str(e)}")
            st.info("Loading sample data as fallback...")
            
            # Fallback to sample data
            try:
                with open("data/sample_calendars/google_sample.json", 'r') as f:
                    calendar_data = json.load(f)
            except FileNotFoundError:
                with open("data/sample_calendars/mixed_day.json", 'r') as f:
                    calendar_data = json.load(f)
            
            st.session_state.calendar_data = calendar_data
            parser = CalendarParser()
            events = parser.parse_calendar(calendar_data)
            st.session_state.parsed_events = events
            st.session_state.calendar_provider = "google"
            
            st.success(f"✅ Loaded sample data with {len(events)} events!")
            st.rerun()
            
    elif provider == "outlook":
        # Outlook logic (sample data)
        try:
            sample_file = "data/sample_calendars/outlook_sample.json"
            try:
                with open(sample_file, 'r') as f:
                    calendar_data = json.load(f)
            except FileNotFoundError:
                with open("data/sample_calendars/busy_day.json", 'r') as f:
                    calendar_data = json.load(f)
            
            st.session_state.calendar_data = calendar_data
            
            # Parse calendar events
            parser = CalendarParser()
            events = parser.parse_calendar(calendar_data)
            st.session_state.parsed_events = events
            
            st.success(f"✅ Successfully connected to {provider.title()} Calendar! Loaded {len(events)} events.")
            
        except Exception as e:
            st.error(f"❌ Error loading {provider} calendar data: {str(e)}")

def logout():
    """Handle user logout"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.calendar_provider = None
    st.session_state.calendar_data = None
    st.session_state.parsed_events = []
    
    # Clear Google Calendar authentication if exists
    if 'google_credentials' in st.session_state:
        del st.session_state.google_credentials
    if 'oauth_state' in st.session_state:
        del st.session_state.oauth_state
        
    st.rerun()

def show_main_app():
    """Display the main application"""
    st.title("🧠 MindSync - Personal Wellbeing Companion")
    st.subheader(f"Connected to {st.session_state.calendar_provider.title()} Calendar")
    
    # Sidebar navigation
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.markdown(f"📅 **Provider:** {st.session_state.calendar_provider.title()}")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox("Navigate to:", [
        "📊 Dashboard",
        "📅 Calendar Data",
        "🔍 Stress Analysis", 
        "💡 Suggestions & Schedule",
        "📈 Analytics"
    ])
    
    # Sidebar actions
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Switch Calendar", help="Change calendar provider"):
            st.session_state.calendar_provider = None
            st.session_state.calendar_data = None
            st.session_state.parsed_events = []
            st.rerun()
    with col2:
        if st.button("🚪 Logout"):
            logout()
    
    # Page routing
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "📅 Calendar Data":
        calendar_data_page()
    elif page == "🔍 Stress Analysis":
        stress_analysis_page()
    elif page == "💡 Suggestions & Schedule":
        suggestions_page()
    elif page == "📈 Analytics":
        analytics_page()

def dashboard_page():
    """Main dashboard with overview"""
    st.header("📊 Dashboard Overview")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ No calendar data available!")
        return
    
    events = st.session_state.parsed_events
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Total Events", len(events))
    with col2:
        total_duration = sum(event.duration_minutes for event in events)
        st.metric("⏱️ Total Duration", f"{total_duration} min")
    with col3:
        meetings = len([e for e in events if e.is_meeting])
        st.metric("🤝 Meetings", meetings)
    with col4:
        focus_time = len([e for e in events if e.event_type == 'focus_time'])
        st.metric("🎯 Focus Blocks", focus_time)
    
    st.markdown("---")
    
    # Quick insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Today's Schedule")
        if events:
            for event in events[:5]:  # Show first 5 events
                st.markdown(f"**{event.start_time.strftime('%H:%M')}** - {event.title}")
                st.caption(f"{event.duration_minutes} min • {event.event_type}")
            
            if len(events) > 5:
                st.caption(f"... and {len(events) - 5} more events")
    
    with col2:
        st.subheader("⚡ Quick Stats")
        avg_duration = total_duration / len(events) if events else 0
        st.metric("Average Event Duration", f"{avg_duration:.1f} min")
        
        longest_event = max(events, key=lambda x: x.duration_minutes) if events else None
        if longest_event:
            st.metric("Longest Event", f"{longest_event.duration_minutes} min")
            st.caption(f"Event: {longest_event.title}")
    
    # Timeline preview
    if events:
        st.subheader("📅 Timeline Preview")
        create_timeline_chart(events[:10])  # Show first 10 events

def calendar_data_page():
    """Calendar data management page"""
    st.header("📅 Calendar Data Management")
    
    # Option to load different sample data
    st.subheader("📄 Load Sample Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Light Day Sample", use_container_width=True):
            load_sample_calendar("light_day")
    with col2:
        if st.button("📄 Busy Day Sample", use_container_width=True):
            load_sample_calendar("busy_day")
    with col3:
        if st.button("📄 Mixed Day Sample", use_container_width=True):
            load_sample_calendar("mixed_day")
    
    # Manual file upload option
    st.subheader("📁 Upload Custom Calendar File")
    uploaded_file = st.file_uploader(
        "Choose a JSON calendar file",
        type=['json'],
        help="Upload a JSON file containing your calendar events"
    )
    
    if uploaded_file is not None:
        try:
            calendar_data = json.load(uploaded_file)
            st.session_state.calendar_data = calendar_data
            
            # Parse calendar events
            parser = CalendarParser()
            events = parser.parse_calendar(calendar_data)
            st.session_state.parsed_events = events
            
            st.success(f"✅ Successfully loaded {len(events)} events!")
            
        except Exception as e:
            st.error(f"❌ Error loading calendar: {str(e)}")
    
    # Display current data if available
    if st.session_state.parsed_events:
        st.markdown("---")
        display_calendar_preview(st.session_state.parsed_events)

def load_sample_calendar(sample_type):
    """Load predefined sample calendar data"""
    try:
        with open(f"data/sample_calendars/{sample_type}.json", 'r') as f:
            calendar_data = json.load(f)
        
        st.session_state.calendar_data = calendar_data
        
        # Parse events
        parser = CalendarParser()
        events = parser.parse_calendar(calendar_data)
        st.session_state.parsed_events = events
        
        st.success(f"✅ Loaded {sample_type.replace('_', ' ')} sample with {len(events)} events!")
        
    except FileNotFoundError:
        st.error(f"❌ Sample file not found: {sample_type}.json")
    except Exception as e:
        st.error(f"❌ Error loading sample: {str(e)}")

def display_calendar_preview(events):
    """Display a preview of calendar events"""
    if not events:
        return
    
    st.subheader("📊 Calendar Preview")
    
    # Convert events to DataFrame for display
    event_data = []
    for event in events:
        event_data.append({
            'Title': event.title,
            'Start': event.start_time.strftime('%Y-%m-%d %H:%M'),
            'End': event.end_time.strftime('%Y-%m-%d %H:%M'),
            'Duration (min)': event.duration_minutes,
            'Type': event.event_type,
            'Participants': event.participants
        })
    
    df = pd.DataFrame(event_data)
    
    # Display events table
    st.dataframe(df, use_container_width=True)
    
    # Timeline visualization
    if len(events) > 0:
        st.subheader("📅 Timeline View")
        create_timeline_chart(events)

def create_timeline_chart(events):
    """Create a timeline visualization of events"""
    # Prepare data for timeline
    timeline_data = []
    for event in events:
        timeline_data.append({
            'Task': event.title[:30] + "..." if len(event.title) > 30 else event.title,
            'Start': event.start_time,
            'Finish': event.end_time,
            'Type': event.event_type
        })
    
    df_timeline = pd.DataFrame(timeline_data)
    
    # Create Gantt chart
    fig = px.timeline(
        df_timeline,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Type",
        title="Daily Schedule Timeline"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def stress_analysis_page():
    st.header("🔍 Stress Analysis")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ Please load calendar data first!")
        return
    
    st.info("🚧 Stress prediction functionality will be implemented in Week 2")
    
    # Placeholder for stress analysis
    st.subheader("Stress Prediction Rules Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.slider("Max consecutive meetings", 1, 10, 3)
        st.slider("Minimum break time (minutes)", 5, 60, 15)
    with col2:
        st.slider("Long meeting threshold (minutes)", 30, 180, 60)
        st.slider("Meeting density threshold", 1, 20, 8)

def suggestions_page():
    st.header("💡 Suggestions & Schedule")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ Please load calendar data first!")
        return
    
    st.info("🚧 Suggestion engine will be implemented in Week 2-3")

def analytics_page():
    st.header("📈 Analytics")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ Please load calendar data first!")
        return
    
    st.info("🚧 Analytics dashboard will be implemented in Week 3-4")

if __name__ == "__main__":
    main()