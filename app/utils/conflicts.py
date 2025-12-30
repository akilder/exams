import streamlit as st
from core import conflicts
import pandas as pd
from core.models import get_all_exams_view, get_inscriptions, get_students_count


def conflicts_page(conn,role=''):
    exams_df = pd.DataFrame(get_all_exams_view(conn))
    students_count = get_students_count(conn)
    if not exams_df.empty:
        exams_df["jour"] = pd.to_datetime(exams_df["jour"]).dt.date
        exams_df["heure_debut"] = exams_df["heure_debut"].astype(str)
    else:
        exams_df = pd.DataFrame(columns=["id", "jour", "heure_debut", "module_nom", "nb_inscrits", "salles", "profs"])

    st.subheader("Global KPIs")
    total_exams = len(exams_df)
    avg_students_per_exam = exams_df["nb_inscrits"].mean() if total_exams > 0 else 0

    conf_summary = conflicts.get_conflicts_summary(conn)
    student_conflicts = conf_summary["student_conflicts"]
    prof_conflicts = conf_summary["prof_conflicts"]
    room_conflicts = conf_summary["room_capacity_conflicts"]
    time_overlap_conflicts = conf_summary["time_overlap_conflicts"]


    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("Students Number", students_count)
    kpi_col2.metric("Total Exams", total_exams)
    kpi_col3.metric("Total Inscriptions", get_inscriptions(conn))
    kpi_col4.metric("Average Students per Exam", f"{avg_students_per_exam:.1f}")

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
    kpi_col5.metric("Student Conflicts", student_conflicts)
    kpi_col6.metric("Professor Conflicts", prof_conflicts)
    kpi_col7.metric("Room Conflicts", room_conflicts)
    kpi_col8.metric("Time Overlaps", time_overlap_conflicts)
    if exams_df.empty:
        st.info("No exams scheduled yet")
        return
    else:
        unique_days = exams_df["jour"].unique()
        all_options = ["All"] + list(unique_days)
        selected_day = st.selectbox("Select day", all_options, index=0)

        if selected_day == "All":
            filtered_df = exams_df
        else:
            filtered_df = exams_df[exams_df["jour"] == selected_day]

        st.subheader(f"Exams for {selected_day} [{len(filtered_df)}]")
        st.dataframe(
            filtered_df[["date_heure", "module_nom", "nb_inscrits", "salles", "profs"]],
            use_container_width=True
        )



