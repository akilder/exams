from datetime import datetime, timedelta
from typing import Iterable, Union, Tuple

from core.conflicts import get_student_conflicts
from core.models import  select_best_module
from core import models


def exam_slots_generator(
        start_date: datetime,
        hours_per_day: Iterable[Union[int, Tuple[int, int]]] = ((8, 0), (10, 0), (12, 0), (14, 0)),
        skip_friday: bool = False,
):
    current = start_date
    while True:
        if skip_friday and current.weekday() == 4:
            current += timedelta(days=1)
            continue

        for h in hours_per_day:
            if isinstance(h, tuple):
                hr, mn = h
            else:
                hr, mn = h, 0
            yield current.replace(hour=hr, minute=mn, second=0, microsecond=0)

        current += timedelta(days=1)


def generate_edt(initial_conn,
                 start_date: datetime = datetime.now(),
                 hours_per_day: Iterable[Tuple[int, int]] = ((8, 15), (10, 15), (12, 15), (14, 15)),
                 skip_friday=True,
                 exam_duration=120
                 ):
    modules = models.get_modules_to_schedule(initial_conn)
    if not modules:
        return
    slots_gen = exam_slots_generator(
        start_date=start_date,
        hours_per_day=hours_per_day,
        skip_friday=skip_friday,
    )

    conflict_dict = get_student_conflicts(initial_conn)

    slot = next(slots_gen)

    profs_slot = []
    free_rooms = []
    salles = None
    best_profs = None
    module = None
    new_module = True
    new_slot = False
    generated_exams_count = 0
    while modules:
        if not free_rooms or new_slot:
            free_rooms = models.get_free_rooms_for_slot(slot, initial_conn)
        if not profs_slot or new_slot:
            profs_slot = models.get_all_profs_for_slot(slot, initial_conn)
        if new_slot or new_module:
            module,salles ,best_profs= select_best_module(modules, slot, free_rooms,profs_slot,conflict_dict)
            new_module = False
        new_slot = False

        if (not module or not free_rooms or not profs_slot) or \
                (salles is None or best_profs is None or len(salles) != len(best_profs)):
            slot = next(slots_gen)
            new_slot = True
            continue

        exam_id = models.create_examen(
            conn=initial_conn,
            module_id=module['id'],
            date_heure=slot,
            duree_minutes=exam_duration,
        )

        models.add_rooms_to_exam(exam_id, salles, best_profs, initial_conn)
        conflict_dict.setdefault(slot.date(), set()).add(module['groups_info'])
        modules.remove(module)
        generated_exams_count +=1
        new_module = True

        for prof, salle in zip(best_profs, salles):
            profs_slot.remove(prof)
            free_rooms.remove(salle)

        if not free_rooms or not profs_slot:
            slot = next(slots_gen)
            new_slot = True
    return generated_exams_count

