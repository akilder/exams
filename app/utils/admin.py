import streamlit as st
from core import models
from core.generator import generate_edt
from datetime import datetime, time as dt_time
from .sidebar import render_sidebar
import time

def admin_page(role, conn):
    sidebar_inputs = render_sidebar(role)
    if not sidebar_inputs:
        return

    st.header("Exam Timetable Generator")

    st.markdown("### ⚙️ Actions")

    col1, col2 = st.columns([1, 1])

    with col1:
        generate_btn = st.button(
            "🚀 Generate Exams",
            type="primary",
            use_container_width=True
        )

    with col2:
        clear_btn = st.button(
            "🗑️ Clear All Exams",
            type="secondary",
            use_container_width=True
        )
    if clear_btn:
        models.clear_all_examens(conn)
        st.success("All exams cleared from the database.")

    if generate_btn:
        start_datetime = datetime.combine(sidebar_inputs["start_date"], dt_time.min)

        # Start timer
        start_time = time.perf_counter()

        with st.spinner("Generating exams..."):
            edt = generate_edt(
                conn, start_datetime, sidebar_inputs["hours"], sidebar_inputs["skip_friday"]
            )

        # Stop timer
        duration = time.perf_counter() - start_time

        st.success(f"Generated {edt} exams in {duration:.2f} seconds")
