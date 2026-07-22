#!/bin/bash
# run.sh - Lancement de la plateforme E-Learning

cd ~/cours_en_ligne

echo "📚 E-Learning Sénégal - Plateforme de formation en ligne"

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier la base de données
if [ ! -f data/cours.db ]; then
    echo "📦 Initialisation de la base de données..."
    if [ -f scripts/migrate.sh ]; then
        bash scripts/migrate.sh
    else
        echo "⚠️  Script de migration manquant. Création manuelle..."
        sqlite3 data/cours.db "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY);"
    fi
fi

# Création des dossiers nécessaires
mkdir -p logs static/certificates

# Arrêt des anciens processus
pkill -f "gunicorn.*app:app" 2>/dev/null || true

echo "▶️ Démarrage du serveur sur http://localhost:5000"
gunicorn -w 2 -b 127.0.0.1:5000 app:app \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon

# Vérification
sleep 2
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo ""
    echo "✅ Application démarrée avec succès !"
    echo ""
    echo "   🌐 Interface: http://localhost:5000"
    echo "   📡 API: http://localhost:5000/api/courses"
    echo ""
    echo "📋 Pour voir les logs: tail -f logs/access.log"
    echo "🛑 Pour arrêter: pkill -f 'gunicorn.*app:app'"
    echo "🔄 Pour redémarrer: bash run.sh"
else
    echo "❌ Erreur au démarrage. Vérifiez les logs:"
    echo "   tail -f logs/error.log"
fi
