#!/bin/bash
# ================================================================
# elearning.sh - Lancement de la plateforme E-Learning Sénégal
# Usage : ./elearning.sh   (depuis n'importe quel répertoire)
# Auteur : [Votre nom]
# Version : 1.0
# ================================================================

set -e  # Arrêt immédiat en cas d'erreur

# ---- Détection automatique du répertoire du projet ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "❌ Erreur : impossible de se positionner dans le répertoire du projet."; exit 1; }

# ---- Configuration ----
PORT=5000
WORKERS=2

# ---- Fonctions ----
die() {
    echo "❌ Erreur : $1"
    exit 1
}

info() {
    echo "ℹ️ $1"
}

success() {
    echo "✅ $1"
}

# ---- Vérifications initiales ----
if [ ! -d "venv" ]; then
    die "L'environnement virtuel n'existe pas. Exécutez d'abord 'python3 -m venv venv' et installez les dépendances."
fi

if [ ! -f "data/cours.db" ]; then
    info "Base de données manquante. Initialisation en cours..."
    if [ -f "scripts/migrate.sh" ]; then
        bash scripts/migrate.sh
    else
        die "Le script de migration est introuvable."
    fi
fi

# ---- Nettoyage des anciens processus ----
info "Nettoyage des anciens processus Gunicorn..."
pkill -f "gunicorn.*app:app" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# Libération du port si occupé
if command -v fuser >/dev/null 2>&1; then
    fuser -k $PORT/tcp 2>/dev/null || true
fi

# ---- Activation de l'environnement virtuel ----
source venv/bin/activate || die "Impossible d'activer l'environnement virtuel"

# ---- Lancement de l'application ----
info "Démarrage de Gunicorn sur le port $PORT avec $WORKERS workers..."
mkdir -p logs

gunicorn -w $WORKERS -b 127.0.0.1:$PORT app:app \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon

# Attente du démarrage
sleep 2

if pgrep -f "gunicorn.*app:app" > /dev/null; then
    success "Application démarrée avec succès !"
    echo ""
    echo "   🌐 Interface    : http://localhost:$PORT"
    echo "   📡 API         : http://localhost:$PORT/api/courses"
    echo "   🛠️ Administration : http://localhost:$PORT/admin"
    echo "   📊 Dashboard   : http://localhost:$PORT/dashboard"
    echo ""
    echo "📋 Pour voir les logs : tail -f logs/access.log"
    echo "🛑 Pour arrêter        : pkill -f 'gunicorn.*app:app'"
    echo "🔄 Pour redémarrer     : ./elearning.sh"
else
    die "Le serveur n'a pas démarré. Vérifiez les logs : tail -f logs/error.log"
fi
