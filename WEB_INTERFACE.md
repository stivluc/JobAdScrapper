# 🌐 Interface Web - Job Ad Scraper

## 📋 Présentation

L'interface web moderne du Job Ad Scraper permet de :
- **Lancer le scraping** d'un simple clic
- **Visualiser la progression** en temps réel
- **Consulter les résultats** avec tri et filtrage
- **Modifier la configuration** avec un éditeur intégré
- **Consulter l'historique** des sessions

## 🚀 Démarrage rapide

### 1. Installation des dépendances
```bash
source job_scraper_env/bin/activate
pip install -r requirements.txt
```

### 2. Lancement de l'interface
```bash
# Sur macOS/Linux
./start_web.sh

# Sur Windows
start_web.bat

# Ou directement
python3 app.py
```

### 3. Accès à l'interface
- **Interface principale** : http://localhost:5000
- **Configuration** : http://localhost:5000/config
- **Offres d'emploi** : http://localhost:5000/jobs
- **Historique** : http://localhost:5000/sessions

## 📊 Fonctionnalités

### 🏠 Tableau de bord
- **Statistiques en temps réel** : Nombre d'offres, score moyen, entreprises
- **Contrôle du scraping** : Démarrage, arrêt, progression
- **Offres récentes** : Top 5 des meilleures offres
- **Aperçu des sessions** : Historique des dernières exécutions

### 💼 Gestion des offres
- **Liste paginée** : Affichage optimisé par cartes
- **Filtrage avancé** : Par score de compatibilité, date, entreprise
- **Tri personnalisé** : Score, date, entreprise, localisation
- **Liens directs** : Accès aux offres originales en un clic

### ⚙️ Configuration
- **Éditeur YAML intégré** : Modification directe de config.yaml
- **Validation en temps réel** : Vérification de la syntaxe
- **Prévisualisation** : Affichage des paramètres actuels
- **Templates** : Configurations pré-définies

### 📈 Historique et statistiques
- **Sessions complètes** : Détails de chaque exécution
- **Graphiques** : Évolution des performances
- **Analyse des erreurs** : Diagnostic et solutions
- **Export des données** : JSON, CSV, Excel

## 🗄️ Base de données SQLite

### Structure des données
```sql
-- Table des offres d'emploi
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary TEXT,
    description TEXT,
    url TEXT UNIQUE,
    source TEXT,
    match_score REAL,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Table des sessions de scraping
CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    total_jobs INTEGER,
    unique_jobs INTEGER,
    status TEXT,
    error_message TEXT,
    config_snapshot TEXT,
    created_at TIMESTAMP
);
```

### Avantages de SQLite
- **Persistance** : Les données survivent aux redémarrages
- **Performance** : Requêtes rapides avec index
- **Déduplication** : Contraintes UNIQUE sur les URLs
- **Historique** : Suivi complet des sessions
- **Portabilité** : Fichier unique, facile à sauvegarder

## 🔧 Configuration technique

### Port et accès
- **Port par défaut** : 5000
- **Interface** : 0.0.0.0 (accessible depuis le réseau local)
- **Mode debug** : Activé en développement

### Sécurité
- **Accès local** : Interface non exposée publiquement
- **Validation** : Contrôles sur les entrées utilisateur
- **Timeout** : Limitation des sessions longues

### Performance
- **Pagination** : Affichage par lots (20 offres/page)
- **Cache** : Mise en cache des statistiques
- **Optimisation** : Index sur les colonnes fréquemment utilisées

## 🎛️ Utilisation détaillée

### Démarrage du scraping
1. **Vérifier la configuration** : Page Configuration
2. **Cliquer sur "Démarrer"** : Bouton sur le tableau de bord
3. **Suivre la progression** : Barre de progression temps réel
4. **Consulter les résultats** : Redirection automatique

### Modification de la configuration
1. **Aller à la page Configuration**
2. **Modifier le YAML** : Éditeur avec coloration syntaxique
3. **Valider** : Bouton de validation intégré
4. **Sauvegarder** : Prise en compte immédiate

### Consultation des résultats
1. **Page des offres** : Liste complète avec filtres
2. **Tri personnalisé** : Par score, date, entreprise
3. **Filtrage** : Score minimum, mots-clés
4. **Export** : Boutons d'export en différents formats

### Analyse des performances
1. **Page Historique** : Toutes les sessions
2. **Graphiques** : Évolution des performances
3. **Détails** : Clic sur une session pour plus d'infos
4. **Diagnostic** : Messages d'erreur détaillés

## 🔍 API REST

### Endpoints disponibles
```
GET  /                    # Tableau de bord
GET  /jobs               # Liste des offres
GET  /config             # Configuration
POST /config/save        # Sauvegarde config
GET  /sessions           # Historique
POST /start_scraping     # Démarrage scraping
GET  /scraping_status    # Statut temps réel
GET  /api/jobs           # API JSON des offres
```

### Exemple d'utilisation API
```javascript
// Récupération des offres
fetch('/api/jobs?min_score=70&page=1')
    .then(response => response.json())
    .then(data => console.log(data.jobs));

// Démarrage du scraping
fetch('/start_scraping', { method: 'POST' })
    .then(response => response.json())
    .then(data => console.log(data.message));
```

## 🛠️ Personnalisation

### Modification des templates
Les templates HTML sont dans `templates/` :
- `base.html` : Template principal
- `index.html` : Tableau de bord
- `jobs.html` : Liste des offres
- `config.html` : Configuration
- `sessions.html` : Historique

### Ajout de fonctionnalités
1. **Nouvelles routes** : Ajouter dans `app.py`
2. **Nouveaux templates** : Créer dans `templates/`
3. **Styles CSS** : Modifier dans les templates
4. **JavaScript** : Ajouter dans les templates

## 🚨 Dépannage

### Problèmes courants

#### Port 5000 occupé
```bash
# Changer le port dans app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

#### Erreur de base de données
```bash
# Supprimer la base et redémarrer
rm jobs.db
python3 app.py
```

#### Templates non trouvés
```bash
# Vérifier la structure des dossiers
ls -la templates/
```

#### Scraping ne démarre pas
1. Vérifier ChromeDriver
2. Valider la configuration
3. Consulter les logs dans le terminal

## 🎯 Conseils d'utilisation

### Optimisation
1. **Fermez les onglets inutiles** : Économise la mémoire
2. **Utilisez les filtres** : Améliore les performances
3. **Nettoyez régulièrement** : Supprimez les anciennes sessions
4. **Monitoring** : Surveillez l'utilisation CPU/RAM

### Bonnes pratiques
1. **Sauvegardez jobs.db** : Fichier unique contenant toutes les données
2. **Testez la configuration** : Avant de lancer un scraping long
3. **Consultez l'historique** : Pour optimiser les paramètres
4. **Utilisez les graphiques** : Pour identifier les tendances

---

**🌐 Interface web prête ! Lancez `./start_web.sh` et accédez à http://localhost:5000**