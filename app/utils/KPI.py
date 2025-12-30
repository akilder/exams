from .department_kpis import department_kpis

def kpi(conn,role,dep_id=''):
    if dep_id:
        department_kpis(conn,role,dep_id)
    else:
        department_kpis(conn,role)
