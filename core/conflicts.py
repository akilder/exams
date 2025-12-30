# utils/conflicts.py

from typing import Dict
from datetime import datetime


def get_student_conflicts_sumary(student_conn):
    cur = student_conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM student_conflicts")
    return cur.fetchall()

def get_student_conflicts(student_conn):
    cur = student_conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM module_groups_today")
    rows = cur.fetchall()
    cur.close()
    conflict_dict = {}
    for row in rows:
        d = row['exam_date']
        conflict_dict.setdefault(d, set()).add(row['groups_info'])
    return conflict_dict



def get_all_student_conflicts(slot_datetime: datetime, all_student_conf_conn) -> Dict[int, bool]:
        cur = all_student_conf_conn.cursor(dictionary=True)
        cur.execute("""
            SELECT DISTINCT i1.module_id
            FROM inscriptions i1
            JOIN inscriptions i2
                ON i1.etudiant_id = i2.etudiant_id
                AND i1.module_id != i2.module_id
            JOIN examens e
                ON e.module_id = i2.module_id
            WHERE e.date_heure = %s
        """, (slot_datetime,))
        rows = cur.fetchall()
        cur.close()
        return {row["module_id"]: True for row in rows}

def has_student_conflict_for_module_in_slot(module_id: int, slot: datetime, student_conn) -> bool:
    cur = student_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) > 0
        FROM module_student_conflicts_today 
        WHERE checking_module = %s AND conflict_date = DATE(%s)
    """, (module_id, slot))
    result = cur.fetchone()[0]
    cur.close()
    return bool(result)

def has_student_conflict_for_module_in_slot_cached(module_id, slot, conflict_dict):
    if not conflict_dict:
        return False
    return module_id in conflict_dict.get(slot.date(), set())

def has_group_conflict(module_groups_info: str, slot_date, conflicts_dict: dict) -> bool:
    if slot_date not in conflicts_dict:
        return False

    # Split groups in the module
    module_groups_set = set(module_groups_info.split(','))

    # Check against all conflict strings for that date
    for conflict_str in conflicts_dict[slot_date]:
        conflict_set = set(conflict_str.split(','))
        if module_groups_set & conflict_set:  # intersection not empty
            return True
    return False




def get_prof_overload_conflicts(prof_conn):
    cur = prof_conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM prof_overload_conflicts")
    return cur.fetchall()


def get_room_capacity_conflicts(room_conn):
    cur = room_conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM room_capacity_conflicts")
    return cur.fetchall()


def get_all_overlap_conflicts(overlap_conn):
    cur = overlap_conn.cursor()
    cur.execute("SELECT * FROM overlap_conflicts")
    return cur.fetchall()


def get_conflicts_summary(summary_conn) -> dict:
    result = {
        "student_conflicts": len(get_student_conflicts_sumary(summary_conn)),
        "prof_conflicts": len(get_prof_overload_conflicts(summary_conn)),
        "room_capacity_conflicts": len(get_room_capacity_conflicts(summary_conn)),
        "time_overlap_conflicts": len(get_all_overlap_conflicts(summary_conn)),
    }
    return result

