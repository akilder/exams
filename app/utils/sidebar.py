import streamlit as st
from datetime import datetime, time as dt_time

def build_hour_options(nbr_exams_per_day=1, start_time=dt_time(8,0), exam_duration=120):
    options = []
    start_minute = start_time.hour * 60 + start_time.minute
    current = start_minute
    for _ in range(nbr_exams_per_day):
        h, m = divmod(current, 60)
        if (h*60 + m + exam_duration) < 24*60:
            options.append((h, m))
            current += exam_duration
        else:
            break
    return options

def render_sidebar(role):
    with st.sidebar:
        if role == "Admin":
            st.header("Generation")

            start_date = st.date_input("Start date", datetime.now())
            start_time = st.time_input("Start hour", value=dt_time(8,0))
            nbr_slots_per_day = st.number_input("Number of slots per day", 1, 20, 4)
            exam_duration = st.number_input("Exam duration (minutes)", 30, 300, 120)
            skip_friday = st.checkbox("Skip Friday", value=True)

            all_hours = build_hour_options(nbr_slots_per_day, start_time, exam_duration)
            hours = st.multiselect("Hours per day", all_hours, default=all_hours)

            return {
                "start_date": start_date,
                "start_time": start_time,
                "nbr_slots_per_day": nbr_slots_per_day,
                "exam_duration": exam_duration,
                "skip_friday": skip_friday,
                "hours": hours
            }
    return None