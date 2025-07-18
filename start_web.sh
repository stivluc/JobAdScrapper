#!/bin/bash

echo "🌐 Démarrage de l'interface web Job Ad Scraper"
echo "=============================================="

# Vérification de l'environnement virtuel
if [ ! -d "job_scraper_env" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "Créez l'environnement avec: python3 -m venv job_scraper_env"
    echo "Puis activez-le et installez les dépendances: pip install -r requirements.txt"
    exit 1
fi

# Activation de l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
source job_scraper_env/bin/activate

# Vérification de la configuration
if [ ! -f "config.yaml" ]; then
    echo "❌ Fichier de configuration manquant (config.yaml)"
    exit 1
fi

# Vérification des dépendances
echo "🔍 Vérification des dépendances..."
python3 -c "import flask, yaml, sqlite3, requests, selenium" 2>/dev/null || {
    echo "❌ Dépendances manquantes. Installation..."
    pip install -r requirements.txt
}

# Vérification de ChromeDriver
echo "🔍 Vérification de ChromeDriver..."
if ! command -v chromedriver &> /dev/null; then
    echo "⚠️ ChromeDriver non trouvé. Installation recommandée:"
    echo "   brew install chromedriver"
    echo ""
    echo "Le scraper fonctionnera mais sans navigation automatique."
    echo ""
fi

# Création des dossiers nécessaires
mkdir -p templates static results

echo "✅ Environnement prêt"
echo ""
echo "🌐 Démarrage du serveur web..."
echo "📱 Interface disponible sur: http://localhost:8080"
echo "🔧 Configuration: http://localhost:8080/config"
echo "💼 Offres: http://localhost:8080/jobs"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

# Lancement de l'application Flask
python3 app.py