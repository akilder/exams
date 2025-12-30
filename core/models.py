# utils/models.py

from datetime import datetime
from typing import List, Dict
from core.conflicts import has_student_conflict_for_module_in_slot, has_student_conflict_for_module_in_slot_cached, \
    has_group_conflict

def get_students_count(conn) -> int:
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COUNT(id) AS total
        FROM etudiants;
    """)
    number = cur.fetchone()
    cur.close()
    return number['total']
# ============================
# 1) MODULES / FORMATIONS
# ============================

def get_modules_to_schedule(conn2) -> List[Dict]:
    cur = conn2.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM modules_with_groups
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def get_student_count_for_module(module_id: int,conn) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT nb_inscrits 
        FROM modules 
        WHERE id = %s
    """, (module_id,))
    (count,) = cur.fetchone()
    cur.close()
    return count


def get_students_for_module(module_id: int,conn) -> List[int]:
    cur = conn.cursor()
    cur.execute("""
        SELECT etudiant_id
        FROM inscriptions
        WHERE module_id = %s
        ORDER BY etudiant_id
    """, (module_id,))
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    return ids

def get_departement_stats(conn, dep_id=''):
    cur = conn.cursor(dictionary=True)

    if dep_id:
        cur.execute("""
            SELECT *
            FROM departement_stats
            WHERE departement_id = %s
        """, (dep_id,))
    else:
        cur.execute("SELECT * FROM departement_stats")

    result = cur.fetchall()
    cur.close()
    return result

def get_student_exam_schedule(conn, student_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT *
        FROM student_exam_schedule
        WHERE etudiant_id = %s
        ORDER BY date_heure
    """, (student_id,))
    result = cur.fetchall()
    cur.close()
    return result

def prof_exam_schedule(conn,prof_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
            SELECT *
            FROM prof_exam_schedule
            WHERE prof_id = %s
            ORDER BY date_heure
        """, (prof_id,))
    result = cur.fetchall()
    cur.close()
    return result
def get_inscriptions(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM inscriptions")
    result = cur.fetchone()
    cur.close()
    return result['total']
# ============================
# 2) PROFS
# ============================
def get_profs_for_dept_on_date(dept_id: int, exam_date: datetime, conn) -> List[Dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, nom, prenom, dept_id, exams_today
        FROM profs_available_by_dept 
        WHERE dept_id = %s AND exam_date = %s
    """, (dept_id, exam_date.date()))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_all_profs(conn) -> List[Dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT *
        FROM profs;
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_all_profs_for_slot(slot_datetime, conn):
    cur = conn.cursor(dictionary = True)

    cur.execute("""
        SELECT p.id, p.nom, p.dept_id
        FROM profs p
        WHERE p.id NOT IN (
            SELECT es.prof_id
            FROM exam_salle es
            JOIN examens e ON e.id = es.exam_id
            WHERE DATE(e.date_heure) = DATE(%s)
        )
        AND p.id NOT IN (
            SELECT es.prof_id
            FROM exam_salle es
            JOIN examens e ON e.id = es.exam_id
            WHERE DATE(e.date_heure) = DATE(%s)
            GROUP BY es.prof_id
            HAVING COUNT(e.id) >= 3
        )
    """, (slot_datetime, slot_datetime))

    profs = cur.fetchall()
    cur.close()

    return profs



def choose_best_profs_for_module(module, salles, available_profs):
    best_profs = []
    assigned_profs = set()

    for salle in salles:
        best_prof = None
        for prof in available_profs:
            if prof["dept_id"] == module["dept_id"] and prof["id"] not in assigned_profs:
                best_prof = prof
                assigned_profs.add(prof["id"])
                break

        if not best_prof and available_profs:
            for prof in available_profs:
                if prof["id"] not in assigned_profs:
                    best_prof = prof
                    assigned_profs.add(prof["id"])
                    break

        if best_prof is not None:
            best_profs.append(best_prof)

    return best_profs


# ============================
# 3) SALLES
# ============================

def get_free_rooms_for_slot(slot_datetime: datetime,conn) -> List[Dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            s.id,
            s.nom,
            s.capacite,
            s.type
        FROM salles s
        WHERE NOT EXISTS (
            SELECT 1
            FROM examens e
            JOIN exam_salle egs ON e.id = egs.exam_id
            WHERE egs.salle_id = s.id
              AND e.date_heure = %s
        )
        ORDER BY s.capacite ASC;
    """, (slot_datetime,))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_all_rooms(conn) -> List[Dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, nom, capacite, type
        FROM salles
        ORDER BY capacite ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_total_capacity_for_all_rooms(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
    SELECT SUM(capacite)
    FROM salles
    """)
    result = cur.fetchone()
    cur.close()
    return result

def choose_salle_for_module(module,rooms):
    total_capacity = sum(r["capacite"] for r in rooms)
    if total_capacity < module["nb_inscrits"]:
        return []

    available_rooms = rooms.copy()
    salles = []
    remaining = module['nb_inscrits']

    while remaining > 0 and available_rooms:
        room = min(available_rooms, key=lambda r: abs(1 - r["capacite"] / remaining))
        salles.append(room)
        remaining -= room["capacite"]
        available_rooms.remove(room)

    return salles


# ============================
# 4) EXAMENS + EXAM_SALLE
# ============================

def get_total_exams_needed(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM modules WHERE nb_inscrits > 0;")
    (count,) = cur.fetchone()
    cur.close()
    return count

def get_rooms_count(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM salles;")
    (count,) = cur.fetchone()
    cur.close()
    return count

def create_examen(
    module_id: int,
    date_heure: datetime,
    conn,
    duree_minutes: int = 120,
) -> int:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO examens (module_id, date_heure, duree_minutes)
        VALUES (%s, %s, %s)
    """, (module_id, date_heure, duree_minutes))
    exam_id = cur.lastrowid
    conn.commit()
    cur.close()
    return exam_id

def add_rooms_to_exam(
    exam_id: int,
    salles: List[Dict],
    profs,
    conn,
) -> None:
    cur = conn.cursor()
    if len(salles) != len(profs):
        raise ValueError("The number of salles does not match the number of professors.")
    data = [(exam_id, s["id"], p["id"]) for s, p in zip(salles, profs)]
    cur.executemany("INSERT INTO exam_salle (exam_id, salle_id, prof_id) VALUES (%s,%s,%s)", data)
    conn.commit()
    cur.close()


def add_rooms_to_exam2(
    exam_id: int,
    salles,
    profs,
    conn,
) -> None:
    cur = conn.cursor()
    data = [(exam_id, s, p) for s, p in zip(salles, profs)]
    cur.executemany("INSERT INTO exam_salle (exam_id, salle_id, prof_id) VALUES (%s,%s,%s)", data)
    conn.commit()
    cur.close()


def update_exam_prof(exam_id: int, new_prof_id: int,conn) -> None:
    cur = conn.cursor()
    cur.execute("""
        UPDATE examens
        SET prof_id = %s
        WHERE id = %s
    """, (new_prof_id, exam_id))
    conn.commit()
    cur.close()


def update_exam_datetime(exam_id: int, new_datetime: datetime,conn) -> None:
    cur = conn.cursor()
    cur.execute("""
        UPDATE examens
        SET date_heure = %s
        WHERE id = %s
    """, (new_datetime, exam_id))
    conn.commit()
    cur.close()


def clear_all_examens(conn) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM exam_salle;")
    cur.execute("DELETE FROM examens;")
    conn.commit()
    cur.close()


def get_all_exams_view(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT *
        FROM all_exams_complete 
    """)
    return cur.fetchall()
def get_all_exams(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
            SELECT * FROM examens ORDER BY date_heure ASC
        """)
    return cur.fetchall()


# ============================
# 5) CHECKS / CONFLICT HELPERS
# ============================

def count_exams_for_prof_on_date(prof_id: int, exam_date: datetime,conn) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM examens
        WHERE prof_id = %s AND DATE(date_heure) = %s
    """, (prof_id, exam_date.date()))
    (count,) = cur.fetchone()
    cur.close()
    return count


def room_is_free(salle_id: int, slot_datetime: datetime,conn) -> bool:
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM examens e
        JOIN exam_salle egs ON e.id = egs.exam_id
        WHERE egs.salle_id = %s
          AND e.date_heure = %s
    """, (salle_id, slot_datetime))
    (count,) = cur.fetchone()
    cur.close()
    return count == 0





def calculate_module_score(module, current_slot, available_rooms,available_profs,conflict_dict):
    slot_date = current_slot.date()
    if has_group_conflict(module['groups_info'], slot_date, conflict_dict):
        return False,False

    best_room = choose_salle_for_module(module, available_rooms)
    if best_room is None:
        return False, False
    best_profs = choose_best_profs_for_module(module, best_room, available_profs)
    if best_profs is None:
        return False, False
    return best_room, best_profs



def select_best_module(modules, current_slot, available_rooms,available_profs, conflict_dict):
    for module in modules:
        best_room,best_profs = calculate_module_score(module, current_slot, available_rooms,available_profs,conflict_dict)
        if best_room and best_profs:
            return module, best_room ,best_profs
    return None, None, None



def select_best_module2(modules, current_slot, available_rooms,available_profs, conflict_dict):
    for module in modules:
        best_room,best_profs = calculate_module_score2(module, current_slot, available_rooms,available_profs,conflict_dict)
        if best_room and best_profs:
            return module, best_room ,best_profs
    return None, None, None


def calculate_module_score2(module, current_slot, available_rooms,available_profs,conflict_dict):
    slot_date = current_slot.date()
    if has_group_conflict(module['groups_info'], slot_date, conflict_dict):
        return False,False

    best_room = choose_salle_for_module2(module, available_rooms)
    if best_room is None:
        return False, False
    best_profs = choose_best_profs_for_module2(module, best_room, available_profs)
    if best_profs is None:
        return False, False
    return best_room, best_profs


def choose_salle_for_module2(module, rooms):
    total_capacity = sum(rooms.values())
    if total_capacity < module["nb_inscrits"]:
        return []  # not enough capacity

    available_rooms = rooms.copy()
    salles = []
    remaining = module['nb_inscrits']

    while remaining > 0 and available_rooms:
        # pick the room that best fits the remaining students
        room_id = min(available_rooms, key=lambda rid: abs(1 - available_rooms[rid] / remaining))
        salles.append(room_id)
        remaining -= available_rooms[room_id]
        del available_rooms[room_id]

    return salles



def choose_best_profs_for_module2(module, salles, available_profs):
    best_profs = []
    assigned_profs = set()

    for _ in salles:
        best_prof_id = None

        for prof_id, dept_id in available_profs.items():
            if dept_id == module["dept_id"] and prof_id not in assigned_profs:
                best_prof_id = prof_id
                assigned_profs.add(prof_id)
                break

        if best_prof_id is None:
            for prof_id in available_profs:
                if prof_id not in assigned_profs:
                    best_prof_id = prof_id
                    assigned_profs.add(prof_id)
                    break

        if best_prof_id is not None:
            best_profs.append(best_prof_id)

    return best_profs



