#!/bin/bash
cd ~/cours_en_ligne

echo "🔧 Mise à jour de templates/admin.html pour intégrer online_link..."

# 1. Ajouter le champ dans le formulaire des sessions (s'il n'existe pas déjà)
if ! grep -q 'id="f-online_link"' templates/admin.html; then
    sed -i '/<div class="form-group"><label>Lieu<\/label>/a \    <div class="form-group"><label>Lien Zoom<\/label><input type="text" id="f-online_link" placeholder="https://zoom.us/j/..."><\/div>' templates/admin.html
    echo "✅ Champ online_link ajouté au formulaire."
else
    echo "ℹ️ Champ online_link déjà présent."
fi

# 2. Modifier la fonction saveEntity pour inclure online_link
# On cherche la ligne où on construit l'objet data et on ajoute online_link
# On utilise sed pour insérer la ligne après la déclaration de data
if ! grep -q 'data.online_link' templates/admin.html; then
    sed -i '/const data = {}/a \    const online_link = document.getElementById('\''f-online_link'\'')?.value || '\'\'';\n    data.online_link = online_link;' templates/admin.html
    echo "✅ online_link intégré dans la fonction saveEntity."
else
    echo "ℹ️ online_link déjà intégré dans saveEntity."
fi

echo "✅ Mise à jour terminée."
echo "🔄 Redémarrez l'application pour appliquer les changements : ./elearning.sh"
