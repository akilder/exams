import random

random.seed(42)

NB_DEPTS = 7
NB_FORMATIONS = 200
NB_ETUDIANTS = 25000
MODULES_MIN = 6
MODULES_MAX = 9
NB_PROFS = 250
BATCH_SIZE_INSCRIPTIONS = 400

departements = [
    ("Informatique", "INFO"),
    ("Mathématiques", "MATH"),
    ("Physique", "PHY"),
    ("Chimie", "CHIM"),
    ("Biologie", "BIO"),
    ("Economie", "ECO"),
    ("Gestion", "GEST"),
]

output = []

def w(line=""):
    output.append(line)

w("SET FOREIGN_KEY_CHECKS = 0;")
tables = [
    "exam_salle",
    "examens",
    "inscriptions",
    "etudiants",
    "modules",
    "formations",
    "profs",
    "salles",
    "departements"
]
for t in tables:
    w(f"DELETE FROM {t};")
w("SET FOREIGN_KEY_CHECKS = 1;\n")

w("INSERT INTO departements (nom, code) VALUES")
for i, (nom, code) in enumerate(departements):
    sep = "," if i < len(departements) - 1 else ";"
    w(f"('{nom}', '{code}'){sep}")
w()

formations = []
w("INSERT INTO formations (nom, dept_id, nb_modules, promo_code) VALUES")
for i in range(NB_FORMATIONS):
    dept_id = (i % NB_DEPTS) + 1
    nb_modules = random.randint(MODULES_MIN, MODULES_MAX)
    promo = f"F-{i+1:03d}"
    formations.append((i + 1, nb_modules))
    sep = "," if i < NB_FORMATIONS - 1 else ";"
    w(f"('Formation {i+1}', {dept_id}, {nb_modules}, '{promo}'){sep}")
w()

module_id = 1
modules_par_formation = {}

w("INSERT INTO modules (nom, formation_id) VALUES")
for f_id, nb_mod in formations:
    mods = []
    for _ in range(nb_mod):
        mods.append(module_id)
        w(f"('Module {module_id}', {f_id}),")
        module_id += 1
    modules_par_formation[f_id] = mods
output[-1] = output[-1].rstrip(",") + ";"
w()

w("INSERT INTO profs (nom, prenom, dept_id) VALUES")
for i in range(NB_PROFS):
    dept_id = random.randint(1, NB_DEPTS)
    sep = "," if i < NB_PROFS - 1 else ";"
    w(f"('Prof{i+1}', 'P{i+1}', {dept_id}){sep}")
w()

w("INSERT INTO salles (nom, capacite, type) VALUES")
salles = []

for i in range(20):
    salles.append((i+1, random.randint(80, 300), "amphi"))

for i in range(100):
    salles.append((i+21, 20, "salle"))

for i, (sid, cap, t) in enumerate(salles):
    sep = "," if i < len(salles) - 1 else ";"
    w(f"('S{sid}', {cap}, '{t}'){sep}")
w()

groups = []  # (group_id, formation_id, nbr_etudiants)
GROUPS_PER_FORMATION = 5  # for example

group_id_counter = 1
w("INSERT INTO groups (nom, formation_id, nbr_etudiants) VALUES")
for f_id, nb_mod in formations:
    for g in range(GROUPS_PER_FORMATION):
        nbr_etudiants = 0  # will be updated later when generating students
        sep = "," if not (f_id == formations[-1][0] and g == GROUPS_PER_FORMATION-1) else ";"
        w(f"('Group {group_id_counter}', {f_id}, {nbr_etudiants}){sep}")
        groups.append((group_id_counter, f_id))
        group_id_counter += 1
w()

# Generate etudiants with group_id
etudiants = []  # (etu_id, formation_id, group_id)

w("INSERT INTO etudiants (nom, prenom, formation_id, group_id) VALUES")
for etu_id in range(1, NB_ETUDIANTS + 1):
    f_id = random.randint(1, NB_FORMATIONS)
    group_id = random.choice([g[0] for g in groups if g[1] == f_id])
    etudiants.append((etu_id, f_id, group_id))
    sep = "," if etu_id < NB_ETUDIANTS else ";"
    w(f"('Etudiant{etu_id}', 'E{etu_id}', {f_id}, {group_id}){sep}")
w()

w("\n-- INSCRIPTIONS")
inscriptions = []

TARGET_INSCRIPTIONS = 130_000

avg_modules = TARGET_INSCRIPTIONS // NB_ETUDIANTS

for etu_id, f_id, group_id in etudiants:
    f_mods = modules_par_formation[f_id]
    min_mod = max(1, int(len(f_mods) * 0.8))
    max_mod = len(f_mods)
    num_modules = min(len(f_mods), random.randint(min_mod, max_mod))
    # randomly pick modules
    for mid in random.sample(f_mods, num_modules):
        inscriptions.append((etu_id, mid))


# batch insert
for i in range(0, len(inscriptions), BATCH_SIZE_INSCRIPTIONS):
    batch = inscriptions[i:i + BATCH_SIZE_INSCRIPTIONS]
    w("INSERT INTO inscriptions (etudiant_id, module_id) VALUES")
    for j, (etu, mod) in enumerate(batch):
        sep = "," if j < len(batch) - 1 else ";"
        w(f"({etu}, {mod}){sep}")
w()


with open("../db/dataset.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

