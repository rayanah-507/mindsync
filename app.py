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
    
    if 'code' in query_params:
        auth_code = query_params['code']
        
        st.info("🔄 Processing Google Calendar authentication...")
        
        try:
            from src.google_calendar_api import GoogleCalendarAPI
            google_cal = GoogleCalendarAPI()
            
            # Exchange code for token
            if google_cal.exchange_code_for_token(auth_code):
                st.success("✅ Authentication successful!")
                
                # Fetch calendar events immediately
                events = google_cal.get_calendar_events()
                
                if events and len(events) > 0:
                    # Store everything in session state
                    calendar_data = {"events": events}
                    st.session_state.calendar_data = calendar_data
                    
                    # Parse events
                    parser = CalendarParser()
                    parsed_events = parser.parse_google_calendar_events(events)
                    st.session_state.parsed_events = parsed_events
                    st.session_state.calendar_provider = "google"
                    
                    st.success(f"✅ Loaded {len(events)} events from Google Calendar!")
                    
                    # Clear query params
                    st.query_params.clear()
                    
                    # Small delay then redirect
                    import time
                    time.sleep(2)
                    st.rerun()
                    
                else:
                    st.warning("⚠️ No events found in your Google Calendar")
                    # Still set up with empty events
                    st.session_state.calendar_data = {"events": []}
                    st.session_state.parsed_events = []
                    st.session_state.calendar_provider = "google"
                    
                    st.query_params.clear()
                    st.rerun()
            else:
                st.error("❌ Failed to authenticate with Google Calendar")
                
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")

def main():
    # Handle OAuth callback first
    query_params = st.query_params
    if 'code' in query_params:
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
    
    # DEBUG/RESET SECTION
    st.write("🔍 Current session state:")
    st.write(f"calendar_provider: {st.session_state.get('calendar_provider')}")
    st.write(f"google_credentials: {'Yes' if 'google_credentials' in st.session_state else 'No'}")
    
    # Reset button for debugging
    if st.button("🔄 Reset Session"):
        st.session_state.calendar_provider = None
        st.session_state.calendar_data = None
        st.session_state.parsed_events = []
        if 'google_credentials' in st.session_state:
            del st.session_state.google_credentials
        st.rerun()
    
    st.markdown("---")
    
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
            from src.google_calendar_api import GoogleCalendarAPI
            
            # Initialize Google Calendar API
            google_cal = GoogleCalendarAPI()
            
            # DEBUG: Check authentication status
            st.write("🔍 DEBUG: Checking authentication...")
            is_auth = google_cal.is_authenticated()
            st.write(f"🔍 Is authenticated: {is_auth}")
            
            if 'google_credentials' in st.session_state:
                st.write("🔍 Google credentials found in session")
                st.write(f"🔍 Credentials: {st.session_state.google_credentials}")
            else:
                st.write("🔍 No Google credentials in session")
            
            # Check if already authenticated
            if google_cal.is_authenticated():
                st.info("✅ Already authenticated! Loading your calendar events...")
                
                # DEBUG: Try to fetch events
                st.write("🔍 Fetching events...")
                events = google_cal.get_calendar_events()
                st.write(f"🔍 Events returned: {events}")
                
                if events:
                    st.write(f"🔍 Number of events: {len(events)}")
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
                    st.error("❌ No events returned or failed to fetch")
                    return
            else:
                # Not authenticated - show auth URL
                st.write("🔍 Not authenticated, generating auth URL...")
                auth_url = google_cal.get_auth_url()
                if auth_url:
                    st.info("🔄 Click the link below to connect your Google Calendar:")
                    st.markdown(f"**[🔗 Connect Google Calendar]({auth_url})**")
                    st.markdown("You will be redirected back to this app after authorization.")
                    st.stop()
                else:
                    st.error("❌ Failed to generate authentication URL")
                    st.stop()
                    
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
    elif provider == "outlook":
        # Outlook logic stays the same
        try:
            sample_file = "data/sample_calendars/outlook_sample.json"
            try:
                with open(sample_file, 'r') as f:
                    calendar_data = json.load(f)
            except FileNotFoundError:
                with open("data/sample_calendars/busy_day.json", 'r') as f:
                    calendar_data = json.load(f)
            
            st.session_state.calendar_data = calendar_data
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
    
    # Add Google Calendar status
    if st.session_state.calendar_provider == "google":
        try:
            from src.google_calendar_api import GoogleCalendarAPI
            google_cal = GoogleCalendarAPI()
            if google_cal.is_authenticated():
                st.sidebar.markdown("✅ **Google Calendar Connected**")
                if st.sidebar.button("🔌 Disconnect Google Calendar"):
                    google_cal.logout()
                    st.session_state.calendar_provider = None
                    st.session_state.calendar_data = None
                    st.session_state.parsed_events = []
                    st.rerun()
            else:
                st.sidebar.markdown("❌ **Google Calendar Not Connected**")
        except:
            st.sidebar.markdown("❌ **Google Calendar Not Connected**")
    
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox("Navigate to:", [
        "📊 Dashboard",
        "📅 Calendar Data",
        "🔍 Stress Analysis", 
        "💡 Suggestions & Schedule"
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


def dashboard_page():
    """Main dashboard with overview"""
    st.header("📊 Dashboard Overview")
    
    # DEBUG INFO
    st.write("🔍 DEBUG INFO:")
    st.write(f"parsed_events in session: {len(st.session_state.parsed_events) if st.session_state.parsed_events else 'None'}")
    st.write(f"calendar_data in session: {st.session_state.calendar_data}")
    st.write(f"calendar_provider: {st.session_state.calendar_provider}")
    
    if 'google_credentials' in st.session_state:
        st.write(f"google_credentials: {st.session_state.google_credentials}")
    else:
        st.write("No google_credentials in session")
    
    st.write("---")
    
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
    
    # Display current connection status
    if st.session_state.calendar_provider == "google":
        try:
            from src.google_calendar_api import GoogleCalendarAPI
            google_cal = GoogleCalendarAPI()
            if google_cal.is_authenticated():
                st.success("✅ Connected to Google Calendar")
                
                # Refresh data option
                if st.button("🔄 Refresh Calendar Data"):
                    events = google_cal.get_calendar_events()
                    if events:
                        calendar_data = {"events": events}
                        st.session_state.calendar_data = calendar_data
                        
                        parser = CalendarParser()
                        parsed_events = parser.parse_google_calendar_events(events)
                        st.session_state.parsed_events = parsed_events
                        
                        st.success(f"✅ Refreshed! Loaded {len(events)} events.")
                        st.rerun()
            else:
                st.warning("⚠️ Google Calendar not connected")
        except:
            pass
    
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
            'Participants': event.participants,
            'Location': event.location if event.location else '',  
            'Description': event.description if event.description else '' 
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
    """Complete stress analysis page with 7-day forecast."""
    st.header("🔍 Stress Analysis")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ Please load calendar data first!")
        return
    
    # Import stress calculator
    try:
        from src.stress_predictor import MeetingStressCalculator
        calculator = MeetingStressCalculator()
    except ImportError as e:
        st.error(f"❌ Error importing stress calculator: {str(e)}")
        return
    
    events = st.session_state.parsed_events
    
    # Calculate 7-day stress forecast
    with st.spinner("🧠 Analyzing 7-day stress patterns..."):
        forecast_data = []
        today = datetime.now().date()
        
        for i in range(7):
            target_date = today + timedelta(days=i)
            stress_result = calculator.calculate_daily_stress(events, target_date)
            forecast_data.append({
                'date': target_date,
                'day_name': target_date.strftime('%A'),
                'stress_score': stress_result['daily_stress_score'],
                'stress_level': stress_result['stress_level'],
                'meeting_count': stress_result['meeting_analysis']['total_meetings'],
                'meeting_hours': stress_result['meeting_analysis']['total_hours'],
                'components': stress_result['components'],
                'recommendations': stress_result['recommendations']
            })
    
    # Today's detailed analysis (first day)
    today_analysis = forecast_data[0]
    
    # 7-Day Overview Chart
    st.subheader("📅 7-Day Stress Forecast")
    
    import pandas as pd
    import plotly.express as px
    
    # Create forecast dataframe
    forecast_df = pd.DataFrame([
        {
            'Date': item['date'].strftime('%m/%d'),
            'Day': item['day_name'][:3],
            'Stress Score': item['stress_score'],
            'Meetings': item['meeting_count'],
            'Hours': item['meeting_hours']
        }
        for item in forecast_data
    ])
    
    # Stress forecast chart
    fig = px.line(
        forecast_df,
        x='Day',
        y='Stress Score',
        title='7-Day Stress Forecast',
        markers=True,
        hover_data=['Date', 'Meetings', 'Hours']
    )
    
    # Add color zones
    fig.add_hline(y=25, line_dash="dash", line_color="green", annotation_text="Low Stress")
    fig.add_hline(y=50, line_dash="dash", line_color="yellow", annotation_text="Moderate")
    fig.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="High Stress")
    
    fig.update_layout(height=400, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    # Quick 7-day summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_stress = sum(item['stress_score'] for item in forecast_data) / 7
        st.metric("📊 Avg Stress", f"{avg_stress:.1f}/100")
    with col2:
        high_stress_days = sum(1 for item in forecast_data if item['stress_score'] > 60)
        st.metric("🔥 High Stress Days", high_stress_days)
    with col3:
        total_meetings = sum(item['meeting_count'] for item in forecast_data)
        st.metric("📅 Total Meetings", total_meetings)
    with col4:
        total_hours = sum(item['meeting_hours'] for item in forecast_data)
        st.metric("⏱️ Total Hours", f"{total_hours:.1f}h")
    
    # Week recommendations
    if high_stress_days >= 3:
        st.error("🚨 **HIGH STRESS WEEK DETECTED** - Consider rescheduling some meetings!")
    elif avg_stress > 50:
        st.warning("⚠️ **BUSY WEEK** - Plan recovery time and prioritize breaks.")
    else:
        st.success("✅ **MANAGEABLE WEEK** - Good work-life balance!")
    
    # Today's Detailed Analysis
    st.markdown("---")
    st.subheader(f"🎯 Today's Analysis ({today_analysis['day_name']})")
    
    # Today's stress display
    stress_score = today_analysis['stress_score']
    stress_level = today_analysis['stress_level']
    
    # Color-coded stress display
    if stress_score <= 25:
        color = "🟢"
        bg_color = "#d4edda"
    elif stress_score <= 50:
        color = "🟡" 
        bg_color = "#fff3cd"
    elif stress_score <= 75:
        color = "🟠"
        bg_color = "#f8d7da"
    else:
        color = "🚨"
        bg_color = "#f5c6cb"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="margin: 0;">{color} Today's Stress Score</h2>
            <h1 style="margin: 10px 0; font-size: 3em;">{stress_score}/100</h1>
            <h3 style="margin: 0; color: #666;">{stress_level}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Today's meeting overview
        meeting_analysis = today_analysis
        st.metric("📅 Meetings Today", meeting_analysis['meeting_count'])
        st.metric("⏱️ Meeting Hours", f"{meeting_analysis['meeting_hours']}h")
        if meeting_analysis['meeting_count'] > 0:
            components = meeting_analysis['components']
            lunch_meetings = components.get('lunch_disruption_penalty', 0) > 0
            st.metric("🍽️ Lunch Disruption", "Yes" if lunch_meetings else "No")
    
    # Today's recommendations
    st.subheader("💡 Today's Recommendations")
    recommendations = today_analysis['recommendations']
    for i, rec in enumerate(recommendations, 1):
        if rec.startswith("🚨") or rec.startswith("⚠️"):
            st.error(f"{i}. {rec}")
        elif rec.startswith("Great") or rec.startswith("✅"):
            st.success(f"{i}. {rec}")
        else:
            st.info(f"{i}. {rec}")
    
    # Today's stress components breakdown
    st.markdown("---")
    st.subheader("📊 Today's Stress Components")
    
    components = today_analysis['components']
    
    # Create breakdown chart with CORRECT component names
    component_data = {
        'Component': [
            'Base Meeting Load',
            'Back-to-Back Penalty', 
            'Lunch Disruption',
            'Long Meeting Penalty',
            'Overload Penalty'
        ],
        'Stress Points': [
            components['base_meeting_stress'],
            components['back_to_back_penalty'],
            components['lunch_disruption_penalty'],
            components['long_meeting_penalty'], 
            components['overload_penalty']
        ],
        'Description': [
            f"Core stress from {components['meeting_count']} meetings ({components['total_meeting_hours']}h)",
            'Penalty for meetings with <10min gaps',
            'Stress from meetings during lunch hours (1-2 PM)',
            'Penalty for meetings longer than 90 minutes',
            'Penalty for excessive daily meeting load'
        ]
    }
    
    df_components = pd.DataFrame(component_data)
    
    # Bar chart of stress components
    fig_components = px.bar(
        df_components,
        x='Component',
        y='Stress Points', 
        title="Today's Stress Component Breakdown",
        color='Stress Points',
        color_continuous_scale='Reds'
    )
    fig_components.update_layout(height=400)
    st.plotly_chart(fig_components, use_container_width=True)
    
    # Component details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Component Details:**")
        for _, row in df_components.iterrows():
            if row['Stress Points'] > 0:
                st.markdown(f"**{row['Component']}:** {row['Stress Points']:.1f}")
                st.caption(row['Description'])
    
    with col2:
        st.markdown("**Adjustment Factors:**")
        st.markdown(f"**Difficulty Multiplier:** {components['difficulty_multiplier']:.2f}")
        st.caption("Meeting complexity based on content and participants")
        
        st.markdown(f"**Circadian Factor:** {components['circadian_factor']:.2f}")
        st.caption("Time-of-day and day-of-week adjustment")
        
        # Key insights
        if components['back_to_back_penalty'] > 20:
            st.warning("🔄 High back-to-back meeting penalty")
        if components['lunch_disruption_penalty'] > 0:
            st.warning("🍽️ Lunch hour meetings detected")
        if components['overload_penalty'] > 0:
            st.error("⚡ Meeting overload detected")
    
    # 7-Day Detailed Breakdown
    with st.expander("📋 7-Day Detailed Breakdown"):
        for item in forecast_data:
            date_str = item['date'].strftime('%A, %B %d')
            score = item['stress_score']
            level = item['stress_level']
            
            if score > 60:
                st.error(f"**{date_str}:** {score}/100 ({level}) - {item['meeting_count']} meetings, {item['meeting_hours']}h")
            elif score > 30:
                st.warning(f"**{date_str}:** {score}/100 ({level}) - {item['meeting_count']} meetings, {item['meeting_hours']}h")
            else:
                st.success(f"**{date_str}:** {score}/100 ({level}) - {item['meeting_count']} meetings, {item['meeting_hours']}h")
    
    # Export functionality
    st.markdown("---")
    if st.button("📤 Export 7-Day Forecast"):
        export_text = "MINDSYNC 7-DAY STRESS FORECAST\n" + "="*40 + "\n\n"
        for item in forecast_data:
            export_text += f"{item['date'].strftime('%A, %B %d')}: {item['stress_score']}/100 ({item['stress_level']})\n"
            export_text += f"  Meetings: {item['meeting_count']}, Hours: {item['meeting_hours']}\n\n"
        
        st.download_button(
            label="⬇️ Download Forecast",
            data=export_text,
            file_name=f"stress_forecast_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    st.markdown("---")
    st.caption("🧠 7-Day stress forecast with per-day analysis")

def suggestions_page():
    """Smart suggestions and schedule optimization page with multi-day support."""
    st.header("💡 Suggestions & Schedule")
    
    if not st.session_state.parsed_events:
        st.warning("⚠️ Please load calendar data first!")
        return
    
    # Import and initialize
    try:
        from src.stress_predictor import MeetingStressCalculator
        from src.suggestion_engine import SuggestionEngine
        
        calculator = MeetingStressCalculator()
        engine = SuggestionEngine()
        
    except ImportError as e:
        st.error(f"❌ Error: {str(e)}")
        return
    
    # Date selection for viewing suggestions
    st.subheader("📅 Select Date for Suggestions")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Date picker for specific day
        selected_date = st.date_input(
            "Choose date:",
            value=datetime.now().date(),
            min_value=datetime.now().date(),
            max_value=datetime.now().date() + timedelta(days=30)
        )
    
    with col2:
        # Quick date buttons
        st.markdown("**Quick select:**")
        col_today, col_tomorrow = st.columns(2)
        with col_today:
            if st.button("📅 Today"):
                selected_date = datetime.now().date()
                st.rerun()
        with col_tomorrow:
            if st.button("📅 Tomorrow"):
                selected_date = datetime.now().date() + timedelta(days=1)
                st.rerun()
    
    # Generate suggestions for selected date using existing methods
    stress_analysis = calculator.calculate_daily_stress(st.session_state.parsed_events, selected_date)
    
    # Filter events for selected date (manual filtering since original engine doesn't support date selection)
    selected_date_events = [event for event in st.session_state.parsed_events if event.start_time.date() == selected_date]
    
    # Generate suggestions using existing method but with filtered events
    if selected_date_events:
        suggestions = engine.generate_suggestions(selected_date_events, stress_analysis)
    else:
        suggestions = {
            'break_suggestions': [],
            'optimization_tips': [f"No meetings scheduled for {selected_date.strftime('%A, %B %d')}. Great for focused work!"],
            'daily_plan': [],
            'summary': f"No meetings scheduled for {selected_date.strftime('%A, %B %d')}."
        }
    
    stress_score = stress_analysis['daily_stress_score']
    
    # Display selected date info
    date_str = selected_date.strftime('%A, %B %d, %Y')
    if selected_date == datetime.now().date():
        st.subheader(f"🎯 Today's Suggestions ({date_str})")
    elif selected_date == datetime.now().date() + timedelta(days=1):
        st.subheader(f"🌅 Tomorrow's Suggestions ({date_str})")
    else:
        st.subheader(f"📋 Suggestions for {date_str}")
    
    # Emergency alerts for high stress
    if stress_score >= 60:
        emergency_suggestions = engine.get_emergency_suggestions(stress_score)
        for suggestion in emergency_suggestions[:3]:  # Top 3 only
            st.error(f"🚨 {suggestion}")
        st.markdown("---")
    
    # Summary metrics for selected date
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Stress Score", f"{stress_score}/100")
    with col2:
        st.metric("⏰ Break Opportunities", len(suggestions['break_suggestions']))
    with col3:
        st.metric("💡 Optimization Tips", len(suggestions['optimization_tips']))
    
    # Top break suggestions for selected date
    st.subheader("⏰ Recommended Breaks")
    break_suggestions = suggestions['break_suggestions'][:3]  # Top 3 only
    
    if break_suggestions:
        for i, break_rec in enumerate(break_suggestions, 1):
            priority_color = "🔴" if break_rec['priority'] >= 4 else "🟡" if break_rec['priority'] >= 3 else "🟢"
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.markdown(f"**{break_rec['time']}**")
            with col2:
                st.markdown(f"{priority_color} {break_rec['activity']} ({break_rec['duration']}min)")
            with col3:
                if st.button(f"Add", key=f"add_{selected_date}_{i}"):
                    st.success("✅ Break noted!")
    else:
        st.info("No break opportunities found for this date.")
    
    # Optimization tips for selected date
    st.subheader("⚡ Optimization Tips")
    for tip in suggestions['optimization_tips'][:3]:  # Top 3 only
        if tip.startswith(("🚨", "⚠️")):
            st.warning(tip)
        elif tip.startswith("🌟"):
            st.success(tip)
        else:
            st.info(tip)
    
    # Multi-day overview section
    st.markdown("---")
    st.subheader("📊 7-Day Suggestions Overview")
    
    with st.spinner("🧠 Generating 7-day suggestions overview..."):
        # Generate multi-day data using existing methods
        multi_day_data = []
        today = datetime.now().date()
        
        for i in range(7):
            target_date = today + timedelta(days=i)
            
            # Calculate stress for this specific date
            day_stress_analysis = calculator.calculate_daily_stress(st.session_state.parsed_events, target_date)
            
            # Filter events for this date
            day_events = [event for event in st.session_state.parsed_events if event.start_time.date() == target_date]
            
            # Generate suggestions for this date
            if day_events:
                day_suggestions = engine.generate_suggestions(day_events, day_stress_analysis)
            else:
                day_suggestions = {
                    'break_suggestions': [],
                    'optimization_tips': [],
                    'daily_plan': [],
                    'summary': f"No meetings scheduled."
                }
            
            multi_day_data.append({
                'date': target_date,
                'day_name': target_date.strftime('%A'),
                'stress_analysis': day_stress_analysis,
                'suggestions': day_suggestions
            })
    
    # Create overview table
    overview_data = []
    for day_data in multi_day_data:
        overview_data.append({
            'Date': day_data['date'].strftime('%m/%d'),
            'Day': day_data['day_name'][:3],
            'Stress Score': day_data['stress_analysis']['daily_stress_score'],
            'Breaks': len(day_data['suggestions']['break_suggestions']),
            'Tips': len(day_data['suggestions']['optimization_tips']),
            'Meetings': day_data['stress_analysis']['meeting_analysis']['total_meetings']
        })
    
    # Display overview table
    import pandas as pd
    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True)
    
    # Expandable sections for each day
    st.subheader("📋 Daily Breakdown")
    
    for day_data in multi_day_data:
        date_obj = day_data['date']
        stress_analysis = day_data['stress_analysis']
        suggestions = day_data['suggestions']
        
        # Determine day label
        if date_obj == datetime.now().date():
            day_label = f"Today - {day_data['day_name']} ({date_obj.strftime('%m/%d')})"
        elif date_obj == datetime.now().date() + timedelta(days=1):
            day_label = f"Tomorrow - {day_data['day_name']} ({date_obj.strftime('%m/%d')})"
        else:
            day_label = f"{day_data['day_name']} ({date_obj.strftime('%m/%d')})"
        
        # Color code based on stress level
        stress_score = stress_analysis['daily_stress_score']
        if stress_score > 60:
            icon = "🔥"
        elif stress_score > 30:
            icon = "⚠️"
        else:
            icon = "✅"
        
        with st.expander(f"{icon} {day_label} - Stress: {stress_score}/100"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Break Suggestions:**")
                if suggestions['break_suggestions']:
                    for break_rec in suggestions['break_suggestions'][:3]:
                        priority_color = "🔴" if break_rec['priority'] >= 4 else "🟡" if break_rec['priority'] >= 3 else "🟢"
                        st.markdown(f"• {break_rec['time']} - {priority_color} {break_rec['activity']} ({break_rec['duration']}min)")
                else:
                    st.markdown("• No break opportunities")
            
            with col2:
                st.markdown("**Optimization Tips:**")
                if suggestions['optimization_tips']:
                    for tip in suggestions['optimization_tips'][:3]:
                        st.markdown(f"• {tip}")
                else:
                    st.markdown("• No specific tips needed")
            
            # Quick stats for this day
            st.markdown(f"**Meeting Stats:** {stress_analysis['meeting_analysis']['total_meetings']} meetings, "
                       f"{stress_analysis['meeting_analysis']['total_hours']} hours")
    
    # Quick actions (still for selected date)
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧘 2-Min Break", use_container_width=True):
            st.success("Take 6 deep breaths: Inhale (4) → Hold (4) → Exhale (6)")
    
    with col2:
        if st.button("💧 Hydrate", use_container_width=True):
            st.info("💧 Drink water & check posture!")
    
    with col3:
        if st.button("📱 Focus Mode", use_container_width=True):
            st.info("📱 Enable Do Not Disturb")
    
    # Stress-specific advice for selected date
    with st.expander("🎯 Stress-Level Advice"):
        if stress_score <= 20:
            st.success("**Low Stress:** Use this energy for creative work!")
        elif stress_score <= 40:
            st.info("**Moderate Stress:** Stay organized, take planned breaks")
        elif stress_score <= 60:
            st.warning("**Elevated Stress:** Prioritize ruthlessly, take breaks")
        else:
            st.error("**High Stress:** Cancel non-essentials, delegate, take recovery time")
    
    # Export functionality
    st.markdown("---")
    if st.button("📤 Export 7-Day Suggestions"):
        export_text = "MINDSYNC 7-DAY SUGGESTIONS OVERVIEW\n" + "="*40 + "\n\n"
        
        for day_data in multi_day_data:
            date_obj = day_data['date']
            stress_analysis = day_data['stress_analysis']
            suggestions = day_data['suggestions']
            
            export_text += f"{day_data['day_name']}, {date_obj.strftime('%B %d')}\n"
            export_text += f"Stress Score: {stress_analysis['daily_stress_score']}/100\n"
            export_text += f"Meetings: {stress_analysis['meeting_analysis']['total_meetings']}\n"
            export_text += f"Break Opportunities: {len(suggestions['break_suggestions'])}\n"
            
            if suggestions['break_suggestions']:
                export_text += "Top Breaks:\n"
                for break_rec in suggestions['break_suggestions'][:3]:
                    export_text += f"  • {break_rec['time']} - {break_rec['activity']} ({break_rec['duration']}min)\n"
            
            if suggestions['optimization_tips']:
                export_text += "Top Tips:\n"
                for tip in suggestions['optimization_tips'][:3]:
                    export_text += f"  • {tip}\n"
            
            export_text += "\n" + "-"*30 + "\n\n"
        
        st.download_button(
            label="⬇️ Download Suggestions",
            data=export_text,
            file_name=f"suggestions_overview_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )


if __name__ == "__main__":
    main()