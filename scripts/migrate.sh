#!/bin/bash
# migrate.sh - Initialisation de la base de données

cd ~/cours_en_ligne
mkdir -p data

echo "📦 Initialisation de la base de données..."

# Création du schéma
cat > data/schema.sql << 'EOS'
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS course_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT,
    is_free BOOLEAN DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    category_id INTEGER NOT NULL,
    instructor_name TEXT NOT NULL,
    difficulty_level TEXT,
    duration_weeks INTEGER NOT NULL,
    is_free BOOLEAN DEFAULT 1,
    price DECIMAL(10,2) DEFAULT 0,
    currency TEXT DEFAULT 'XOF',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'published'
);

CREATE TABLE IF NOT EXISTS course_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    module_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrollment_number TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_status TEXT DEFAULT 'pending',
    payment_amount DECIMAL(10,2) DEFAULT 0,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    progress_percentage INTEGER DEFAULT 0,
    certificate_generated BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    certificate_number TEXT UNIQUE NOT NULL,
    issued_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    transaction_id TEXT UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL,
    payment_method TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_courses_slug ON courses(slug);
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_certificates_number ON certificates(certificate_number);
EOS

sqlite3 data/cours.db < data/schema.sql

# Insertion des données de démonstration
cat > data/seed.sql << 'EOS'
INSERT OR IGNORE INTO course_categories (name, slug, description, icon, is_free, price) VALUES
('Développement Web', 'dev-web', 'Apprenez à créer des sites et applications web', '🌐', 0, 25000),
('Data Science', 'data-science', 'Analyse de données et intelligence artificielle', '📊', 0, 35000),
('Marketing Digital', 'marketing-digital', 'Stratégies de marketing en ligne', '📱', 0, 20000),
('Langues', 'langues', 'Apprentissage des langues étrangères', '🗣️', 1, 0),
('Développement Personnel', 'dev-personnel', 'Soft skills et croissance personnelle', '🧠', 1, 0);

INSERT OR IGNORE INTO courses (code, title, slug, description, category_id, instructor_name, difficulty_level, duration_weeks, is_free, price) VALUES
('WEB-001', 'Développement Web Complet', 'dev-web-complet', 'Apprenez HTML, CSS, JavaScript et PHP', 1, 'Dr. Jean Diop', 'débutant', 12, 0, 25000),
('WEB-002', 'React.js - De zéro à expert', 'react-expert', 'Maîtrisez React.js', 1, 'Mme Awa Ndiaye', 'intermédiaire', 8, 0, 30000),
('DS-001', 'Introduction à la Data Science', 'data-science-intro', 'Bases de l''analyse de données avec Python', 2, 'Dr. Cheikh Fall', 'débutant', 10, 0, 35000),
('LANG-001', 'Anglais - Niveau débutant', 'anglais-debutant', 'Apprenez l''anglais à votre rythme', 4, 'M. Pape Gueye', 'débutant', 12, 1, 0),
('DP-001', 'Gestion du Temps', 'gestion-temps', 'Optimisez votre temps et productivité', 5, 'Mme Sophie Diagne', 'débutant', 4, 1, 0);
EOS

sqlite3 data/cours.db < data/seed.sql

echo "✅ Migration terminée !"
echo "📊 $(sqlite3 data/cours.db 'SELECT COUNT(*) FROM courses;') cours disponibles"
