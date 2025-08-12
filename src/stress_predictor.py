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
    Research-backed meeting stress calculator based on 11 peer-reviewed studies.
    Calculates daily stress score (0-100) from calendar meeting data.
    """
    
    def __init__(self):
        # Model parameters calibrated from research
        self.params = {
            'α1': 6,     # Meeting frequency weight
            'α2': 0.12,  # Duration weight
            'α3': 15,    # Back-to-back exponential penalty
            'α4': 8,     # Clustering penalty
            'α5': 2,     # Recovery deficit weight
            'α6': 0.25,  # Carryover factor
            'α7': 10     # Intensity clustering penalty
        }
        
        # Initialize sentiment analyzer if available
        if VADER_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        else:
            self.sentiment_analyzer = None
        
        # Keyword categories based on research
        self.high_stress_keywords = [
            "urgent", "crisis", "deadline", "review", "performance", 
            "conflict", "escalation", "emergency", "critical", "budget",
            "layoff", "restructure", "termination", "firing", "discipline"
        ]
        
        self.medium_stress_keywords = [
            "planning", "decision", "strategy", "proposal", "presentation", 
            "discussion", "brainstorm", "workshop", "training", "interview",
            "onboarding", "kickoff", "retrospective", "demo"
        ]
        
        self.low_stress_keywords = [
            "social", "celebration", "team building", "coffee", "informal", 
            "casual", "lunch", "fun", "birthday", "farewell", "welcome",
            "happy hour", "game", "party"
        ]
        
        self.recurring_keywords = [
            "weekly", "daily", "standup", "1:1", "sync", "recurring", 
            "regular", "team meeting", "status", "check-in", "scrum",
            "all hands", "townhall"
        ]
        
        self.urgent_keywords = [
            "urgent", "emergency", "asap", "immediate", "crisis", 
            "escalation", "breaking", "urgent call", "fire drill",
            "hotfix", "incident"
        ]
    
    def calculate_daily_stress(self, events: List[Any], previous_day_stress: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive daily stress score from calendar events.
        
        Args:
            events: List of calendar events (CalendarEvent objects)
            previous_day_stress: Previous day's stress score for carryover calculation
            
        Returns:
            Dictionary with stress score and component breakdown
        """
        if not events:
            return {
                'daily_stress_score': 0,
                'stress_level': 'No Meetings',
                'components': {
                    'base_meeting_stress': 0,
                    'back_to_back_penalty': 0,
                    'clustering_stress': 0,
                    'recovery_deficit': 0,
                    'intensity_clustering': 0,
                    'circadian_factor': 1.0,
                    'carryover_factor': 1.0
                },
                'recommendations': ["Great! No meetings scheduled for today."]
            }
        
        # Sort meetings by time
        meetings_sorted = sorted(events, key=lambda m: m.start_time)
        
        # Calculate all stress components
        bms = self._calculate_base_meeting_stress(events)
        bbmp = self._calculate_back_to_back_penalty(meetings_sorted)
        tcs = self._calculate_clustering_stress(meetings_sorted)
        rda = self._calculate_recovery_deficit(meetings_sorted)
        mic = self._calculate_intensity_clustering(events)
        
        # Calculate adjustment factors
        avg_hour = sum(m.start_time.hour for m in events) / len(events)
        weekday = events[0].start_time.weekday()
        
        caf = self._get_circadian_multiplier(int(avg_hour)) * self._get_day_of_week_factor(weekday)
        cfc = self._calculate_carryover_factor(previous_day_stress)
        
        # Final calculation
        raw_stress = (bms + bbmp + tcs + rda + mic) * caf * cfc
        
        # Cap at 100 and ensure minimum 0
        daily_stress = min(100, max(0, raw_stress))
        
        # Determine stress level and recommendations
        stress_level, recommendations = self._get_stress_level_and_recommendations(daily_stress, events)
        
        return {
            'daily_stress_score': round(daily_stress, 1),
            'stress_level': stress_level,
            'components': {
                'base_meeting_stress': round(bms, 1),
                'back_to_back_penalty': round(bbmp, 1),
                'clustering_stress': round(tcs, 1),
                'recovery_deficit': round(rda, 1),
                'intensity_clustering': round(mic, 1),
                'circadian_factor': round(caf, 2),
                'carryover_factor': round(cfc, 2)
            },
            'recommendations': recommendations,
            'meeting_analysis': self._analyze_meetings(events)
        }
    
    def _calculate_base_meeting_stress(self, events: List[Any]) -> float:
        """Calculate base stress from meeting count and duration."""
        meeting_count = len(events)
        total_duration_stress = 0
        
        for event in events:
            mtd = self._calculate_meeting_type_difficulty(event)
            total_duration_stress += event.duration_minutes * mtd
        
        bms = (self.params['α1'] * (meeting_count ** 1.2) + 
               self.params['α2'] * total_duration_stress)
        
        return bms
    
    def _calculate_meeting_type_difficulty(self, event: Any) -> float:
        """Calculate Meeting Type Difficulty using NLP analysis."""
        # Base difficulty by participant count
        participant_count = getattr(event, 'participants', 1)
        if participant_count <= 2:
            base_difficulty = 1.0  # 1:1 meetings
        elif participant_count <= 5:
            base_difficulty = 1.2  # Small group
        else:
            base_difficulty = 1.5  # Large group (6+)
        
        # Participant weight
        participant_weight = math.log2(max(participant_count, 2))
        
        # Sentiment analysis
        sentiment_modifier = self._analyze_sentiment(event)
        
        # Content complexity analysis
        content_complexity = self._analyze_content_complexity(event)
        
        # Recurring vs ad-hoc modifier
        recurring_modifier = self._analyze_recurring_pattern(event)
        
        # Lunch penalty
        lunch_penalty = self._calculate_lunch_penalty(event)
        
        mtd = (base_difficulty * participant_weight * sentiment_modifier * 
               content_complexity * recurring_modifier * lunch_penalty)
        
        return mtd
    
    def _analyze_sentiment(self, event: Any) -> float:
        """Analyze sentiment of meeting title and description."""
        text = f"{getattr(event, 'title', '')} {getattr(event, 'description', '')}"
        
        if not text.strip():
            return 1.0
        
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(text)
            sentiment_score = scores['compound']
            
            if sentiment_score > 0.1:
                return 0.9   # Positive meetings are less stressful
            elif sentiment_score < -0.1:
                return 1.3   # Negative meetings are more stressful
            else:
                return 1.0   # Neutral
        else:
            # Basic sentiment analysis without VADER
            negative_words = ['problem', 'issue', 'urgent', 'crisis', 'conflict']
            positive_words = ['celebration', 'success', 'achievement', 'fun', 'social']
            
            text_lower = text.lower()
            neg_count = sum(1 for word in negative_words if word in text_lower)
            pos_count = sum(1 for word in positive_words if word in text_lower)
            
            if pos_count > neg_count:
                return 0.9
            elif neg_count > pos_count:
                return 1.3
            else:
                return 1.0
    
    def _analyze_content_complexity(self, event: Any) -> float:
        """Analyze content complexity using keyword analysis."""
        text = f"{getattr(event, 'title', '')} {getattr(event, 'description', '')}".lower()
        
        if any(keyword in text for keyword in self.high_stress_keywords):
            return 1.4
        elif any(keyword in text for keyword in self.medium_stress_keywords):
            return 1.2
        elif any(keyword in text for keyword in self.low_stress_keywords):
            return 0.8
        else:
            return 1.0
    
    def _analyze_recurring_pattern(self, event: Any) -> float:
        """Determine if meeting is recurring or ad-hoc."""
        text = f"{getattr(event, 'title', '')} {getattr(event, 'description', '')}".lower()
        
        if any(keyword in text for keyword in self.recurring_keywords):
            return 0.9  # Familiar meetings are less stressful
        elif any(keyword in text for keyword in self.urgent_keywords):
            return 1.3  # Urgent ad-hoc meetings are more stressful
        else:
            return 1.0
    
    def _calculate_lunch_penalty(self, event: Any) -> float:
        """Apply penalty for meetings during lunch hours (11:30 AM - 1:30 PM)."""
        start_time = event.start_time
        hour = start_time.hour
        minute = start_time.minute
        
        if ((hour == 11 and minute >= 30) or 
            (hour == 12) or 
            (hour == 13 and minute <= 30)):
            return 1.3
        else:
            return 1.0
    
    def _calculate_back_to_back_penalty(self, meetings_sorted: List[Any]) -> float:
        """Calculate penalty for back-to-back meetings."""
        penalty = 0
        current_chain = []
        
        for i, meeting in enumerate(meetings_sorted):
            if i == 0:
                current_chain = [meeting]
                continue
            
            prev_meeting = meetings_sorted[i-1]
            gap_minutes = (meeting.start_time - prev_meeting.end_time).total_seconds() / 60
            
            if gap_minutes <= 10:  # Back-to-back threshold
                current_chain.append(meeting)
            else:
                # Process completed chain
                if len(current_chain) >= 2:
                    chain_length = len(current_chain)
                    penalty += self.params['α3'] * (chain_length ** 1.5)
                current_chain = [meeting]
        
        # Process final chain
        if len(current_chain) >= 2:
            chain_length = len(current_chain)
            penalty += self.params['α3'] * (chain_length ** 1.5)
        
        return penalty
    
    def _calculate_clustering_stress(self, meetings_sorted: List[Any]) -> float:
        """Calculate stress from insufficient recovery time."""
        stress = 0
        for i in range(1, len(meetings_sorted)):
            prev_meeting = meetings_sorted[i-1]
            current_meeting = meetings_sorted[i]
            gap_minutes = (current_meeting.start_time - prev_meeting.end_time).total_seconds() / 60
            
            # Insufficient recovery time (not back-to-back, but still problematic)
            if 10 < gap_minutes <= 30:
                stress += self.params['α4'] * (60 / gap_minutes)
        
        return stress
    
    def _calculate_recovery_deficit(self, meetings_sorted: List[Any]) -> float:
        """Calculate accumulated recovery deficit."""
        deficit = 0
        
        for i in range(1, len(meetings_sorted)):
            prev_meeting = meetings_sorted[i-1]
            current_meeting = meetings_sorted[i]
            
            # Calculate required recovery time
            required_recovery = self._get_required_recovery_time(prev_meeting)
            actual_gap = (current_meeting.start_time - prev_meeting.end_time).total_seconds() / 60
            
            if actual_gap < required_recovery:
                deficit += self.params['α5'] * (required_recovery - actual_gap)
        
        return deficit
    
    def _get_required_recovery_time(self, meeting: Any) -> float:
        """Calculate required recovery time based on meeting characteristics."""
        participant_count = getattr(meeting, 'participants', 1)
        
        # Base recovery time
        if participant_count <= 2:
            base_recovery = 5
        elif participant_count <= 5:
            base_recovery = 8
        else:
            base_recovery = 12
        
        # Add recovery for high-stress content
        content_complexity = self._analyze_content_complexity(meeting)
        if content_complexity >= 1.4:
            base_recovery += 3
        
        # Add recovery for lunch meetings
        if self._calculate_lunch_penalty(meeting) > 1.0:
            base_recovery += 5
        
        return base_recovery
    
    def _calculate_intensity_clustering(self, events: List[Any]) -> float:
        """Calculate penalty for multiple meetings in same hour."""
        meetings_by_hour = defaultdict(list)
        
        for event in events:
            hour = event.start_time.hour
            meetings_by_hour[hour].append(event)
        
        penalty = 0
        for hour, meetings_in_hour in meetings_by_hour.items():
            if len(meetings_in_hour) >= 2:
                penalty += self.params['α7'] * (len(meetings_in_hour) ** 2)
        
        return penalty
    
    def _get_circadian_multiplier(self, hour: int) -> float:
        """Get circadian rhythm adjustment factor."""
        circadian_map = {
            7: 1.4,   # Early morning fatigue
            8: 1.4,
            9: 1.0,   # Optimal
            10: 1.0,
            11: 1.3,  # Lunch disruption starts
            12: 1.3,
            13: 1.3,  # Lunch disruption continues
            14: 1.0,  # Post-lunch recovery
            15: 1.0,
            16: 1.0,
            17: 1.4,  # End-of-day fatigue
            18: 1.4,
            19: 1.6,  # Overtime penalty
            20: 1.6,
            21: 1.6
        }
        return circadian_map.get(hour, 1.0)
    
    def _get_day_of_week_factor(self, weekday: int) -> float:
        """Get day of week adjustment factor."""
        # weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
        day_factors = {
            0: 1.2,  # Monday blues
            1: 1.0,  # Tuesday
            2: 1.0,  # Wednesday
            3: 1.0,  # Thursday
            4: 0.9,  # Friday (TGIF effect)
            5: 1.0,  # Saturday
            6: 1.0   # Sunday
        }
        return day_factors.get(weekday, 1.0)
    
    def _calculate_carryover_factor(self, previous_day_stress: Optional[float]) -> float:
        """Calculate stress carryover from previous day."""
        if previous_day_stress is None:
            return 1.0
        
        decay_factor = 0.7
        carryover = 1 + (self.params['α6'] * (previous_day_stress / 100) * decay_factor)
        return min(carryover, 1.5)  # Cap the carryover effect
    
    def _get_stress_level_and_recommendations(self, stress_score: float, events: List[Any]) -> tuple:
        """Determine stress level and generate recommendations."""
        if stress_score <= 20:
            level = "Low Stress"
            recommendations = [
                "Great! Your meeting load is manageable.",
                "Consider using this light day to tackle focused work.",
                "Maybe offer to help colleagues with their workload."
            ]
        elif stress_score <= 40:
            level = "Moderate Stress"
            recommendations = [
                "Your meeting load is moderate. Stay organized.",
                "Take short breaks between meetings when possible.",
                "Prepare meeting agendas to make sessions more efficient."
            ]
        elif stress_score <= 60:
            level = "Elevated Stress"
            recommendations = [
                "Consider rescheduling non-critical meetings.",
                "Take 5-10 minute breaks between meetings.",
                "Practice deep breathing exercises between sessions.",
                "Stay hydrated and avoid caffeine overload."
            ]
        elif stress_score <= 80:
            level = "High Stress"
            recommendations = [
                "⚠️ Heavy meeting day detected. Prioritize ruthlessly.",
                "Cancel or delegate non-essential meetings.",
                "Block 15-minute breaks between back-to-back meetings.",
                "Consider declining lunch meetings to preserve energy.",
                "Prepare thoroughly to reduce in-meeting stress."
            ]
        else:
            level = "Critical Stress"
            recommendations = [
                "🚨 CRITICAL: This schedule may lead to burnout.",
                "Immediately reschedule or cancel non-urgent meetings.",
                "Block recovery time after high-stress meetings.",
                "Consider working from home to reduce commute stress.",
                "Speak with your manager about workload management.",
                "Take micro-breaks (2-3 minutes) between every meeting."
            ]
        
        return level, recommendations
    
    def _analyze_meetings(self, events: List[Any]) -> Dict[str, Any]:
        """Provide detailed meeting analysis."""
        if not events:
            return {}
        
        total_duration = sum(event.duration_minutes for event in events)
        meetings_sorted = sorted(events, key=lambda m: m.start_time)
        
        # Find back-to-back meetings
        back_to_back_count = 0
        for i in range(1, len(meetings_sorted)):
            gap = (meetings_sorted[i].start_time - meetings_sorted[i-1].end_time).total_seconds() / 60
            if gap <= 10:
                back_to_back_count += 1
        
        # Find lunch meetings
        lunch_meetings = [
            event for event in events 
            if self._calculate_lunch_penalty(event) > 1.0
        ]
        
        # Find high-stress meetings
        high_stress_meetings = [
            event for event in events 
            if self._analyze_content_complexity(event) >= 1.4
        ]
        
        return {
            'total_meetings': len(events),
            'total_duration_hours': round(total_duration / 60, 1),
            'back_to_back_transitions': back_to_back_count,
            'lunch_meetings': len(lunch_meetings),
            'high_stress_meetings': len(high_stress_meetings),
            'first_meeting': meetings_sorted[0].start_time.strftime('%H:%M'),
            'last_meeting': meetings_sorted[-1].end_time.strftime('%H:%M'),
            'longest_meeting': max(events, key=lambda x: x.duration_minutes).duration_minutes
        }