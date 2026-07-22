-- ============================================================
-- Module Suivi Académique - Tables supplémentaires
-- ============================================================

-- ===== EXAMENS =====
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    exam_type TEXT CHECK(exam_type IN ('qcm', 'pratique', 'theorique', 'mixte')),
    coefficient INTEGER DEFAULT 1,
    max_score INTEGER DEFAULT 20,
    passing_score INTEGER DEFAULT 10,
    scheduled_date DATETIME,
    duration_minutes INTEGER,
    is_final BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'ongoing', 'completed', 'cancelled')),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX idx_exams_course ON exams(course_id);
CREATE INDEX idx_exams_status ON exams(status);

-- ===== NOTES =====
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    score DECIMAL(5,2),
    is_passed BOOLEAN DEFAULT 0,
    graded_by INTEGER,
    graded_at DATETIME,
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (graded_by) REFERENCES users(id),
    UNIQUE(enrollment_id, exam_id)
);

CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);
CREATE INDEX idx_grades_exam ON grades(exam_id);

-- ===== SUIVI PAIEMENTS =====
CREATE TABLE IF NOT EXISTS payment_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    due_date DATETIME NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'cancelled')),
    paid_at DATETIME,
    payment_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);

CREATE INDEX idx_payment_schedules_enrollment ON payment_schedules(enrollment_id);
CREATE INDEX idx_payment_schedules_status ON payment_schedules(status);

-- ===== SUIVI PROGRESSION =====
ALTER TABLE enrollments ADD COLUMN last_activity DATETIME;
ALTER TABLE enrollments ADD COLUMN total_score DECIMAL(5,2) DEFAULT 0;

-- ===== VUES POUR RAPPORTS =====

-- Vue : Relevé de notes par étudiant
CREATE VIEW IF NOT EXISTS v_student_grades AS
SELECT 
    e.id as enrollment_id,
    u.id as user_id,
    u.first_name,
    u.last_name,
    u.email,
    c.id as course_id,
    c.title as course_title,
    c.code as course_code,
    ex.id as exam_id,
    ex.title as exam_title,
    ex.coefficient,
    ex.max_score,
    g.score,
    g.is_passed,
    ROUND(AVG(g.score) OVER (PARTITION BY e.id), 2) as average_score,
    ROUND(SUM(g.score * ex.coefficient) OVER (PARTITION BY e.id) / SUM(ex.coefficient) OVER (PARTITION BY e.id), 2) as weighted_average
FROM enrollments e
JOIN users u ON e.user_id = u.id
JOIN courses c ON e.course_id = c.id
LEFT JOIN exams ex ON ex.course_id = c.id
LEFT JOIN grades g ON g.enrollment_id = e.id AND g.exam_id = ex.id
WHERE e.status IN ('active', 'completed');

-- Vue : État financier par étudiant
CREATE VIEW IF NOT EXISTS v_student_financial AS
SELECT 
    e.id as enrollment_id,
    u.id as user_id,
    u.first_name,
    u.last_name,
    c.id as course_id,
    c.title as course_title,
    c.price as total_fees,
    COALESCE(SUM(p.amount), 0) as paid_amount,
    c.price - COALESCE(SUM(p.amount), 0) as balance_due,
    COUNT(DISTINCT ps.id) as total_installments,
    COUNT(DISTINCT CASE WHEN ps.status = 'paid' THEN ps.id END) as paid_installments,
    MAX(ps.due_date) as next_due_date,
    CASE 
        WHEN COALESCE(SUM(p.amount), 0) >= c.price THEN 'payé'
        WHEN COALESCE(SUM(p.amount), 0) > 0 AND COALESCE(SUM(p.amount), 0) < c.price THEN 'partiel'
        ELSE 'non payé'
    END as payment_status
FROM enrollments e
JOIN users u ON e.user_id = u.id
JOIN courses c ON e.course_id = c.id
LEFT JOIN payments p ON p.enrollment_id = e.id AND p.status = 'completed'
LEFT JOIN payment_schedules ps ON ps.enrollment_id = e.id
WHERE e.status IN ('active', 'completed')
GROUP BY e.id, u.id, c.id;

-- Vue : Résultat définitif des inscrits
CREATE VIEW IF NOT EXISTS v_final_results AS
SELECT 
    e.id as enrollment_id,
    u.id as user_id,
    u.first_name,
    u.last_name,
    u.email,
    c.id as course_id,
    c.title as course_title,
    c.code as course_code,
    e.status,
    e.completion_date,
    e.progress_percentage,
    sg.weighted_average as final_grade,
    CASE 
        WHEN sg.weighted_average >= 10 THEN 'validé'
        WHEN sg.weighted_average IS NOT NULL AND sg.weighted_average < 10 THEN 'échec'
        WHEN e.status = 'completed' AND sg.weighted_average IS NULL THEN 'en attente'
        ELSE 'en cours'
    END as final_result,
    COUNT(DISTINCT ex.id) as total_exams,
    COUNT(DISTINCT CASE WHEN g.is_passed = 1 THEN g.exam_id END) as passed_exams,
    sf.payment_status,
    sf.total_fees,
    sf.paid_amount,
    sf.balance_due
FROM enrollments e
JOIN users u ON e.user_id = u.id
JOIN courses c ON e.course_id = c.id
LEFT JOIN v_student_grades sg ON sg.enrollment_id = e.id
LEFT JOIN exams ex ON ex.course_id = c.id
LEFT JOIN grades g ON g.enrollment_id = e.id
LEFT JOIN v_student_financial sf ON sf.enrollment_id = e.id
WHERE e.status IN ('active', 'completed')
GROUP BY e.id, u.id, c.id;

