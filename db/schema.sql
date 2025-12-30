CREATE DATABASE edt_examens CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE edt_examens;



CREATE TABLE departements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL
);


CREATE TABLE formations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(200) NOT NULL,
    dept_id INT NOT NULL,
    nb_modules INT DEFAULT 6,
    promo_code VARCHAR(20),
    FOREIGN KEY (dept_id) REFERENCES departements(id)
);


CREATE TABLE `groups` (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(200) NOT NULL,
    formation_id INT NOT NULL,
    nbr_etudiants INT NOT NULL DEFAULT 0,
    FOREIGN KEY (formation_id) REFERENCES formations(id)
);

CREATE TABLE etudiants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    formation_id INT NOT NULL,
    group_id INT NOT NULL,
    FOREIGN KEY (formation_id) REFERENCES formations(id),
    FOREIGN KEY (group_id) REFERENCES `groups`(id)
);

CREATE TABLE modules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(200) NOT NULL,
    nb_inscrits INT NOT NULL DEFAULT 0,
    formation_id INT NOT NULL,
    FOREIGN KEY (formation_id) REFERENCES formations(id)
);


CREATE TABLE profs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departements(id)
);

CREATE TABLE salles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    capacite INT NOT NULL,
    type ENUM('amphi','salle') DEFAULT 'salle',
    batiment VARCHAR(50) NULL ,
    etage INT NULL
);

CREATE TABLE inscriptions (
    etudiant_id INT NOT NULL,
    module_id INT NOT NULL,
    PRIMARY KEY (etudiant_id, module_id),
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id)  REFERENCES modules(id)   ON DELETE CASCADE
);

CREATE TABLE examens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    module_id INT NOT NULL,
    date_heure DATETIME NOT NULL,
    duree_minutes INT NOT NULL DEFAULT 90,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);
CREATE TABLE exam_salle (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL,
    salle_id INT NOT NULL,
    prof_id INT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES examens(id) ON DELETE CASCADE,
    FOREIGN KEY (salle_id) REFERENCES salles(id),
    FOREIGN KEY (prof_id)   REFERENCES profs(id),
    UNIQUE (exam_id, salle_id,prof_id)
);
CREATE INDEX idx_insc_module_etud
ON inscriptions (module_id, etudiant_id);

CREATE INDEX idx_examsalle_profid_examid
ON exam_salle (prof_id, exam_id);

CREATE INDEX idx_examsalle_examid_salleid
ON exam_salle (exam_id, salle_id);

CREATE INDEX idx_examsalle_salleid
ON exam_salle (salle_id);

CREATE INDEX idx_examens_dateheure
ON examens (date_heure);

CREATE INDEX idx_examens_module
ON examens (module_id);

CREATE INDEX idx_examens_date_module
ON examens (date_heure, module_id);

CREATE INDEX idx_examens_datetime_id
ON examens (date_heure, id);

CREATE INDEX idx_examens_module_date
ON examens (module_id, date_heure);

CREATE INDEX idx_modules_nbinscrits
ON modules (nb_inscrits DESC);

CREATE INDEX idx_groups_formation ON `groups`(formation_id);

CREATE INDEX idx_modules_formation
ON modules (formation_id, id);

CREATE INDEX idx_formations_dept
ON formations (dept_id, id);

CREATE INDEX idx_etudiants_formation
ON etudiants (formation_id, id);

CREATE INDEX idx_profs_dept
ON profs (dept_id, id);

CREATE INDEX idx_salles_type_capacite
ON salles (type, capacite);


CREATE INDEX idx_salles_capacite ON salles(capacite);






CREATE VIEW student_conflicts AS
SELECT
    i.etudiant_id,
    DATE(e.date_heure) AS jour,
    COUNT(e.id) AS nb_examens,
    GROUP_CONCAT(e.id) AS exam_ids
FROM inscriptions i
JOIN examens e ON e.module_id = i.module_id
GROUP BY i.etudiant_id, DATE(e.date_heure)
HAVING COUNT(e.id) > 1
ORDER BY nb_examens DESC;



CREATE VIEW departement_stats AS
SELECT
    d.id AS departement_id,
    d.nom AS departement_nom,
    d.code AS departement_code,

    COUNT(DISTINCT f.id) AS nb_formations,
    COUNT(DISTINCT m.id) AS nb_modules,
    COUNT(DISTINCT e.id) AS nb_examens,
    COUNT(DISTINCT et.id) AS nb_etudiants,
    COUNT(DISTINCT p.id) AS nb_profs,
    COUNT(DISTINCT s.id) AS salles_utilisees

FROM departements d
LEFT JOIN formations f   ON f.dept_id = d.id
LEFT JOIN modules m      ON m.formation_id = f.id
LEFT JOIN examens e      ON e.module_id = m.id
LEFT JOIN exam_salle es  ON es.exam_id = e.id
LEFT JOIN salles s       ON s.id = es.salle_id
LEFT JOIN profs p        ON p.dept_id = d.id
LEFT JOIN etudiants et   ON et.formation_id = f.id
GROUP BY d.id, d.nom, d.code;

CREATE VIEW modules_with_groups AS
SELECT
    m.id,
    m.nom,
    m.nb_inscrits,
    f.dept_id,
    GROUP_CONCAT(CONCAT(g.id, ':', g.nbr_etudiants) ORDER BY g.id) AS groups_info
FROM modules m
JOIN formations f ON m.formation_id = f.id
LEFT JOIN examens e ON e.module_id = m.id
JOIN inscriptions i ON i.module_id = m.id
JOIN etudiants et ON et.id = i.etudiant_id
JOIN `groups` g ON g.id = et.group_id
WHERE e.id IS NULL
GROUP BY m.id, m.nom, m.nb_inscrits, f.dept_id
ORDER BY m.nb_inscrits DESC;


CREATE VIEW module_student_conflicts_today AS
SELECT DISTINCT
    i1.module_id AS checking_module,
    DATE(e.date_heure) AS conflict_date,
    COUNT(DISTINCT i1.etudiant_id) AS conflicting_students
FROM inscriptions i1
JOIN inscriptions i2 ON i1.etudiant_id = i2.etudiant_id
    AND i1.module_id != i2.module_id
JOIN examens e ON e.module_id = i2.module_id
GROUP BY i1.module_id, DATE(e.date_heure)
HAVING COUNT(DISTINCT i1.etudiant_id) > 0;

CREATE OR REPLACE VIEW module_groups_today AS
SELECT
    i1.module_id AS module_id,
    DATE(e.date_heure) AS exam_date,
    GROUP_CONCAT(DISTINCT CONCAT(g.id, ':', g.nbr_etudiants) ORDER BY g.id) AS groups_info
FROM inscriptions i1
JOIN examens e
    ON e.module_id = i1.module_id
JOIN etudiants et
    ON et.id = i1.etudiant_id
JOIN `groups` g
    ON g.id = et.group_id
GROUP BY i1.module_id, DATE(e.date_heure);


CREATE VIEW student_exam_schedule AS
SELECT
    e.id AS exam_id,
    e.date_heure,
    DATE(e.date_heure) AS jour,
    TIME(e.date_heure) AS heure_debut,
    m.nom AS module_nom,
    m.nb_inscrits,
    GROUP_CONCAT(DISTINCT s.nom SEPARATOR ', ') AS salles,
    GROUP_CONCAT(DISTINCT CONCAT(p.nom, ' ', p.prenom) SEPARATOR ', ') AS profs,
    et.id AS etudiant_id
FROM examens e
JOIN modules m          ON e.module_id = m.id
JOIN inscriptions i      ON i.module_id = m.id
JOIN etudiants et        ON et.id = i.etudiant_id
LEFT JOIN exam_salle es  ON es.exam_id = e.id
LEFT JOIN salles s       ON s.id = es.salle_id
LEFT JOIN profs p        ON p.id = es.prof_id
GROUP BY e.id, et.id
ORDER BY e.date_heure;

CREATE VIEW prof_exam_schedule AS
SELECT
    e.id AS exam_id,
    e.date_heure,
    TIME(e.date_heure) AS heure_debut,
    DATE(e.date_heure) AS jour,
    m.nom AS module_nom,
    m.nb_inscrits,
    p.id AS prof_id,
    GROUP_CONCAT(DISTINCT s.nom SEPARATOR ', ') AS salles,
    CONCAT(p.nom, ' ', p.prenom) AS prof
FROM examens e
JOIN modules m ON e.module_id = m.id
JOIN exam_salle es ON e.id = es.exam_id
JOIN salles s ON es.salle_id = s.id
JOIN profs p ON es.prof_id = p.id
GROUP BY e.id, e.date_heure, m.nom, m.nb_inscrits, p.id
ORDER BY e.date_heure;


CREATE VIEW prof_overload_conflicts AS
SELECT
    p.id AS prof_id,
    CONCAT(p.nom, ' ', p.prenom) AS prof_nom,
    p.dept_id,
    DATE(e.date_heure) AS jour,
    COUNT(es.exam_id) AS nb_examens,
    GROUP_CONCAT(e.id) AS exam_ids
FROM exam_salle es
JOIN profs p ON es.prof_id = p.id
JOIN examens e ON es.exam_id = e.id
GROUP BY p.id, DATE(e.date_heure)
HAVING COUNT(es.exam_id) > 3
ORDER BY nb_examens DESC;



CREATE VIEW room_capacity_conflicts AS
SELECT
    e.id AS exam_id,
    e.date_heure,
    e.module_id,
    COUNT(i.etudiant_id) AS total_inscrits,
    SUM(s.capacite) AS total_capacite,
    COUNT(i.etudiant_id) - SUM(s.capacite) AS deficit,
    m.nom AS module_nom
FROM examens e
JOIN exam_salle es ON e.id = es.exam_id
JOIN salles s ON es.salle_id = s.id
JOIN inscriptions i ON i.module_id = e.module_id
JOIN modules m ON m.id = e.module_id
GROUP BY e.id, e.date_heure, e.module_id, m.nom
HAVING COUNT(i.etudiant_id) > SUM(s.capacite)
ORDER BY deficit DESC;


CREATE VIEW overlap_conflicts AS
SELECT
    'salle' AS type_conflit,
    s.nom AS resource,
    e1.id AS exam1_id,
    e2.id AS exam2_id,
    e1.date_heure AS exam1_time,
    e2.date_heure AS exam2_time,
    TIMEDIFF(e2.date_heure, e1.date_heure) AS time_diff
FROM examens e1
JOIN exam_salle es1 ON e1.id = es1.exam_id
JOIN examens e2 ON e1.id < e2.id
JOIN exam_salle es2 ON e2.id = es2.exam_id
JOIN salles s ON es1.salle_id = es2.salle_id AND es1.salle_id = s.id
WHERE e1.date_heure = e2.date_heure

UNION ALL

SELECT
    'prof' AS type_conflit,
    CONCAT(p.nom, ' ', p.prenom) AS resource,
    e1.id AS exam1_id,
    e2.id AS exam2_id,
    e1.date_heure AS exam1_time,
    e2.date_heure AS exam2_time,
    TIMEDIFF(e2.date_heure, e1.date_heure) AS time_diff
FROM exam_salle es1
JOIN exam_salle es2 ON es1.prof_id = es2.prof_id
JOIN examens e1 ON es1.exam_id = e1.id
JOIN examens e2 ON es2.exam_id = e2.id
JOIN profs p ON es1.prof_id = p.id
WHERE e1.date_heure = e2.date_heure
  AND e1.module_id != e2.module_id
  AND e1.id < e2.id

ORDER BY type_conflit, exam1_time DESC;


CREATE VIEW modules_to_schedule AS
SELECT
    m.id,
    m.nom,
    m.nb_inscrits,
    f.dept_id
FROM modules m
JOIN formations f ON m.formation_id = f.id
LEFT JOIN examens e ON e.module_id = m.id
WHERE e.id IS NULL
AND m.nb_inscrits <= (SELECT SUM(capacite) FROM salles)
ORDER BY m.nb_inscrits DESC;


CREATE VIEW all_exams_complete AS
SELECT
    e.id,
    e.date_heure,
    TIME(e.date_heure) AS heure_debut,
    DATE(e.date_heure) AS jour,
    m.nom AS module_nom,
    m.nb_inscrits,
    GROUP_CONCAT(DISTINCT s.nom SEPARATOR ', ') AS salles,
    GROUP_CONCAT(DISTINCT CONCAT(p.nom, ' ', p.prenom) SEPARATOR ', ') AS profs,
    GROUP_CONCAT(DISTINCT s.id SEPARATOR ',') AS salles_ids,
    GROUP_CONCAT(DISTINCT p.id SEPARATOR ',') AS profs_ids
FROM examens e
JOIN modules m ON e.module_id = m.id
LEFT JOIN exam_salle es ON e.id = es.exam_id
LEFT JOIN salles s ON es.salle_id = s.id
LEFT JOIN profs p ON es.prof_id = p.id
GROUP BY e.id, e.date_heure, m.nom, m.nb_inscrits
ORDER BY e.date_heure;



CREATE VIEW profs_available_by_dept AS
SELECT
    p.id,
    p.nom,
    p.prenom,
    p.dept_id,
    DATE(e.date_heure) AS exam_date,
    COALESCE(COUNT(es.exam_id), 0) AS exams_today
FROM profs p
LEFT JOIN exam_salle es ON p.id = es.prof_id
LEFT JOIN examens e ON es.exam_id = e.id
GROUP BY p.id, p.nom, p.prenom, p.dept_id, DATE(e.date_heure)
HAVING exams_today < 3
ORDER BY p.dept_id, exams_today ASC, p.nom;


DELIMITER //
CREATE TRIGGER trg_update_nb_inscrits
AFTER INSERT ON inscriptions
FOR EACH ROW
BEGIN
    UPDATE modules
    SET nb_inscrits = nb_inscrits + 1
    WHERE id = NEW.module_id;
END//

DELIMITER ;


DELIMITER $$

DELIMITER //

CREATE TRIGGER trg_update_nb_etudiants_group
AFTER INSERT ON etudiants
FOR EACH ROW
BEGIN
    UPDATE `groups`
    SET nbr_etudiants = nbr_etudiants + 1
    WHERE id = NEW.group_id;
END//

DELIMITER ;


DELIMITER $$

CREATE TRIGGER trg_salle_conflit
BEFORE INSERT ON exam_salle
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM exam_salle es
        JOIN examens e1 ON e1.id = es.exam_id
        JOIN examens e2 ON e2.id = NEW.exam_id
        WHERE es.salle_id = NEW.salle_id
          AND e1.date_heure = e2.date_heure
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Salle already used at this time';
    END IF;
END$$

DELIMITER ;
