-- ============================================================
-- Données de démonstration - Cours en Ligne
-- ============================================================

-- ===== Catégories =====
INSERT OR IGNORE INTO course_categories (name, slug, description, icon, is_free, price) VALUES
('Développement Web', 'dev-web', 'Apprenez à créer des sites et applications web', '🌐', 0, 25000),
('Data Science', 'data-science', 'Analyse de données et intelligence artificielle', '📊', 0, 35000),
('Marketing Digital', 'marketing-digital', 'Stratégies de marketing en ligne', '📱', 0, 20000),
('Design Graphique', 'design-graphique', 'Création visuelle et design UI/UX', '🎨', 0, 20000),
('Langues', 'langues', 'Apprentissage des langues étrangères', '🗣️', 1, 0),
('Développement Personnel', 'dev-personnel', 'Soft skills et croissance personnelle', '🧠', 1, 0);

-- ===== Cours =====
INSERT OR IGNORE INTO courses (code, title, slug, description, category_id, instructor_name, difficulty_level, duration_weeks, total_hours, is_free, price, status) VALUES
('WEB-001', 'Développement Web Complet', 'dev-web-complet', 'Apprenez HTML, CSS, JavaScript et PHP de zéro', 
    (SELECT id FROM course_categories WHERE slug='dev-web'), 'Dr. Jean Diop', 'débutant', 12, 48, 0, 25000, 'published'),

('WEB-002', 'React.js - De zéro à expert', 'react-expert', 'Maîtrisez React.js et le développement d''applications modernes',
    (SELECT id FROM course_categories WHERE slug='dev-web'), 'Mme Awa Ndiaye', 'intermédiaire', 8, 32, 0, 30000, 'published'),

('DS-001', 'Introduction à la Data Science', 'data-science-intro', 'Découvrez les bases de l''analyse de données avec Python',
    (SELECT id FROM course_categories WHERE slug='data-science'), 'Dr. Cheikh Fall', 'débutant', 10, 40, 0, 35000, 'published'),

('MD-001', 'Marketing Digital - Stratégie complète', 'marketing-digital-strategie', 'Maîtrisez les outils du marketing digital',
    (SELECT id FROM course_categories WHERE slug='marketing-digital'), 'M. Oumar Sow', 'intermédiaire', 8, 24, 0, 20000, 'published'),

('DG-001', 'Design UI/UX - Création d''interfaces', 'design-ux-ui', 'Apprenez à créer des interfaces utilisateur efficaces',
    (SELECT id FROM course_categories WHERE slug='design-graphique'), 'Mme Fatou Diouf', 'débutant', 6, 20, 0, 20000, 'published'),

('LANG-001', 'Anglais - Niveau débutant', 'anglais-debutant', 'Apprenez l''anglais à votre rythme',
    (SELECT id FROM course_categories WHERE slug='langues'), 'M. Pape Gueye', 'débutant', 12, 36, 1, 0, 'published'),

('DP-001', 'Gestion du Temps et Productivité', 'gestion-temps-productivite', 'Optimisez votre temps et augmentez votre productivité',
    (SELECT id FROM course_categories WHERE slug='dev-personnel'), 'Mme Sophie Diagne', 'débutant', 4, 12, 1, 0, 'published');

-- ===== Modules pour "Développement Web Complet" =====
INSERT OR IGNORE INTO course_modules (course_id, module_number, title, description, duration_minutes, is_free_preview) VALUES
((SELECT id FROM courses WHERE slug='dev-web-complet'), 1, 'Introduction au Développement Web', 'Comprendre comment fonctionne le web', 30, 1),
((SELECT id FROM courses WHERE slug='dev-web-complet'), 2, 'HTML - Structure du contenu', 'Maîtrisez les bases de HTML5', 45, 0),
((SELECT id FROM courses WHERE slug='dev-web-complet'), 3, 'CSS - Mise en forme et design', 'Créez des pages web modernes avec CSS3', 60, 0),
((SELECT id FROM courses WHERE slug='dev-web-complet'), 4, 'JavaScript - Interactivité', 'Ajoutez des fonctionnalités dynamiques', 90, 0),
((SELECT id FROM courses WHERE slug='dev-web-complet'), 5, 'PHP - Backend', 'Développez la logique serveur avec PHP', 120, 0),
((SELECT id FROM courses WHERE slug='dev-web-complet'), 6, 'Base de données MySQL', 'Gérez les données avec MySQL', 75, 0);
