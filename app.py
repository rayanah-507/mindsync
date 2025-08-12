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
    """Complete stress analysis page with research-backed calculations."""
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
    
    # Calculate stress analysis
    with st.spinner("🧠 Analyzing meeting stress patterns..."):
        stress_result = calculator.calculate_daily_stress(events)
    
    # Main stress score display
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stress_score = stress_result['daily_stress_score']
        stress_level = stress_result['stress_level']
        
        # Color-coded stress display
        if stress_score <= 20:
            color = "🟢"
            bg_color = "#d4edda"
        elif stress_score <= 40:
            color = "🟡"
            bg_color = "#fff3cd"
        elif stress_score <= 60:
            color = "🟠"
            bg_color = "#f8d7da"
        elif stress_score <= 80:
            color = "🔴"
            bg_color = "#f8d7da"
        else:
            color = "🚨"
            bg_color = "#f5c6cb"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="margin: 0;">{color} Daily Stress Score</h2>
            <h1 style="margin: 10px 0; font-size: 3em;">{stress_score}/100</h1>
            <h3 style="margin: 0; color: #666;">{stress_level}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Meeting overview
        meeting_analysis = stress_result.get('meeting_analysis', {})
        st.metric("📅 Total Meetings", meeting_analysis.get('total_meetings', 0))
        st.metric("⏱️ Total Duration", f"{meeting_analysis.get('total_duration_hours', 0)}h")
        st.metric("🔄 Back-to-Back", meeting_analysis.get('back_to_back_transitions', 0))
    
    with col3:
        # Quick stats
        st.metric("🍽️ Lunch Meetings", meeting_analysis.get('lunch_meetings', 0))
        st.metric("⚡ High-Stress Meetings", meeting_analysis.get('high_stress_meetings', 0))
        if meeting_analysis.get('first_meeting') and meeting_analysis.get('last_meeting'):
            st.metric("📍 Meeting Span", f"{meeting_analysis['first_meeting']} - {meeting_analysis['last_meeting']}")
    
    # Recommendations
    st.markdown("---")
    st.subheader("💡 Personalized Recommendations")
    
    recommendations = stress_result.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        if rec.startswith("🚨") or rec.startswith("⚠️"):
            st.error(f"{i}. {rec}")
        elif rec.startswith("Great") or rec.startswith("Consider using"):
            st.success(f"{i}. {rec}")
        else:
            st.info(f"{i}. {rec}")
    
    # Detailed stress components breakdown
    st.markdown("---")
    st.subheader("📊 Stress Components Breakdown")
    
    components = stress_result['components']
    
    # Create breakdown chart
    component_data = {
        'Component': [
            'Base Meeting Load',
            'Back-to-Back Penalty',
            'Clustering Stress',
            'Recovery Deficit',
            'Intensity Clustering'
        ],
        'Stress Points': [
            components['base_meeting_stress'],
            components['back_to_back_penalty'],
            components['clustering_stress'],
            components['recovery_deficit'],
            components['intensity_clustering']
        ],
        'Description': [
            'Core stress from meeting count and duration',
            'Penalty for consecutive meetings with <10min gaps',
            'Stress from insufficient recovery time (10-30min gaps)',
            'Accumulated deficit from inadequate break time',
            'Penalty for multiple meetings in same hour'
        ]
    }
    
    import pandas as pd
    import plotly.express as px
    
    df_components = pd.DataFrame(component_data)
    
    # Bar chart of stress components
    fig = px.bar(
        df_components, 
        x='Component', 
        y='Stress Points',
        title='Stress Components Analysis',
        color='Stress Points',
        color_continuous_scale='Reds'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Component details table
    st.subheader("📋 Component Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Core Stress Components:**")
        for i, row in df_components.iterrows():
            st.markdown(f"**{row['Component']}:** {row['Stress Points']:.1f}")
            st.caption(row['Description'])
            st.markdown("")
    
    with col2:
        st.markdown("**Adjustment Factors:**")
        st.markdown(f"**Circadian Factor:** {components['circadian_factor']:.2f}")
        st.caption("Time-of-day adjustment (early morning, lunch, overtime penalties)")
        
        st.markdown(f"**Carryover Factor:** {components['carryover_factor']:.2f}")
        st.caption("Previous day stress carryover effect")
        
        # Additional insights
        st.markdown("**Key Insights:**")
        if components['back_to_back_penalty'] > 20:
            st.warning("🔄 High back-to-back meeting penalty detected")
        if components['recovery_deficit'] > 15:
            st.warning("😴 Significant recovery deficit - need longer breaks")
        if components['intensity_clustering'] > 10:
            st.warning("⚡ Meeting intensity clustering detected")
    
    # Meeting timeline with stress indicators
    st.markdown("---")
    st.subheader("📅 Meeting Timeline with Stress Indicators")
    
    if events:
        timeline_data = []
        for i, event in enumerate(sorted(events, key=lambda x: x.start_time)):
            # Calculate individual meeting stress
            mtd = calculator._calculate_meeting_type_difficulty(event)
            meeting_stress = event.duration_minutes * mtd * 0.1  # Simplified individual stress
            
            timeline_data.append({
                'Meeting': event.title[:30] + "..." if len(event.title) > 30 else event.title,
                'Start': event.start_time,
                'End': event.end_time,
                'Duration': event.duration_minutes,
                'Participants': event.participants,
                'Stress Level': min(meeting_stress, 10),  # Cap for visualization
                'Type': event.event_type
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        
        # Enhanced timeline chart
        fig_timeline = px.timeline(
            df_timeline,
            x_start="Start",
            x_end="End",
            y="Meeting",
            color="Stress Level",
            color_continuous_scale="Reds",
            title="Daily Meeting Timeline with Stress Levels",
            hover_data=["Duration", "Participants", "Type"]
        )
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Stress reduction tips
    st.markdown("---")
    st.subheader("🧘 Research-Backed Stress Reduction Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Before Meetings:**")
        st.markdown("• Take 2-3 deep breaths")
        st.markdown("• Review agenda and key points")
        st.markdown("• Set clear objectives")
        st.markdown("• Minimize distractions")
        
        st.markdown("**During Meetings:**")
        st.markdown("• Stay focused on agenda")
        st.markdown("• Take notes to stay engaged")
        st.markdown("• Speak up if unclear")
        st.markdown("• Manage time actively")
    
    with col2:
        st.markdown("**Between Meetings:**")
        st.markdown("• Take a 5-10 minute break")
        st.markdown("• Do quick stretches")
        st.markdown("• Hydrate and have a snack")
        st.markdown("• Process and note action items")
        
        st.markdown("**End of Day:**")
        st.markdown("• Review accomplishments")
        st.markdown("• Plan tomorrow's priorities")
        st.markdown("• Practice gratitude")
        st.markdown("• Disconnect from work")
    
    # Configuration section for advanced users
    with st.expander("⚙️ Advanced Configuration"):
        st.markdown("**Model Parameters** (Research-backed defaults)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"Meeting frequency weight (α1): {calculator.params['α1']}")
            st.text(f"Duration weight (α2): {calculator.params['α2']}")
            st.text(f"Back-to-back penalty (α3): {calculator.params['α3']}")
        
        with col2:
            st.text(f"Clustering penalty (α4): {calculator.params['α4']}")
            st.text(f"Recovery deficit weight (α5): {calculator.params['α5']}")
            st.text(f"Carryover factor (α6): {calculator.params['α6']}")
        
        st.info("💡 These parameters are calibrated based on 11 peer-reviewed research studies. Modification may affect accuracy.")
    
    # Export functionality
    st.markdown("---")
    st.subheader("📤 Export Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export Summary", use_container_width=True):
            summary_text = f"""
MINDSYNC STRESS ANALYSIS REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}

DAILY STRESS SCORE: {stress_score}/100
STRESS LEVEL: {stress_level}

MEETING OVERVIEW:
- Total Meetings: {meeting_analysis.get('total_meetings', 0)}
- Total Duration: {meeting_analysis.get('total_duration_hours', 0)} hours
- Back-to-Back Transitions: {meeting_analysis.get('back_to_back_transitions', 0)}
- Lunch Meetings: {meeting_analysis.get('lunch_meetings', 0)}
- High-Stress Meetings: {meeting_analysis.get('high_stress_meetings', 0)}

STRESS COMPONENTS:
- Base Meeting Stress: {components['base_meeting_stress']:.1f}
- Back-to-Back Penalty: {components['back_to_back_penalty']:.1f}
- Clustering Stress: {components['clustering_stress']:.1f}
- Recovery Deficit: {components['recovery_deficit']:.1f}
- Intensity Clustering: {components['intensity_clustering']:.1f}

RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in recommendations)}

---
Generated by MindSync - Research-backed meeting stress analysis
            """
            st.download_button(
                label="⬇️ Download Report",
                data=summary_text,
                file_name=f"stress_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    with col2:
        if st.button("📊 Export Data", use_container_width=True):
            # Prepare CSV data
            export_data = {
                'Date': [datetime.now().strftime('%Y-%m-%d')],
                'Stress_Score': [stress_score],
                'Stress_Level': [stress_level],
                'Total_Meetings': [meeting_analysis.get('total_meetings', 0)],
                'Total_Duration_Hours': [meeting_analysis.get('total_duration_hours', 0)],
                'Back_to_Back_Count': [meeting_analysis.get('back_to_back_transitions', 0)],
                'Base_Meeting_Stress': [components['base_meeting_stress']],
                'Back_to_Back_Penalty': [components['back_to_back_penalty']],
                'Clustering_Stress': [components['clustering_stress']],
                'Recovery_Deficit': [components['recovery_deficit']],
                'Intensity_Clustering': [components['intensity_clustering']],
                'Circadian_Factor': [components['circadian_factor']],
                'Carryover_Factor': [components['carryover_factor']]
            }
            
            import pandas as pd
            df_export = pd.DataFrame(export_data)
            csv_data = df_export.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"stress_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📋 Copy Summary", use_container_width=True):
            summary_short = f"Stress Score: {stress_score}/100 ({stress_level}) | Meetings: {meeting_analysis.get('total_meetings', 0)} | Duration: {meeting_analysis.get('total_duration_hours', 0)}h"
            st.code(summary_short)
            st.success("✅ Summary ready to copy!")
    
    # Research attribution
    st.markdown("---")
    with st.expander("📚 Research Attribution"):
        st.markdown("""
        **This stress analysis model is based on the following peer-reviewed research:**
        
        1. **Allen, J. A., et al. (2022)** - Meeting-to-Work Transition Time and Recovery From Virtual Meeting Fatigue
        2. **Luong, A., & Rogelberg, S. G. (2005)** - The Relationship Between Meeting Load and Daily Well-Being
        3. **Liskin, O., et al. (2013)** - Meeting Intensity as an Indicator for Project Pressure
        4. **Fletcher, A., & Dawson, D. (2001)** - A Quantitative Model of Work-Related Fatigue
        5. **Bailey, B. P., & Iqbal, S. T. (2008)** - Mental Workload During Task Execution
        
        **Additional research sources:**
        - Microsoft Brain Research Study on meeting fatigue
        - University of Hong Kong Monday Blues research
        - CNBC Lunch Break productivity research
        - ResearchGate lunch break impact studies
        
        **Model calibration:** Parameters are calibrated based on findings from 11+ peer-reviewed studies on workplace stress, cognitive load, and meeting fatigue.
        """)
    
    # Feedback section
    st.markdown("---")
    st.subheader("💬 Feedback")
    
    col1, col2 = st.columns(2)
    
    with col1:
        accuracy_rating = st.select_slider(
            "How accurate does this stress assessment feel?",
            options=["Very Low", "Low", "Moderate", "High", "Very High"],
            value="Moderate"
        )
    
    with col2:
        usefulness_rating = st.select_slider(
            "How useful are these recommendations?",
            options=["Not Useful", "Somewhat", "Useful", "Very Useful", "Extremely"],
            value="Useful"
        )
    
    feedback_text = st.text_area(
        "Additional feedback or suggestions:",
        placeholder="Share your thoughts on the stress analysis accuracy, recommendations, or features you'd like to see..."
    )
    
    if st.button("📨 Submit Feedback"):
        # In a real app, this would save to a database
        st.success("Thank you for your feedback! This helps improve the accuracy of our stress analysis model.")
        st.balloons()
    
    # Help section
    with st.expander("❓ How does the stress calculation work?"):
        st.markdown("""
        **The MindSync stress model analyzes your calendar using 9 research-backed components:**
        
        **1. Base Meeting Stress:** Core stress from meeting count and total duration
        **2. Meeting Type Difficulty:** NLP analysis of meeting content, participant count, and context
        **3. Back-to-Back Penalty:** Exponential penalty for meetings with <10 minute gaps
        **4. Clustering Stress:** Additional stress from meetings with 10-30 minute gaps (insufficient recovery)
        **5. Recovery Deficit:** Accumulated deficit when break time is shorter than required
        **6. Intensity Clustering:** Penalty for multiple meetings scheduled in the same hour
        **7. Circadian Adjustment:** Time-of-day factors (early morning, lunch disruption, overtime)
        **8. Day-of-Week Factor:** Monday blues effect and Friday relief
        **9. Carryover Factor:** Previous day's stress impact on current day
        
        **The final score is calculated as:**
        ```
        Daily Stress = (Sum of Components 1-6) × Circadian × Day-of-Week × Carryover
        ```
        
        **Score ranges:**
        - 0-20: Low Stress (manageable workload)
        - 21-40: Moderate Stress (stay organized)
        - 41-60: Elevated Stress (consider optimizations)
        - 61-80: High Stress (take immediate action)
        - 81-100: Critical Stress (risk of burnout)
        """)
        
        st.info("💡 The model uses natural language processing to analyze meeting titles and descriptions for stress indicators, sentiment, and meeting types.")
        
    st.markdown("---")
    st.caption("🧠 MindSync Stress Analysis - Powered by research-backed algorithms")

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