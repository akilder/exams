# app/dashboard.py
import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.admin import admin_page
from utils.conflicts import conflicts_page
from utils.student_exam_page import student_exam_page
from utils.professor_exam_page import professor_exam_page
import streamlit as st

from db.connection import get_connection
from utils.KPI import kpi


st.set_page_config(
    page_title="Exams",
    layout="wide",
)

BOOTSTRAP_CSS = """
<style>
body { background-color: #f5f6fa; }

.block-card {
    background-color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}

.btn-primary {
    background-color: #0d6efd;
    color: white;
    padding: 0.4rem 0.9rem;
    border-radius: 0.35rem;
    border: none;
    cursor: pointer;
}
.btn-primary:hover { background-color: #0b5ed7; }

.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 0.4rem;
    font-size: 0.8rem;
    color: white;
}
.badge-green { background-color: #28a745; }
.badge-red   { background-color: #dc3545; }
.badge-blue  { background-color: #0d6efd; }
</style>
"""
st.markdown(BOOTSTRAP_CSS, unsafe_allow_html=True)


with st.sidebar:
    conn = get_connection()
    role = st.selectbox(
        "Role",
        ["Admin", "Vice-Doyen", "Chef de Département", "Étudiant", "Professeur"],
        key="role"
    )

if role == "Admin":
    admin_page(role, conn)
    conflicts_page(conn)
    st.markdown("---")
elif role == "Vice-Doyen":
    conflicts_page(conn)
    st.markdown("---")
    kpi(conn,role='Vice-Doyen')
elif role == 'Chef de Département':
    kpi(conn,'')
elif role == 'Étudiant':
    student_exam_page(conn,'')
elif role == 'Professeur':
    professor_exam_page(conn,'')
else:
    st.write(f"Role: {role}")


