#!/bin/bash
# Script d'activation et de lancement du scraper d'emploi

echo "🎯 Démarrage du scraper d'emploi"
echo "================================"

# Vérification que l'environnement virtuel existe
if [ ! -d "job_scraper_env" ]; then
    echo "❌ Environnement virtuel non trouvé. Veuillez d'abord exécuter:"
    echo "   python3 -m venv job_scraper_env"
    echo "   source job_scraper_env/bin/activate"
    echo "   pip install -r requirements.txt"
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

echo "✅ Environnement prêt"
echo ""
echo "Options disponibles:"
echo "1. 🚀 Lancer le scraper d'emploi: python3 main.py"
echo "2. ⚙️ Éditer la configuration: nano config.yaml"
echo "3. 📊 Voir les résultats précédents: ls -la results/"
echo "4. 🧪 Tester la configuration: python3 -c \"import yaml; print('✅ Configuration valide')\""
echo ""
echo "📝 Personnalisez config.yaml avec vos critères de recherche"
echo "🎯 Recherche: Suisse romande + Lille + Télétravail"
echo ""

# Lancement interactif
read -p "Que souhaitez-vous faire ? (1-4/q pour quitter): " choice

case $choice in
    1)
        echo "🚀 Lancement du scraper d'emploi..."
        python3 main.py
        ;;
    2)
        echo "⚙️ Ouverture de la configuration..."
        nano config.yaml
        ;;
    3)
        echo "📊 Résultats précédents:"
        ls -la results/ 2>/dev/null || echo "Aucun résultat trouvé"
        ;;
    4)
        echo "🧪 Test de la configuration..."
        python3 -c "import yaml; config = yaml.safe_load(open('config.yaml', 'r')); print('✅ Configuration valide'); print(f'📍 {len(config[\"search_criteria\"][\"locations\"])} localisations configurées')"
        ;;
    q|Q)
        echo "👋 Au revoir !"
        ;;
    *)
        echo "❌ Option invalide"
        ;;
esac