#!/bin/bash
cd ~/cours_en_ligne

cat > templates/admin.html << 'EOT'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛠️ Administration</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <style>
        .admin-container { display: flex; }
        .admin-sidebar { width: 200px; background: #f0f2f5; padding: 20px; border-right: 1px solid #dee2e6; }
        .admin-sidebar a { display: block; padding: 10px; margin: 5px 0; background: #fff; border-radius: 6px; text-decoration: none; color: #333; }
        .admin-sidebar a:hover { background: #e9ecef; }
        .admin-content { flex: 1; padding: 20px; overflow-x: auto; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .admin-table th { background: #1a237e; color: #fff; padding: 8px; }
        .admin-table td { padding: 6px; border-bottom: 1px solid #dee2e6; }
        .admin-table tr:nth-child(even) { background: #f8f9fa; }
        .btn-sm { padding: 4px 10px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-edit { background: #ffc107; color: #333; }
        .btn-del { background: #dc3545; color: #fff; }
        .btn-add { background: #28a745; color: #fff; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; margin-bottom: 10px; }
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:none; justify-content:center; align-items:center; z-index:999; }
        .modal-content { background:#fff; padding:20px; border-radius:8px; width:90%; max-width:600px; max-height:90vh; overflow-y:auto; }
        .modal-content .close { float:right; cursor:pointer; font-size:24px; }
        .form-group { margin-bottom:10px; }
        .form-group label { display:block; font-weight:600; }
        .form-group input, .form-group select, .form-group textarea { width:100%; padding:6px; border:1px solid #ccc; border-radius:4px; }
        .tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
        .tabs button { padding:8px 16px; background:#e9ecef; border:none; border-radius:6px; cursor:pointer; }
        .tabs button.active { background:#1a237e; color:#fff; }
        .section { display: none; }
        .section.active { display: block; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🛠️ Panneau d'administration</h1>
        <div class="header-actions">
            <a href="/" style="color:#fff;">← Accueil</a>
        </div>
    </header>
    <div class="admin-container">
        <div class="admin-sidebar">
            <h3>Gestion</h3>
            <a href="#" onclick="showSection('users')">👤 Utilisateurs</a>
            <a href="#" onclick="showSection('courses')">📚 Cours</a>
            <a href="#" onclick="showSection('chapters')">📖 Chapitres</a>
            <a href="#" onclick="showSection('sessions')">🕐 Sessions</a>
            <a href="#" onclick="showSection('enrollments')">📋 Inscriptions</a>
            <a href="#" onclick="showSection('categories')">🏷️ Catégories</a>
        </div>
        <div class="admin-content">
            <div id="section-users" class="section active">
                <h2>Utilisateurs</h2>
                <button class="btn-add" onclick="showModal('userModal', null)">+ Ajouter</button>
                <div id="users-list"></div>
            </div>
            <div id="section-courses" class="section">
                <h2>Cours</h2>
                <button class="btn-add" onclick="showModal('courseModal', null)">+ Ajouter</button>
                <div id="courses-list"></div>
            </div>
            <div id="section-chapters" class="section">
                <h2>Chapitres</h2>
                <button class="btn-add" onclick="showModal('chapterModal', null)">+ Ajouter</button>
                <div id="chapters-list"></div>
            </div>
            <div id="section-sessions" class="section">
                <h2>Sessions</h2>
                <button class="btn-add" onclick="showModal('sessionModal', null)">+ Ajouter</button>
                <div id="sessions-list"></div>
            </div>
            <div id="section-enrollments" class="section">
                <h2>Inscriptions</h2>
                <button class="btn-add" onclick="showModal('enrollmentModal', null)">+ Ajouter</button>
                <div id="enrollments-list"></div>
            </div>
            <div id="section-categories" class="section">
                <h2>Catégories</h2>
                <button class="btn-add" onclick="showModal('categoryModal', null)">+ Ajouter</button>
                <div id="categories-list"></div>
            </div>
        </div>
    </div>
</div>

<footer><p>&copy; 2026 E-Learning Sénégal - Admin</p></footer>

<script>
// ========== GLOBAL VARIABLES ==========
let currentEditId = null;
let currentEntity = null;

// ========== SECTION NAVIGATION ==========
function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${id}`).classList.add('active');
    loadData(id);
}

// ========== LOAD DATA ==========
function loadData(section) {
    switch(section) {
        case 'users': fetchUsers(); break;
        case 'courses': fetchCourses(); break;
        case 'chapters': fetchChapters(); break;
        case 'sessions': fetchSessions(); break;
        case 'enrollments': fetchEnrollments(); break;
        case 'categories': fetchCategories(); break;
    }
}

// ========== FETCH FUNCTIONS ==========
async function fetchUsers() {
    const resp = await fetch('/api/admin/users');
    const data = await resp.json();
    renderTable('users-list', data, ['id','email','first_name','last_name','status','role'], 'user');
}
async function fetchCourses() {
    const resp = await fetch('/api/admin/courses');
    const data = await resp.json();
    renderTable('courses-list', data, ['id','title','category_name','instructor_name','price','status'], 'course');
}
async function fetchChapters() {
    const resp = await fetch('/api/admin/chapters');
    const data = await resp.json();
    renderTable('chapters-list', data, ['id','course_id','title','order_index','description'], 'chapter');
}
async function fetchSessions() {
    const resp = await fetch('/api/admin/sessions');
    const data = await resp.json();
    renderTable('sessions-list', data, ['id','chapter_id','title','day_of_week','start_time','end_time','location','online_link'], 'session');
}
async function fetchEnrollments() {
    const resp = await fetch('/api/admin/enrollments');
    const data = await resp.json();
    renderTable('enrollments-list', data, ['id','user_id','course_id','status','payment_status','progress_percentage'], 'enrollment');
}
async function fetchCategories() {
    const resp = await fetch('/api/admin/categories');
    const data = await resp.json();
    renderTable('categories-list', data, ['id','name','slug','description','icon'], 'category');
}

// ========== RENDER TABLE ==========
function renderTable(containerId, data, fields, entity) {
    const container = document.getElementById(containerId);
    if (!data || data.length === 0) {
        container.innerHTML = '<p>Aucune donnée.</p>';
        return;
    }
    let html = `<table class="admin-table"><thead><tr>`;
    fields.forEach(f => html += `<th>${f}</th>`);
    html += `<th>Actions</th></tr></thead><tbody>`;
    data.forEach(row => {
        html += `<tr>`;
        fields.forEach(f => {
            let val = row[f];
            if (val === null || val === undefined) val = '';
            html += `<td>${val}</td>`;
        });
        html += `<td>
            <button class="btn-sm btn-edit" onclick="editEntity('${entity}', ${row.id})">✏️</button>
            <button class="btn-sm btn-del" onclick="deleteEntity('${entity}', ${row.id})">🗑️</button>
        </td></tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

// ========== EDIT / DELETE ==========
function editEntity(entity, id) {
    showModal(`${entity}Modal`, id);
}
async function deleteEntity(entity, id) {
    if (!confirm(`Supprimer définitivement cet élément ?`)) return;
    await fetch(`/api/admin/${entity}s/${id}`, { method: 'DELETE' });
    loadData(document.querySelector('.section.active').id.replace('section-',''));
}

// ========== SHOW MODAL ==========
function showModal(modalId, id) {
    currentEditId = id;
    // Créer la modale dynamiquement
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.id = 'dynamicModal';

    let title = id ? 'Modifier' : 'Ajouter';
    let fieldsHtml = '';

    if (modalId === 'userModal') {
        title += ' utilisateur';
        fieldsHtml = `
            <div class="form-group"><label>Email</label><input type="email" id="f-email" required></div>
            <div class="form-group"><label>Mot de passe</label><input type="password" id="f-password"></div>
            <div class="form-group"><label>Prénom</label><input type="text" id="f-first_name"></div>
            <div class="form-group"><label>Nom</label><input type="text" id="f-last_name"></div>
            <div class="form-group"><label>Téléphone</label><input type="text" id="f-phone"></div>
            <div class="form-group"><label>Statut</label>
                <select id="f-status"><option value="active">Actif</option><option value="suspended">Suspendu</option></select></div>
            <div class="form-group"><label>Rôle</label>
                <select id="f-role"><option value="user">Utilisateur</option><option value="admin">Administrateur</option></select></div>
        `;
    } else if (modalId === 'courseModal') {
        title += ' cours';
        fieldsHtml = `
            <div class="form-group"><label>Titre</label><input type="text" id="f-title" required></div>
            <div class="form-group"><label>Slug</label><input type="text" id="f-slug" required></div>
            <div class="form-group"><label>Description</label><textarea id="f-description"></textarea></div>
            <div class="form-group"><label>Catégorie</label><select id="f-category_id"></select></div>
            <div class="form-group"><label>Instructeur</label><input type="text" id="f-instructor"></div>
            <div class="form-group"><label>Niveau</label>
                <select id="f-difficulty"><option value="débutant">Débutant</option><option value="intermédiaire">Intermédiaire</option><option value="avancé">Avancé</option></select></div>
            <div class="form-group"><label>Durée (semaines)</label><input type="number" id="f-duration" required></div>
            <div class="form-group"><label>Prix</label><input type="number" id="f-price" step="0.01" required></div>
            <div class="form-group"><label>Statut</label>
                <select id="f-status"><option value="published">Publié</option><option value="draft">Brouillon</option><option value="archived">Archivé</option></select></div>
        `;
    } else if (modalId === 'chapterModal') {
        title += ' chapitre';
        fieldsHtml = `
            <div class="form-group"><label>Cours</label><select id="f-course_id"></select></div>
            <div class="form-group"><label>Titre</label><input type="text" id="f-title" required></div>
            <div class="form-group"><label>Description</label><textarea id="f-description"></textarea></div>
            <div class="form-group"><label>Ordre</label><input type="number" id="f-order_index" required></div>
            <div class="form-group"><label>Contenu</label><textarea id="f-content"></textarea></div>
        `;
    } else if (modalId === 'sessionModal') {
        title += ' session';
        fieldsHtml = `
            <div class="form-group"><label>Chapitre</label><select id="f-chapter_id"></select></div>
            <div class="form-group"><label>Titre</label><input type="text" id="f-title"></div>
            <div class="form-group"><label>Jour de la semaine</label>
                <select id="f-day_of_week">
                    <option value="1">Lundi</option><option value="2">Mardi</option><option value="3">Mercredi</option>
                    <option value="4">Jeudi</option><option value="5">Vendredi</option><option value="6">Samedi</option>
                    <option value="7">Dimanche</option>
                </select>
            </div>
            <div class="form-group"><label>Heure début</label><input type="time" id="f-start_time" required></div>
            <div class="form-group"><label>Heure fin</label><input type="time" id="f-end_time" required></div>
            <div class="form-group"><label>Lieu</label><input type="text" id="f-location"></div>
            <div class="form-group"><label>Lien Zoom</label><input type="text" id="f-online_link" placeholder="https://zoom.us/j/..."></div>
            <div class="form-group"><label>Description</label><textarea id="f-description"></textarea></div>
        `;
    } else if (modalId === 'enrollmentModal') {
        title += ' inscription';
        fieldsHtml = `
            <div class="form-group"><label>Utilisateur</label><select id="f-user_id"></select></div>
            <div class="form-group"><label>Cours</label><select id="f-course_id"></select></div>
            <div class="form-group"><label>Statut</label>
                <select id="f-status"><option value="active">Actif</option><option value="pending">En attente</option><option value="completed">Terminé</option></select></div>
            <div class="form-group"><label>Paiement</label>
                <select id="f-payment_status"><option value="paid">Payé</option><option value="pending">En attente</option></select></div>
            <div class="form-group"><label>Progression (%)</label><input type="number" id="f-progress" min="0" max="100"></div>
        `;
    } else if (modalId === 'categoryModal') {
        title += ' catégorie';
        fieldsHtml = `
            <div class="form-group"><label>Nom</label><input type="text" id="f-name" required></div>
            <div class="form-group"><label>Slug</label><input type="text" id="f-slug" required></div>
            <div class="form-group"><label>Description</label><textarea id="f-description"></textarea></div>
            <div class="form-group"><label>Icône</label><input type="text" id="f-icon" placeholder="📚"></div>
        `;
    } else {
        title += ' élément';
        fieldsHtml = `<p>Formulaire pour ${modalId} (à compléter)</p>`;
    }

    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="closeModal('dynamicModal')">&times;</span>
            <h2>${title}</h2>
            <form id="admin-form" onsubmit="saveEntity(event, '${modalId}')">
                ${fieldsHtml}
                <button type="submit" class="btn-add">Enregistrer</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    // Remplir les selects pour les relations
    if (modalId === 'courseModal' || modalId === 'chapterModal' || modalId === 'enrollmentModal') {
        populateSelect('/api/admin/categories', 'f-category_id', 'name');
        populateSelect('/api/admin/courses', 'f-course_id', 'title');
        populateSelect('/api/admin/users', 'f-user_id', 'email');
        populateSelect('/api/admin/chapters', 'f-chapter_id', 'title');
    }

    // Si modification, charger les données
    if (id) {
        const entity = modalId.replace('Modal','');
        fetch(`/api/admin/${entity}s/${id}`)
            .then(r => r.json())
            .then(data => {
                for (let key in data) {
                    const el = document.getElementById(`f-${key}`);
                    if (el) el.value = data[key];
                }
            });
    }
}

// ========== POPULATE SELECT ==========
async function populateSelect(url, selectId, labelKey) {
    const resp = await fetch(url);
    const data = await resp.json();
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">Choisir...</option>';
    data.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = item[labelKey] || item.title || item.email || item.name;
        sel.appendChild(opt);
    });
}

// ========== CLOSE MODAL ==========
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.remove();
}

// ========== SAVE ENTITY ==========
async function saveEntity(event, modalId) {
    event.preventDefault();
    const form = document.getElementById('admin-form');
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => { data[key] = value; });

    // Récupérer online_link explicitement pour les sessions
    const online_link_el = document.getElementById('f-online_link');
    if (online_link_el) data.online_link = online_link_el.value;

    const entity = modalId.replace('Modal','');
    const url = currentEditId ? `/api/admin/${entity}s/${currentEditId}` : `/api/admin/${entity}s`;
    const method = currentEditId ? 'PUT' : 'POST';

    try {
        const resp = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (resp.ok) {
            closeModal('dynamicModal');
            loadData(document.querySelector('.section.active').id.replace('section-',''));
        } else {
            const err = await resp.json();
            alert('Erreur : ' + (err.error || 'inconnue'));
        }
    } catch (e) {
        alert('Erreur réseau');
    }
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', () => {
    loadData('users');
});
</script>
</body>
</html>
EOT

echo "✅ templates/admin.html mis à jour avec les formulaires complets."
echo "🔄 Redémarrez l'application : ./elearning.sh"
