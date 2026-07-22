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
