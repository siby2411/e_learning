-- ============================================================
-- Système d'Inscription aux Cours en Ligne - Schéma
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ===== Utilisateurs =====
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    profession TEXT,
    education_level TEXT CHECK(education_level IN ('bac', 'bac+2', 'bac+3', 'bac+5', 'doctorat', 'autre')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'deleted'))
);

CREATE INDEX idx_users_email ON users(email);

-- ===== Catégories de Cours =====
CREATE TABLE IF NOT EXISTS course_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT,
    parent_id INTEGER,
    is_free BOOLEAN DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0,
    currency TEXT DEFAULT 'XOF',
    FOREIGN KEY (parent_id) REFERENCES course_categories(id)
);

-- ===== Cours =====
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    category_id INTEGER NOT NULL,
    instructor_name TEXT NOT NULL,
    instructor_bio TEXT,
    difficulty_level TEXT CHECK(difficulty_level IN ('débutant', 'intermédiaire', 'avancé', 'expert')),
    duration_weeks INTEGER NOT NULL,
    total_hours INTEGER,
    video_count INTEGER,
    is_free BOOLEAN DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0,
    currency TEXT DEFAULT 'XOF',
    thumbnail_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'published' CHECK(status IN ('draft', 'published', 'archived')),
    FOREIGN KEY (category_id) REFERENCES course_categories(id)
);

CREATE INDEX idx_courses_category ON courses(category_id);
CREATE INDEX idx_courses_slug ON courses(slug);
CREATE INDEX idx_courses_status ON courses(status);

-- ===== Leçons / Modules =====
CREATE TABLE IF NOT EXISTS course_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    module_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    video_url TEXT,
    duration_minutes INTEGER,
    is_free_preview BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE INDEX idx_modules_course ON course_modules(course_id);

-- ===== Inscriptions =====
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrollment_number TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'active', 'completed', 'cancelled', 'expired')),
    payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    payment_amount DECIMAL(10,2) DEFAULT 0,
    payment_currency TEXT DEFAULT 'XOF',
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    completion_date DATETIME,
    progress_percentage INTEGER DEFAULT 0,
    certificate_generated BOOLEAN DEFAULT 0,
    certificate_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE(user_id, course_id)
);

CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);

-- ===== Progression =====
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT 0,
    last_watched_at DATETIME,
    watch_time_seconds INTEGER DEFAULT 0,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE,
    UNIQUE(enrollment_id, module_id)
);

-- ===== Certificats =====
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    certificate_number TEXT UNIQUE NOT NULL,
    file_path TEXT,
    qr_code TEXT,
    issued_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME,
    verification_count INTEGER DEFAULT 0,
    last_verified_at DATETIME,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);

CREATE INDEX idx_certificates_number ON certificates(certificate_number);

-- ===== Paiements =====
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    transaction_id TEXT UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('mobile_money', 'bank_transfer', 'card', 'cash')),
    payment_reference TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed', 'refunded')),
    metadata TEXT,
    processed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
);

-- ===== Statistiques =====
CREATE TABLE IF NOT EXISTS course_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    total_enrollments INTEGER DEFAULT 0,
    active_enrollments INTEGER DEFAULT 0,
    completions INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),
    total_revenue DECIMAL(12,2) DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE(course_id)
);

-- ===== Audits =====
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ===== Sessions =====
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ===== Triggers =====
CREATE TRIGGER update_courses_updated_at 
AFTER UPDATE ON courses
BEGIN
    UPDATE courses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_enrollments_updated_at 
AFTER UPDATE ON enrollments
BEGIN
    UPDATE enrollments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_stats_on_enrollment
AFTER INSERT ON enrollments
BEGIN
    INSERT OR REPLACE INTO course_stats (course_id, total_enrollments, active_enrollments, updated_at)
    SELECT 
        NEW.course_id,
        (SELECT COUNT(*) FROM enrollments WHERE course_id = NEW.course_id),
        (SELECT COUNT(*) FROM enrollments WHERE course_id = NEW.course_id AND status = 'active'),
        CURRENT_TIMESTAMP
    WHERE EXISTS (SELECT 1 FROM courses WHERE id = NEW.course_id);
END;
