from datetime import datetime, timedelta
import math
import re
from collections import defaultdict
from typing import List, Dict, Any, Optional

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("Warning: vaderSentiment not available. Using basic sentiment analysis.")

class MeetingStressCalculator:
    """
    Research-backed meeting stress calculator with improved logic.
    Calculates daily stress score (0-100) from calendar meeting data.
    """
    
    def __init__(self):
        # Model parameters calibrated from research
        self.params = {
            'base_stress_per_hour': 8,      # Base stress per meeting hour
            'meeting_frequency_multiplier': 1.5,  # Stress multiplier per additional meeting
            'back_to_back_penalty': 25,     # Penalty for back-to-back meetings
            'lunch_disruption_penalty': 15, # Penalty for lunch hour meetings
            'long_meeting_threshold': 90,   # Minutes - when meetings become very stressful
            'daily_meeting_limit': 4,       # Reasonable daily meeting limit
            'daily_hour_limit': 4           # Maximum reasonable meeting hours per day
        }
        
        # Lunch break time (1 PM - 2 PM)
        self.lunch_start_hour = 13  # 1 PM
        self.lunch_end_hour = 14    # 2 PM
        
        # Initialize sentiment analyzer
        if VADER_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        else:
            self.sentiment_analyzer = None
        
        # Lunch break keywords to filter out
        self.lunch_keywords = [
            "lunch", "break", "coffee", "snack", "meal", "eat", "food",
            "restaurant", "cafe", "dining", "brunch", "dinner"
        ]
        
        # High stress meeting keywords
        self.high_stress_keywords = [
            "urgent", "crisis", "deadline", "review", "performance", 
            "conflict", "escalation", "emergency", "critical", "budget",
            "layoff", "restructure", "termination", "firing", "discipline"
        ]
        
        # Low stress meeting keywords
        self.low_stress_keywords = [
            "social", "celebration", "team building", "informal", 
            "casual", "fun", "birthday", "farewell", "welcome",
            "happy hour", "game", "party", "brainstorm", "creative"
        ]
    
    def calculate_daily_stress(self, events: List[Any], target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate stress for a specific day from calendar events.
        
        Args:
            events: List of calendar events
            target_date: Specific date to analyze (default: today)
            
        Returns:
            Dictionary with stress score and analysis
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        # Filter events for the target day and remove lunch breaks
        daily_events = self._filter_daily_events(events, target_date)
        actual_meetings = self._filter_out_lunch_breaks(daily_events)
        
        if not actual_meetings:
            return {
                'daily_stress_score': 0,
                'stress_level': 'No Meetings',
                'components': self._get_empty_components(),
                'recommendations': ["Great! No meetings scheduled for today."],
                'meeting_analysis': {'total_meetings': 0, 'total_hours': 0}
            }
        
        # Calculate stress components
        stress_components = self._calculate_stress_components(actual_meetings, target_date)
        
        # Calculate final stress score
        final_score = self._calculate_final_score(stress_components)
        
        # Generate analysis
        stress_level, recommendations = self._get_stress_level_and_recommendations(final_score, actual_meetings)
        meeting_analysis = self._analyze_meetings(actual_meetings, daily_events)
        
        return {
            'daily_stress_score': round(final_score, 1),
            'stress_level': stress_level,
            'components': stress_components,
            'recommendations': recommendations,
            'meeting_analysis': meeting_analysis
        }
    
    def _filter_daily_events(self, events: List[Any], target_date: datetime.date) -> List[Any]:
        """Filter events for a specific day."""
        daily_events = []
        for event in events:
            event_date = event.start_time.date()
            if event_date == target_date:
                daily_events.append(event)
        return sorted(daily_events, key=lambda x: x.start_time)
    
    def _filter_out_lunch_breaks(self, events: List[Any]) -> List[Any]:
        """Remove lunch breaks from meeting list."""
        actual_meetings = []
        
        for event in events:
            # Check if event is likely a lunch break
            is_lunch_break = self._is_lunch_break(event)
            
            if not is_lunch_break:
                actual_meetings.append(event)
        
        return actual_meetings
    
    def _is_lunch_break(self, event: Any) -> bool:
        """Determine if an event is a lunch break."""
        title = getattr(event, 'title', '').lower()
        description = getattr(event, 'description', '').lower()
        
        # Check for lunch keywords
        text = f"{title} {description}"
        if any(keyword in text for keyword in self.lunch_keywords):
            return True
        
        # Check if event is during lunch hours and has no/few participants
        start_hour = event.start_time.hour
        participants = getattr(event, 'participants', 1)
        
        # If during lunch hours (1-2 PM) and <= 2 participants, likely personal lunch
        if (self.lunch_start_hour <= start_hour < self.lunch_end_hour and 
            participants <= 2 and 
            not any(keyword in text for keyword in self.high_stress_keywords)):
            return True
        
        return False
    
    def _calculate_stress_components(self, meetings: List[Any], target_date: datetime.date) -> Dict[str, float]:
        """Calculate all stress components for the day."""
        if not meetings:
            return self._get_empty_components()
        
        # Base meeting load stress
        total_meeting_hours = sum(m.duration_minutes for m in meetings) / 60
        meeting_count = len(meetings)
        
        base_stress = (total_meeting_hours * self.params['base_stress_per_hour'] + 
                      (meeting_count - 1) * self.params['meeting_frequency_multiplier'])
        
        # Meeting difficulty multiplier
        difficulty_multiplier = self._calculate_average_difficulty(meetings)
        base_stress *= difficulty_multiplier
        
        # Back-to-back meeting penalty
        back_to_back_penalty = self._calculate_back_to_back_penalty(meetings)
        
        # Lunch disruption penalty
        lunch_penalty = self._calculate_lunch_disruption_penalty(meetings)
        
        # Long meeting penalty
        long_meeting_penalty = self._calculate_long_meeting_penalty(meetings)
        
        # Overload penalty (too many meetings or too many hours)
        overload_penalty = self._calculate_overload_penalty(meetings)
        
        # Circadian adjustment
        circadian_factor = self._get_circadian_adjustment(meetings, target_date)
        
        return {
            'base_meeting_stress': round(base_stress, 1),
            'back_to_back_penalty': round(back_to_back_penalty, 1),
            'lunch_disruption_penalty': round(lunch_penalty, 1),
            'long_meeting_penalty': round(long_meeting_penalty, 1),
            'overload_penalty': round(overload_penalty, 1),
            'difficulty_multiplier': round(difficulty_multiplier, 2),
            'circadian_factor': round(circadian_factor, 2),
            'total_meeting_hours': round(total_meeting_hours, 1),
            'meeting_count': meeting_count
        }
    
    def _calculate_average_difficulty(self, meetings: List[Any]) -> float:
        """Calculate average meeting difficulty using NLP."""
        if not meetings:
            return 1.0
        
        total_difficulty = 0
        for meeting in meetings:
            difficulty = self._analyze_meeting_difficulty(meeting)
            total_difficulty += difficulty
        
        return total_difficulty / len(meetings)
    
    def _analyze_meeting_difficulty(self, meeting: Any) -> float:
        """Analyze individual meeting difficulty."""
        title = getattr(meeting, 'title', '').lower()
        description = getattr(meeting, 'description', '').lower()
        text = f"{title} {description}"
        
        # Base difficulty from participants
        participants = getattr(meeting, 'participants', 1)
        if participants <= 2:
            base_difficulty = 1.0
        elif participants <= 5:
            base_difficulty = 1.3
        else:
            base_difficulty = 1.6
        
        # Content analysis
        if any(keyword in text for keyword in self.high_stress_keywords):
            content_multiplier = 1.5
        elif any(keyword in text for keyword in self.low_stress_keywords):
            content_multiplier = 0.7
        else:
            content_multiplier = 1.0
        
        # Sentiment analysis
        sentiment_multiplier = self._analyze_sentiment(meeting)
        
        return base_difficulty * content_multiplier * sentiment_multiplier
    
    def _analyze_sentiment(self, meeting: Any) -> float:
        """Analyze meeting sentiment."""
        text = f"{getattr(meeting, 'title', '')} {getattr(meeting, 'description', '')}"
        
        if not text.strip():
            return 1.0
        
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(text)
            sentiment_score = scores['compound']
            
            if sentiment_score > 0.1:
                return 0.8   # Positive meetings less stressful
            elif sentiment_score < -0.1:
                return 1.3   # Negative meetings more stressful
            else:
                return 1.0
        else:
            # Basic sentiment without VADER
            negative_words = ['problem', 'issue', 'urgent', 'crisis', 'conflict']
            positive_words = ['celebration', 'success', 'achievement', 'fun']
            
            text_lower = text.lower()
            if any(word in text_lower for word in positive_words):
                return 0.8
            elif any(word in text_lower for word in negative_words):
                return 1.3
            else:
                return 1.0
    
    def _calculate_back_to_back_penalty(self, meetings: List[Any]) -> float:
        """Calculate penalty for back-to-back meetings."""
        if len(meetings) < 2:
            return 0
        
        penalty = 0
        for i in range(1, len(meetings)):
            gap_minutes = (meetings[i].start_time - meetings[i-1].end_time).total_seconds() / 60
            
            if gap_minutes <= 10:  # Back-to-back (≤10 minutes)
                penalty += self.params['back_to_back_penalty']
            elif gap_minutes <= 30:  # Insufficient break (10-30 minutes)
                penalty += self.params['back_to_back_penalty'] * 0.5
        
        return penalty
    
    def _calculate_lunch_disruption_penalty(self, meetings: List[Any]) -> float:
        """Calculate penalty for meetings during lunch hours."""
        penalty = 0
        
        for meeting in meetings:
            start_hour = meeting.start_time.hour
            end_hour = meeting.end_time.hour
            
            # Check if meeting overlaps with lunch time (1-2 PM)
            if (start_hour < self.lunch_end_hour and end_hour > self.lunch_start_hour):
                penalty += self.params['lunch_disruption_penalty']
        
        return penalty
    
    def _calculate_long_meeting_penalty(self, meetings: List[Any]) -> float:
        """Calculate penalty for very long meetings."""
        penalty = 0
        
        for meeting in meetings:
            if meeting.duration_minutes > self.params['long_meeting_threshold']:
                # Exponential penalty for very long meetings
                excess_time = meeting.duration_minutes - self.params['long_meeting_threshold']
                penalty += (excess_time / 30) * 10  # 10 stress points per extra 30 minutes
        
        return penalty
    
    def _calculate_overload_penalty(self, meetings: List[Any]) -> float:
        """Calculate penalty for too many meetings or too many hours."""
        penalty = 0
        
        meeting_count = len(meetings)
        total_hours = sum(m.duration_minutes for m in meetings) / 60
        
        # Too many meetings penalty
        if meeting_count > self.params['daily_meeting_limit']:
            excess_meetings = meeting_count - self.params['daily_meeting_limit']
            penalty += excess_meetings * 15  # 15 stress points per excess meeting
        
        # Too many hours penalty
        if total_hours > self.params['daily_hour_limit']:
            excess_hours = total_hours - self.params['daily_hour_limit']
            penalty += excess_hours * 20  # 20 stress points per excess hour
        
        return penalty
    
    def _get_circadian_adjustment(self, meetings: List[Any], target_date: datetime.date) -> float:
        """Calculate circadian and day-of-week adjustments."""
        if not meetings:
            return 1.0
        
        # Average meeting time
        avg_hour = sum(m.start_time.hour for m in meetings) / len(meetings)
        
        # Time of day adjustment
        if avg_hour < 8:
            time_factor = 1.3  # Very early
        elif avg_hour < 9:
            time_factor = 1.1  # Early
        elif avg_hour < 17:
            time_factor = 1.0  # Normal hours
        elif avg_hour < 19:
            time_factor = 1.2  # Late
        else:
            time_factor = 1.4  # Very late
        
        # Day of week adjustment
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday
        if weekday == 0:  # Monday
            day_factor = 1.1
        elif weekday == 4:  # Friday
            day_factor = 0.9
        else:
            day_factor = 1.0
        
        return time_factor * day_factor
    
    def _calculate_final_score(self, components: Dict[str, float]) -> float:
        """Calculate final stress score with logical caps."""
        base_score = (components['base_meeting_stress'] + 
                     components['back_to_back_penalty'] + 
                     components['lunch_disruption_penalty'] + 
                     components['long_meeting_penalty'] + 
                     components['overload_penalty'])
        
        # Apply adjustments
        adjusted_score = base_score * components['circadian_factor']
        
        # Logical caps based on meeting load
        meeting_hours = components['total_meeting_hours']
        meeting_count = components['meeting_count']
        
        # Cap score based on actual meeting load
        if meeting_hours <= 2 and meeting_count <= 3:
            max_score = 40  # Light day
        elif meeting_hours <= 4 and meeting_count <= 5:
            max_score = 70  # Moderate day
        else:
            max_score = 100  # Heavy day
        
        final_score = min(adjusted_score, max_score)
        return max(0, final_score)  # Ensure non-negative
    
    def _get_empty_components(self) -> Dict[str, float]:
        """Return empty components structure."""
        return {
            'base_meeting_stress': 0,
            'back_to_back_penalty': 0,
            'lunch_disruption_penalty': 0,
            'long_meeting_penalty': 0,
            'overload_penalty': 0,
            'difficulty_multiplier': 1.0,
            'circadian_factor': 1.0,
            'total_meeting_hours': 0,
            'meeting_count': 0
        }
    
    def _get_stress_level_and_recommendations(self, stress_score: float, meetings: List[Any]) -> tuple:
        """Determine stress level and generate recommendations."""
        if stress_score <= 25:
            level = "Low Stress"
            recommendations = [
                "Great! Your meeting load is very manageable.",
                "Use this time for deep work and creative projects.",
                "Consider helping colleagues with their workload."
            ]
        elif stress_score <= 50:
            level = "Moderate Stress"
            recommendations = [
                "Your meeting schedule is reasonable.",
                "Take short breaks between meetings.",
                "Stay organized with meeting agendas."
            ]
        elif stress_score <= 75:
            level = "High Stress"
            recommendations = [
                "⚠️ Heavy meeting day. Prioritize effectively.",
                "Take 10-15 minute breaks between meetings.",
                "Consider rescheduling non-critical meetings.",
                "Prepare thoroughly to reduce in-meeting stress."
            ]
        else:
            level = "Critical Stress"
            recommendations = [
                "🚨 OVERLOAD: Immediate action required.",
                "Cancel or reschedule non-urgent meetings.",
                "Block recovery time after intense meetings.",
                "Speak with your manager about workload.",
                "Consider working from home to reduce stress."
            ]
        
        return level, recommendations
    
    def _analyze_meetings(self, actual_meetings: List[Any], all_events: List[Any]) -> Dict[str, Any]:
        """Analyze meeting patterns."""
        if not actual_meetings:
            return {'total_meetings': 0, 'total_hours': 0}
        
        total_duration = sum(m.duration_minutes for m in actual_meetings)
        lunch_breaks_filtered = len(all_events) - len(actual_meetings)
        
        # Back-to-back count
        back_to_back = 0
        for i in range(1, len(actual_meetings)):
            gap = (actual_meetings[i].start_time - actual_meetings[i-1].end_time).total_seconds() / 60
            if gap <= 10:
                back_to_back += 1
        
        # Lunch hour meetings
        lunch_hour_meetings = 0
        for meeting in actual_meetings:
            start_hour = meeting.start_time.hour
            if self.lunch_start_hour <= start_hour < self.lunch_end_hour:
                lunch_hour_meetings += 1
        
        return {
            'total_meetings': len(actual_meetings),
            'total_hours': round(total_duration / 60, 1),
            'lunch_breaks_filtered': lunch_breaks_filtered,
            'back_to_back_transitions': back_to_back,
            'lunch_hour_meetings': lunch_hour_meetings,
            'first_meeting': actual_meetings[0].start_time.strftime('%H:%M') if actual_meetings else '',
            'last_meeting': actual_meetings[-1].end_time.strftime('%H:%M') if actual_meetings else '',
            'longest_meeting': max(actual_meetings, key=lambda x: x.duration_minutes).duration_minutes if actual_meetings else 0
        }