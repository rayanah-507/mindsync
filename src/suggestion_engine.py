from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import random

class SuggestionEngine:
    """
    Intelligent wellbeing suggestion engine that generates personalized 
    recommendations based on calendar analysis and stress levels.
    """
    
    def __init__(self):
        self.activities = {
            'mindfulness': {
                2: ["Take 3 deep breaths", "Quick gratitude moment"],
                5: ["5-minute meditation", "Mindful breathing", "Body scan"],
                10: ["Guided meditation", "Mindfulness practice", "Stress visualization"],
                15: ["Extended meditation", "Progressive relaxation", "Mindful walking"]
            },
            'movement': {
                3: ["Neck rolls", "Shoulder shrugs", "Ankle circles"],
                5: ["Desk stretches", "Walk to water cooler", "Quick posture reset"],
                10: ["Walk around building", "Stair climbing", "Full body stretch"],
                15: ["Outdoor walk", "Yoga poses", "Exercise routine"]
            },
            'recovery': {
                3: ["Hydrate", "Eye rest (20-20-20)", "Deep breath"],
                5: ["Healthy snack", "Posture check", "Workspace tidy"],
                10: ["Complete break", "Fresh air", "Mental reset"],
                15: ["Extended recovery", "Relaxation time", "Rest break"]
            },
            'mental': {
                5: ["Review priorities", "Quick journaling", "Email triage"],
                10: ["Task planning", "Note organization", "Goal check"],
                15: ["Weekly review", "Strategic thinking", "Project planning"]
            }
        }
    
    def generate_suggestions(self, events: List[Any], stress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive wellbeing suggestions - FIXED to work with any date."""
        if not events:
            return {
                'break_suggestions': [],
                'optimization_tips': ["Great! No meetings scheduled. Focus on deep work."],
                'daily_plan': [],
                'summary': "No meetings scheduled."
            }
        
        # Sort events by time
        events_sorted = sorted(events, key=lambda x: x.start_time)
        
        # Find break opportunities - FIXED LOGIC
        break_suggestions = self._find_break_opportunities(events_sorted, stress_analysis)
        
        # Generate optimization tips
        optimization_tips = self._generate_optimization_tips(stress_analysis, events)
        
        # Create daily wellbeing plan
        daily_plan = self._create_daily_plan(events_sorted, stress_analysis)
        
        return {
            'break_suggestions': break_suggestions,
            'optimization_tips': optimization_tips,
            'daily_plan': daily_plan,
            'summary': self._create_summary(break_suggestions, optimization_tips)
        }
    
    def _find_break_opportunities(self, events_sorted: List[Any], stress_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find optimal break insertion points - COMPLETELY REWRITTEN."""
        suggestions = []
        
        if not events_sorted:
            return suggestions
        
        # Get the date we're working with
        target_date = events_sorted[0].start_time.date()
        
        # CASE 1: Single meeting - suggest breaks before and after
        if len(events_sorted) == 1:
            meeting = events_sorted[0]
            
            # Break before meeting (if meeting is after 9 AM)
            if meeting.start_time.hour >= 10:
                suggestions.append({
                    'time': (meeting.start_time - timedelta(minutes=30)).strftime('%H:%M'),
                    'duration': 10,
                    'priority': 3,
                    'type': 'preparation',
                    'activity': 'Meeting preparation and mindfulness',
                    'reason': 'Prepare mentally for upcoming meeting'
                })
            
            # Break after meeting (if meeting ends before 6 PM)
            if meeting.end_time.hour < 18:
                suggestions.append({
                    'time': meeting.end_time.strftime('%H:%M'),
                    'duration': 15,
                    'priority': 4,
                    'type': 'recovery',
                    'activity': 'Post-meeting decompression walk',
                    'reason': 'Recovery time after meeting'
                })
        
        # CASE 2: Multiple meetings - find gaps between them AND before/after
        else:
            # Break before first meeting (if it starts after 9 AM)
            first_meeting = events_sorted[0]
            if first_meeting.start_time.hour >= 10:
                suggestions.append({
                    'time': (first_meeting.start_time - timedelta(minutes=15)).strftime('%H:%M'),
                    'duration': 10,
                    'priority': 3,
                    'type': 'preparation',
                    'activity': 'Morning preparation and focus setting',
                    'reason': 'Prepare for the day ahead'
                })
            
            # Breaks between consecutive meetings
            for i in range(len(events_sorted) - 1):
                current_meeting = events_sorted[i]
                next_meeting = events_sorted[i + 1]
                
                # Calculate gap
                gap_minutes = (next_meeting.start_time - current_meeting.end_time).total_seconds() / 60
                
                # RELAXED CONDITIONS - any gap >= 2 minutes can have a break
                if gap_minutes >= 2:
                    # Determine break duration and priority
                    if gap_minutes >= 15:
                        duration = 10
                        priority = 4
                        break_type = 'movement'
                        activity = 'Walk and stretch'
                    elif gap_minutes >= 10:
                        duration = 5
                        priority = 3
                        break_type = 'recovery'
                        activity = 'Quick hydration break'
                    elif gap_minutes >= 5:
                        duration = 3
                        priority = 3
                        break_type = 'mindfulness'
                        activity = 'Deep breathing'
                    else:  # 2-5 minutes
                        duration = 2
                        priority = 2
                        break_type = 'mindfulness'
                        activity = 'Quick mental reset'
                    
                    # Get actual activity
                    activity = self._get_safe_activity(break_type, duration)
                    
                    suggestions.append({
                        'time': current_meeting.end_time.strftime('%H:%M'),
                        'duration': duration,
                        'priority': priority,
                        'type': break_type,
                        'activity': activity,
                        'reason': self._get_break_reason(current_meeting, next_meeting, gap_minutes)
                    })
            
            # Break after last meeting (if it ends before 6 PM)
            last_meeting = events_sorted[-1]
            if last_meeting.end_time.hour < 18:
                suggestions.append({
                    'time': last_meeting.end_time.strftime('%H:%M'),
                    'duration': 15,
                    'priority': 4,
                    'type': 'recovery',
                    'activity': 'End-of-meetings decompression',
                    'reason': 'Transition back to focused work'
                })
        
        # CASE 3: Heavy meeting days - add extra recovery breaks
        if len(events_sorted) >= 4:
            # Find longest gap for an extended break
            longest_gap = 0
            longest_gap_time = None
            
            for i in range(len(events_sorted) - 1):
                gap = (events_sorted[i + 1].start_time - events_sorted[i].end_time).total_seconds() / 60
                if gap > longest_gap:
                    longest_gap = gap
                    longest_gap_time = events_sorted[i].end_time
            
            if longest_gap >= 30 and longest_gap_time:
                suggestions.append({
                    'time': longest_gap_time.strftime('%H:%M'),
                    'duration': 20,
                    'priority': 5,
                    'type': 'recovery',
                    'activity': 'Extended recovery break - walk outside',
                    'reason': 'Heavy meeting day - extended recovery needed'
                })
        
        # Sort by priority (highest first)
        return sorted(suggestions, key=lambda x: x['priority'], reverse=True)
    
    def _recommend_break_activity(self, current_meeting: Any, next_meeting: Any, 
                                gap_minutes: float, stress_analysis: Dict[str, Any]) -> Tuple[int, str, str]:
        """Recommend specific break activity based on context."""
        
        # Determine break urgency (priority 1-5)
        priority = 1
        
        # High stress meeting = higher priority break
        title_lower = getattr(current_meeting, 'title', '').lower()
        if any(keyword in title_lower for keyword in 
               ['urgent', 'crisis', 'review', 'performance']):
            priority += 2
        
        # Many participants = mental fatigue
        participants = getattr(current_meeting, 'participants', 1)
        if participants > 5:
            priority += 1
        
        # Long meeting = physical fatigue
        if current_meeting.duration_minutes > 60:
            priority += 1
        
        # Back-to-back detection
        if gap_minutes <= 10:
            priority += 2
        
        # Choose activity type and get safe duration
        available_duration = max(3, min(15, int(gap_minutes - 2)))
        
        if gap_minutes <= 5:
            break_type = 'mindfulness'
            safe_duration = self._get_safe_duration('mindfulness', available_duration)
        elif current_meeting.duration_minutes > 90:
            break_type = 'movement'
            safe_duration = self._get_safe_duration('movement', available_duration)
        elif gap_minutes >= 10:
            break_type = random.choice(['movement', 'recovery'])
            safe_duration = self._get_safe_duration(break_type, available_duration)
        else:
            break_type = 'recovery'
            safe_duration = self._get_safe_duration('recovery', available_duration)
        
        # Get activity safely
        activity = self._get_safe_activity(break_type, safe_duration)
        
        return min(priority, 5), break_type, activity
    
    def _get_safe_duration(self, break_type: str, desired_duration: int) -> int:
        """Get the closest available duration for an activity type."""
        available_durations = sorted(self.activities[break_type].keys())
        
        # Find the closest duration that's <= desired_duration
        suitable_duration = None
        for duration in available_durations:
            if duration <= desired_duration:
                suitable_duration = duration
            else:
                break
        
        # If no suitable duration found, use the smallest one
        if suitable_duration is None:
            suitable_duration = available_durations[0]
        
        return suitable_duration
    
    def _get_safe_activity(self, break_type: str, duration: int) -> str:
        """Safely get an activity for the given type and duration."""
        try:
            activities_list = self.activities[break_type][duration]
            return random.choice(activities_list)
        except KeyError:
            # Fallback to any available activity for this type
            all_activities = []
            for dur_activities in self.activities[break_type].values():
                all_activities.extend(dur_activities)
            
            if all_activities:
                return random.choice(all_activities)
            else:
                return f"{break_type.title()} break"
    
    def _get_break_reason(self, current_meeting: Any, next_meeting: Any, gap_minutes: float) -> str:
        """Generate explanation for break suggestion."""
        if gap_minutes <= 5:
            return "Short gap - quick mental reset"
        elif gap_minutes <= 10:
            return "Back-to-back meetings - mental reset needed"
        elif current_meeting.duration_minutes > 90:
            return "Long meeting completed - physical movement recommended"
        elif getattr(current_meeting, 'participants', 1) > 8:
            return "Large group meeting - recovery time beneficial"
        elif any(keyword in getattr(current_meeting, 'title', '').lower() 
                for keyword in ['review', 'performance']):
            return "High-stress meeting - stress relief recommended"
        else:
            return "Opportunity for wellbeing break"
    
    def _generate_optimization_tips(self, stress_analysis: Dict[str, Any], events: List[Any]) -> List[str]:
        """Generate schedule optimization recommendations."""
        tips = []
        
        # Use stress analysis (works with both single day and multi-day)
        if isinstance(stress_analysis, dict) and 'daily_stress_score' in stress_analysis:
            # Single day analysis
            components = stress_analysis.get('components', {})
            stress_score = stress_analysis.get('daily_stress_score', 0)
        else:
            # Fallback for unexpected format
            stress_score = 0
            components = {}
        
        # Back-to-back meeting tips
        if components.get('back_to_back_penalty', 0) > 20:
            tips.append("🔄 Consider adding 15-minute buffers between consecutive meetings")
        
        # Lunch disruption tips
        if components.get('lunch_disruption_penalty', 0) > 0:
            tips.append("🍽️ Protect your lunch hour - avoid scheduling meetings 1-2 PM")
        
        # Overload tips
        if components.get('overload_penalty', 0) > 0:
            tips.append("⚡ Meeting overload detected - consider rescheduling non-critical meetings")
        
        # Long meeting tips
        if components.get('long_meeting_penalty', 0) > 0:
            tips.append("⏰ Break long meetings into shorter sessions with breaks")
        
        # High stress day tips
        if stress_score > 60:
            tips.extend([
                "📋 Prepare meeting agendas in advance to reduce stress",
                "💧 Set hydration reminders throughout the day"
            ])
        
        # General wellness tips
        if stress_score > 40:
            tips.append("🧘 Consider starting the day with 5 minutes of mindfulness")
        
        # If low stress
        if stress_score <= 25:
            tips.append("🌟 Great schedule! Use this energy for creative or strategic work")
        
        # Meeting count based tips
        meeting_count = len(events)
        if meeting_count >= 5:
            tips.append("📱 Use 'Do Not Disturb' between meetings to maintain focus")
        elif meeting_count == 1:
            tips.append("🎯 Single meeting day - perfect for deep work blocks")
        elif meeting_count == 0:
            tips.append("🌟 No meetings today. Great for focused work!")
        
        return tips[:5]  # Limit to top 5 tips
    
    def _create_daily_plan(self, events_sorted: List[Any], stress_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create structured daily wellbeing plan."""
        plan = []
        
        if not events_sorted:
            return [{'time': '09:00', 'activity': 'Start your productive day!', 'type': 'focus'}]
        
        # Morning preparation
        first_meeting = events_sorted[0]
        if first_meeting.start_time.hour >= 9:
            plan.append({
                'time': '08:30',
                'activity': 'Morning preparation - review agenda, set intentions',
                'type': 'preparation'
            })
        
        # Add break suggestions to daily plan
        break_suggestions = self._find_break_opportunities(events_sorted, stress_analysis)
        for suggestion in break_suggestions[:3]:  # Top 3 breaks
            plan.append({
                'time': suggestion['time'],
                'activity': f"{suggestion['activity']} ({suggestion['duration']} min)",
                'type': 'break'
            })
        
        # End of day
        last_meeting = events_sorted[-1]
        end_time = (last_meeting.end_time + timedelta(minutes=30)).strftime('%H:%M')
        plan.append({
            'time': end_time,
            'activity': 'Day wrap-up - review accomplishments, plan tomorrow',
            'type': 'closure'
        })
        
        # Sort by time
        return sorted(plan, key=lambda x: x['time'])
    
    def _create_summary(self, break_suggestions: List[Dict], optimization_tips: List[str]) -> str:
        """Create summary of suggestions."""
        total_breaks = len(break_suggestions)
        high_priority_breaks = len([b for b in break_suggestions if b['priority'] >= 4])
        
        if total_breaks == 0:
            return "No break opportunities found in schedule."
        
        summary = f"Found {total_breaks} break opportunities"
        if high_priority_breaks > 0:
            summary += f" ({high_priority_breaks} high priority)"
        
        return summary + f". {len(optimization_tips)} optimization tips available."
    
    def get_emergency_suggestions(self, stress_score: float) -> List[str]:
        """Get emergency stress relief suggestions for critical stress levels."""
        if stress_score >= 75:
            return [
                "🚨 IMMEDIATE: Take 10 deep breaths right now",
                "🚨 Cancel or reschedule non-critical meetings",
                "🚨 Block 15-minute recovery breaks in your calendar"
            ]
        elif stress_score >= 50:
            return [
                "⚠️ Take a 5-minute break before your next meeting",
                "⚠️ Prepare agendas to make meetings more efficient",
                "⚠️ Consider declining optional meetings today"
            ]
        else:
            return []