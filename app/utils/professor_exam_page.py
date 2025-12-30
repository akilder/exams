import streamlit as st
import pandas as pd
from core.models import prof_exam_schedule

def professor_exam_page(conn, prof_id):
    st.title("My Exam Supervision Schedule")
    if not prof_id:
        prof_id_input = st.text_input("Enter your Professor ID")
        if not prof_id_input:
            st.warning("Please enter your Professor ID to view your schedule.")
            return
        try:
            prof_id = int(prof_id_input)
        except ValueError:
            st.error("Professor ID must be a number.")
            return
    exams_df = pd.DataFrame(prof_exam_schedule(conn, prof_id))

    if exams_df.empty:
        st.info("No exams assigned for you.")
        return

    exams_df["jour"] = pd.to_datetime(exams_df["jour"]).dt.date
    exams_df["heure_debut"] = pd.to_datetime(exams_df["date_heure"]).dt.strftime("%H:%M")

    total_exams = len(exams_df)
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    kpi_col1.metric("Total Exams", total_exams)
    st.markdown("---")

    unique_days = exams_df["jour"].unique()
    all_options = ["All Days"] + list(unique_days)
    selected_day = st.selectbox("Select Day", all_options)

    if selected_day != "All Days":
        exams_df = exams_df[exams_df["jour"] == selected_day]

    st.subheader(f"Exams for {selected_day} [{len(exams_df)}]")

    for _, row in exams_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 3])
            col1.markdown(f" Module: {row['module_nom']}")
            col2.markdown(f" Time: {row['heure_debut']}  \n Date: {row['jour']}")
            col3.markdown(f"* Room: {row['salles']}  \n Students: {row['nb_inscrits']}")
            st.markdown("---")
