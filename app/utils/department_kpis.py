import streamlit as st
import pandas as pd
import plotly.express as px
from core.models import get_departement_stats

def department_kpis(conn, role='',dep_id=''):
    if not dep_id and role != 'Vice-Doyen':
        dep_id_input = st.text_input("Enter your departement ID")
        if not dep_id_input:
            st.warning("Please enter your departement ID to view your schedule.")
            return
        try:
            dep_id = int(dep_id_input)
        except ValueError:
            st.error("departement ID must be a number.")
            return
    df = pd.DataFrame(get_departement_stats(conn, dep_id) if dep_id else get_departement_stats(conn))

    if df.empty:
        st.info("No departments found.")
        return

    st.markdown("## 📊 Global Department KPIs")
    total_departments = len(df)
    total_formations = df["nb_formations"].sum()
    total_modules = df["nb_modules"].sum()
    total_exams = df["nb_examens"].sum()
    total_students = df["nb_etudiants"].sum()
    total_profs = df["nb_profs"].sum()
    total_rooms_used = df["salles_utilisees"].sum()

    kpi_cols = st.columns(7)
    kpi_cols[0].metric("🏢 Departments", total_departments)
    kpi_cols[1].metric("📚 Formations", total_formations)
    kpi_cols[2].metric("📖 Modules", total_modules)
    kpi_cols[3].metric("📝 Exams", total_exams)
    kpi_cols[4].metric("👨‍🎓 Students", total_students)
    kpi_cols[5].metric("👩‍🏫 Professors", total_profs)
    kpi_cols[6].metric("🏫 Rooms Used", total_rooms_used)

    st.markdown("---")
    if not dep_id:
        st.markdown("## 🏛 Department Breakdown")
        department_options = ["All Departments"] + df["departement_nom"].tolist()
        selected_department = st.selectbox("Select Department", department_options)

        if selected_department != "All Departments":
            df_filtered = df[df["departement_nom"] == selected_department]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    metrics = {
        "Exams": "nb_examens",
        "Students": "nb_etudiants",
        "Professors": "nb_profs",
        "Rooms Used": "salles_utilisees"
    }

    for metric_name, col_name in metrics.items():
        st.markdown(f"### {metric_name}")
        fig = px.bar(
            df_filtered,
            x="departement_nom",
            y=col_name,
            text=col_name,
            color="departement_nom",
            labels={col_name: metric_name, "departement_nom": "Department"},
            height=400
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
