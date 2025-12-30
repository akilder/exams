import streamlit as st
import pandas as pd
from core.models import get_student_exam_schedule


def student_exam_page(conn, student_id):
    st.title("My Exam Schedule")
    if not student_id:
        student_id_input = st.text_input("Enter your student ID")
        if not student_id_input:
            st.warning("Please enter your student ID to view your schedule.")
            return
        try:
            student_id = int(student_id_input)
        except ValueError:
            st.error("student ID must be a number.")
            return

    exams_df = pd.DataFrame(get_student_exam_schedule(conn, student_id))

    if exams_df.empty:
        st.info("No exams scheduled for you.")
        return

    exams_df["jour"] = pd.to_datetime(exams_df["jour"]).dt.date
    exams_df["heure_debut"] = pd.to_datetime(exams_df["date_heure"])

    unique_days = exams_df["jour"].unique()
    all_options = ["All Days"] + list(unique_days)
    selected_day = st.selectbox("Select Day", all_options)

    if selected_day != "All Days":
        exams_df = exams_df[exams_df["jour"] == selected_day]

    st.markdown("---")
    st.subheader(f"Exams for {selected_day} [{len(exams_df)}]")

    for _, row in exams_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 3])

            col1.markdown(f"Module: {row['module_nom']}")
            col2.markdown(f"Time:{row['heure_debut']}")
            col3.markdown(f"Room(s): {row['salles']}  \nProfs: {row['profs']}")

            st.markdown(f" Number of Students: {row['nb_inscrits']}")
            st.markdown("---")
