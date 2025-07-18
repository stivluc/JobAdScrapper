@echo off
echo 🌐 Démarrage de l'interface web Job Ad Scraper
echo ==============================================

rem Vérification de l'environnement virtuel
if not exist "job_scraper_env" (
    echo ❌ Environnement virtuel non trouvé
    echo Créez l'environnement avec: python -m venv job_scraper_env
    echo Puis activez-le et installez les dépendances: pip install -r requirements.txt
    pause
    exit /b 1
)

rem Activation de l'environnement virtuel
echo 🔄 Activation de l'environnement virtuel...
call job_scraper_env\Scripts\activate

rem Vérification de la configuration
if not exist "config.yaml" (
    echo ❌ Fichier de configuration manquant (config.yaml)
    pause
    exit /b 1
)

rem Vérification des dépendances
echo 🔍 Vérification des dépendances...
python -c "import flask, yaml, sqlite3, requests, selenium" 2>nul || (
    echo ❌ Dépendances manquantes. Installation...
    pip install -r requirements.txt
)

rem Vérification de ChromeDriver
echo 🔍 Vérification de ChromeDriver...
where chromedriver >nul 2>&1 || (
    echo ⚠️ ChromeDriver non trouvé. Installation recommandée:
    echo    Téléchargez depuis https://chromedriver.chromium.org/
    echo    Ou installez avec: chocolatey install chromedriver
    echo.
    echo Le scraper fonctionnera mais sans navigation automatique.
    echo.
)

rem Création des dossiers nécessaires
if not exist "templates" mkdir templates
if not exist "static" mkdir static
if not exist "results" mkdir results

echo ✅ Environnement prêt
echo.
echo 🌐 Démarrage du serveur web...
echo 📱 Interface disponible sur: http://localhost:8080
echo 🔧 Configuration: http://localhost:8080/config
echo 💼 Offres: http://localhost:8080/jobs
echo.
echo Appuyez sur Ctrl+C pour arrêter le serveur
echo.

rem Lancement de l'application Flask
python app.py

pause