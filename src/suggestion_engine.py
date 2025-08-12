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
                10: ["Guided meditation", "Mindfulness practice", "Stress visualization"]
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
                10: ["Complete break", "Fresh air", "Mental reset"]
            },
            'mental': {
                5: ["Review priorities", "Quick journaling", "Email triage"],
                10: ["Task planning", "Note organization", "Goal check"],
                15: ["Weekly review", "Strategic thinking", "Project planning"]
            }
        }
    
    def generate_suggestions(self, events: List[Any], stress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive wellbeing suggestions."""
        if not events:
            return {
                'break_suggestions': [],
                'optimization_tips': ["Great! No meetings today. Focus on deep work."],
                'daily_plan': []
            }
        
        # Sort events by time
        events_sorted = sorted(events, key=lambda x: x.start_time)
        
        # Find break opportunities
        break_suggestions = self._find_break_opportunities(events_sorted, stress_analysis)
        
        # Generate optimization tips
        optimization_tips = self._generate_optimization_tips(stress_analysis)
        
        # Create daily wellbeing plan
        daily_plan = self._create_daily_plan(events_sorted, stress_analysis)
        
        return {
            'break_suggestions': break_suggestions,
            'optimization_tips': optimization_tips,
            'daily_plan': daily_plan,
            'summary': self._create_summary(break_suggestions, optimization_tips)
        }
    
    def _find_break_opportunities(self, events_sorted: List[Any], stress_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find optimal break insertion points."""
        suggestions = []
        
        for i in range(len(events_sorted) - 1):
            current_meeting = events_sorted[i]
            next_meeting = events_sorted[i + 1]
            
            # Calculate gap
            gap_minutes = (next_meeting.start_time - current_meeting.end_time).total_seconds() / 60
            
            if 5 <= gap_minutes <= 60:  # Usable break time
                # Determine break priority and type
                priority, break_type, activity = self._recommend_break_activity(
                    current_meeting, next_meeting, gap_minutes, stress_analysis
                )
                
                suggestions.append({
                    'time': current_meeting.end_time.strftime('%H:%M'),
                    'duration': int(min(gap_minutes - 2, 15)),  # Leave 2 min buffer
                    'priority': priority,
                    'type': break_type,
                    'activity': activity,
                    'reason': self._get_break_reason(current_meeting, next_meeting, gap_minutes)
                })
        
        # Sort by priority
        return sorted(suggestions, key=lambda x: x['priority'], reverse=True)
    
    def _recommend_break_activity(self, current_meeting: Any, next_meeting: Any, 
                                gap_minutes: float, stress_analysis: Dict[str, Any]) -> Tuple[int, str, str]:
        """Recommend specific break activity based on context."""
        
        # Determine break urgency (priority 1-5)
        priority = 1
        
        # High stress meeting = higher priority break
        if any(keyword in current_meeting.title.lower() for keyword in 
               ['urgent', 'crisis', 'review', 'performance']):
            priority += 2
        
        # Many participants = mental fatigue
        if getattr(current_meeting, 'participants', 1) > 5:
            priority += 1
        
        # Long meeting = physical fatigue
        if current_meeting.duration_minutes > 60:
            priority += 1
        
        # Back-to-back detection
        if gap_minutes <= 10:
            priority += 2
        
        # Choose activity type based on context and available time
        if gap_minutes <= 5:
            break_type = 'mindfulness'
            activity = random.choice(self.activities['mindfulness'][min(5, int(gap_minutes))])
        elif current_meeting.duration_minutes > 90:
            break_type = 'movement'
            activity = random.choice(self.activities['movement'][min(15, int(gap_minutes))])
        elif gap_minutes >= 10:
            break_type = random.choice(['movement', 'recovery'])
            duration = min(15, int(gap_minutes))
            activity = random.choice(self.activities[break_type][duration])
        else:
            break_type = 'recovery'
            activity = random.choice(self.activities['recovery'][min(10, int(gap_minutes))])
        
        return min(priority, 5), break_type, activity
    
    def _get_break_reason(self, current_meeting: Any, next_meeting: Any, gap_minutes: float) -> str:
        """Generate explanation for break suggestion."""
        if gap_minutes <= 10:
            return "Back-to-back meetings detected - mental reset needed"
        elif current_meeting.duration_minutes > 90:
            return "Long meeting completed - physical movement recommended"
        elif getattr(current_meeting, 'participants', 1) > 8:
            return "Large group meeting - recovery time beneficial"
        elif any(keyword in current_meeting.title.lower() for keyword in ['review', 'performance']):
            return "High-stress meeting - stress relief recommended"
        else:
            return "Opportunity for wellbeing break"
    
    def _generate_optimization_tips(self, stress_analysis: Dict[str, Any]) -> List[str]:
        """Generate schedule optimization recommendations."""
        tips = []
        components = stress_analysis.get('components', {})
        stress_score = stress_analysis.get('daily_stress_score', 0)
        
        # Back-to-back meeting tips
        if components.get('back_to_back_penalty', 0) > 20:
            tips.append("🔄 Consider adding 15-minute buffers between consecutive meetings")
        
        # Recovery deficit tips
        if components.get('recovery_deficit', 0) > 15:
            tips.append("😴 Schedule longer breaks after complex meetings")
        
        # Lunch meeting tips
        meeting_analysis = stress_analysis.get('meeting_analysis', {})
        if meeting_analysis.get('lunch_meetings', 0) > 0:
            tips.append("🍽️ Protect your lunch hour - consider rescheduling non-critical lunch meetings")
        
        # High stress day tips
        if stress_score > 60:
            tips.extend([
                "⚡ Prepare meeting agendas in advance to reduce in-meeting stress",
                "💧 Set hydration reminders throughout the day",
                "📱 Use 'Do Not Disturb' between meetings to focus"
            ])
        
        # General wellness tips
        if stress_score > 40:
            tips.append("🧘 Consider starting the day with 5 minutes of mindfulness")
        
        # If low stress
        if stress_score <= 20:
            tips.append("🌟 Great schedule! Use this energy for creative or strategic work")
        
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
            return "No break opportunities found. Consider optimizing your schedule."
        
        summary = f"Found {total_breaks} break opportunities"
        if high_priority_breaks > 0:
            summary += f" ({high_priority_breaks} high priority)"
        
        return summary + f". {len(optimization_tips)} optimization tips available."
    
    def get_emergency_suggestions(self, stress_score: float) -> List[str]:
        """Get emergency stress relief suggestions for critical stress levels."""
        if stress_score >= 80:
            return [
                "🚨 IMMEDIATE: Take 10 deep breaths right now",
                "🚨 Cancel or reschedule non-critical meetings",
                "🚨 Block 15-minute recovery breaks in your calendar",
                "🚨 Speak with your manager about workload",
                "🚨 Consider working from home if possible"
            ]
        elif stress_score >= 60:
            return [
                "⚠️ Take a 5-minute break before your next meeting",
                "⚠️ Prepare agendas to make meetings more efficient",
                "⚠️ Decline lunch meetings to preserve energy",
                "⚠️ Set boundaries on after-hours communications"
            ]
        else:
            return []