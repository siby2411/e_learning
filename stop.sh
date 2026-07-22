#!/bin/bash
# stop.sh - Arrêt de la plateforme

echo "🛑 Arrêt de la plateforme E-Learning..."
pkill -f "gunicorn.*app:app" 2>/dev/null && echo "✅ Service arrêté" || echo "ℹ️  Aucun processus trouvé"
