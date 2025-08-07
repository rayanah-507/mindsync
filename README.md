# MindSync: Personal Wellbeing Companion

## Abstract
**MindSync** is an intelligent wellbeing companion application designed to proactively manage stress by analyzing digital calendar data. The system integrates with major calendar platforms to predict periods of high cognitive load and delivers personalized, evidence-based recommendations to maintain optimal productivity and mental wellbeing.

---

## Project Overview
- **Course:** ECS537U Design and Build in Artificial Intelligence  
- **Academic Year:** 2024–25 (Resit)  
- **Project Type:** Individual Research Implementation  
- **Duration:** 4 weeks  

---

## Research Objectives
- **Stress Prediction:** Develop heuristic models grounded in workplace stress literature to identify periods of cognitive overload from calendar patterns  
- **Intervention Timing:** Implement algorithms to optimize the placement of wellbeing activities within existing schedules  
- **Personalization:** Create context-aware recommendation systems that adapt to individual calendar characteristics and meeting types  

---

## Technical Architecture

### Core Components
- **Calendar Integration Layer:** Supports Google Calendar and Microsoft Outlook APIs with JSON-based data processing  
- **Stress Prediction Engine:** Rule-based heuristic system analyzing meeting density, duration, and temporal patterns  
- **Recommendation System:** Evidence-based activity suggestions (e.g., breathing exercises, movement breaks, mindfulness sessions)  
- **Scheduling Optimizer:** Intelligent placement of wellbeing interventions using available time slots  

### Technology Stack
- **Frontend:** Streamlit (Python web framework)  
- **Data Processing:** Pandas, NumPy for calendar data analysis  
- **Visualization:** Plotly for interactive timeline and stress pattern displays  
- **Authentication:** Session-based user management with secure password hashing  

---

## Theoretical Foundation
The stress prediction methodology is grounded in established research on:

- Cognitive Load Theory (Sweller, 1988)  
- Meeting Fatigue and Attention Restoration (Kaplan, 1995)  
- Temporal Patterns in Workplace Stress (Sonnentag & Fritz, 2007)  
- Break Timing Optimization (Trougakos & Hideg, 2009)  

---

## Installation & Usage

### Prerequisites
- Python 3.8+  
- Virtual environment (recommended)  

### Setup
```bash
git clone <repository-url>
cd mindsync
pip install -r requirements.txt
streamlit run app.py
