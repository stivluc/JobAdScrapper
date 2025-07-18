# 🎯 Job Ad Scraper - Scraper d'Emploi Intelligent

Un scraper d'emploi puissant avec **interface web** qui utilise **Google Search + Selenium** pour trouver des offres d'emploi **partout sur internet**, optimisé pour les ingénieurs logiciels.

## 🚀 Fonctionnalités

- ✅ **Interface web intuitive** : Contrôlez le scraping depuis votre navigateur
- ✅ **Base de données SQLite** : Stockage persistant et rapide des offres
- ✅ **Recherche Google intelligente** : Trouve les offres sur TOUS les sites d'emploi
- ✅ **Localisations multiples** : Suisse romande, Lille, télétravail
- ✅ **Score de compatibilité** : Calcule automatiquement la pertinence de chaque offre
- ✅ **Multi-sites** : Indeed, LinkedIn, Glassdoor, Welcome to the Jungle, jobs.ch
- ✅ **Déduplication** : Supprime automatiquement les doublons
- ✅ **Suivi temps réel** : Progression du scraping en direct
- ✅ **Historique complet** : Sessions de scraping avec statistiques
- ✅ **Export multiple** : CSV, Excel depuis l'interface web

## 🚀 Installation

### 1. Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### 2. Installation des dépendances

```bash
# Installer les paquets Python requis
pip install -r requirements.txt
```

### 3. Configuration

1. Ouvrez le fichier `config.yaml`
2. Modifiez vos informations personnelles dans la section `user_profile`:
   - Nom et email
   - Compétences (séparées par des virgules)
   - Années d'expérience
   - Niveau d'éducation

3. Configurez vos critères de recherche dans `search_criteria`:
   - Mots-clés pour le poste
   - Localisation préférée
   - Fourchette salariale
   - Type de contrat
   - Télétravail accepté

### 4. Installation de ChromeDriver (requis)

**macOS :**
```bash
brew install chromedriver
```

**Windows :**
- Téléchargez depuis https://chromedriver.chromium.org/
- Ajoutez à votre PATH

### 5. Lancement

#### Interface Web (RECOMMANDÉE)
```bash
# Lancer l'interface web
./start_web.sh       # macOS/Linux
# ou
start_web.bat        # Windows

# Puis ouvrir http://localhost:8080
```

#### Mode Ligne de Commande
```bash
# Lancer directement le scraper
python main.py
```

## 📁 Structure du projet

```
JobAdScrapper/
├── 🌐 Interface Web
│   ├── app.py               # Application Flask
│   ├── templates/           # Templates HTML
│   │   ├── base.html
│   │   ├── index.html       # Tableau de bord
│   │   ├── jobs.html        # Liste des offres
│   │   ├── config.html      # Éditeur de configuration
│   │   └── sessions.html    # Historique
│   └── static/             # Ressources statiques
│
├── 🔧 Scraper Core
│   ├── main.py             # Moteur de scraping
│   └── config.yaml         # Configuration utilisateur
│
├── 🗄️ Base de données
│   ├── jobs.db            # Base SQLite (créée automatiquement)
│   └── SQLITE_GUIDE.md    # Guide d'utilisation SQLite
│
├── 🚀 Scripts de lancement
│   ├── start_web.sh       # Lancement macOS/Linux
│   └── start_web.bat      # Lancement Windows
│
└── 📋 Documentation
    ├── README.md          # Ce fichier
    └── requirements.txt   # Dépendances Python
```

## ⚙️ Configuration détaillée

### Profil utilisateur (`user_profile`)

```yaml
user_profile:
  skills: "Python, JavaScript, React, Node.js, TypeScript, SQL, PostgreSQL, MongoDB, Docker, Kubernetes, AWS, GCP, Git, CI/CD"
  experience_years: 4
  education_level: "Ingénieur"
```

### Critères de recherche (`search_criteria`)

```yaml
search_criteria:
  keywords: 
    - "ingénieur logiciel"
    - "développeur full stack"
    - "software engineer"
    - "full stack developer"
    - "tech lead"
    - "senior developer"
  
  locations:
    - "Genève, Suisse"
    - "Lausanne, Suisse"
    - "Vaud, Suisse"
    - "Lille, France"
    - "télétravail"
    - "full remote"
  
  salary_min: 40000
  salary_max: 1000000
  contract_types: ["CDI", "Freelance", "Mission longue"]
  remote_ok: true
```

### Sites de recherche (`job_sites`)

```yaml
job_sites:
  - name: "Indeed"
    url: "https://fr.indeed.com"
    enabled: true
  
  - name: "LinkedIn"
    url: "https://www.linkedin.com"
    enabled: false  # Nécessite une authentification
```

## 🎯 Score de compatibilité

Le système calcule automatiquement un score de compatibilité pour chaque offre :

- **40%** : Correspondance des compétences
- **30%** : Adéquation salariale
- **20%** : Localisation
- **10%** : Télétravail (si souhaité)

## 🌐 Interface Web

### Tableau de bord principal
- **Statistiques** : Total offres, score moyen, entreprises uniques
- **Contrôle du scraping** : Démarrage, progression temps réel
- **Offres récentes** : Aperçu des dernières trouvailles
- **Historique** : Sessions précédentes avec durée

### Pages disponibles
- **🏠 Accueil** : http://localhost:8080/
- **💼 Offres** : http://localhost:8080/jobs
- **⚙️ Configuration** : http://localhost:8080/config
- **📊 Sessions** : http://localhost:8080/sessions

### Fonctionnalités avancées
- **Filtrage** : Par score de compatibilité, entreprise, localisation
- **Pagination** : Navigation fluide dans les résultats
- **Export** : CSV et Excel directement depuis l'interface
- **Édition configuration** : Éditeur YAML intégré avec validation
- **Progression temps réel** : Suivi en direct du scraping

## 🗄️ Base de données SQLite

### Stockage automatique
- **Fichier unique** : `jobs.db` contient toutes les données
- **Déduplication automatique** : Plus de doublons
- **Historique complet** : Toutes les sessions sauvegardées
- **Recherche rapide** : Index optimisés

### Sauvegarde simple
```bash
# Copier le fichier = sauvegarde complète
cp jobs.db backup_jobs_$(date +%Y%m%d).db
```

### Consultation des données
- **Interface web** : Recommandée pour la navigation
- **DB Browser** : `brew install --cask db-browser-for-sqlite`
- **Ligne de commande** : `sqlite3 jobs.db`

Pour plus de détails, voir [SQLITE_GUIDE.md](SQLITE_GUIDE.md)

## 📊 Formats d'export

### Interface Web
- **CSV** : Export depuis la page des offres
- **Excel** : Avec formatage et filtres
- **API REST** : `/api/jobs` pour intégrations

### Base de données
Toutes les offres sont stockées avec :
```sql
- title (titre du poste)
- company (entreprise)
- location (localisation)
- salary (salaire)
- description (description complète)
- url (lien original)
- source (site source)
- match_score (score de compatibilité)
- scraped_at (date de découverte)
```

## 🔧 Personnalisation

### Via l'interface web
1. **Accédez** à http://localhost:8080/config
2. **Modifiez** la configuration YAML en direct
3. **Sauvegardez** avec validation automatique
4. **Relancez** le scraping avec les nouveaux paramètres

### Paramètres du scraper v2
```yaml
scraper_settings:
  max_google_queries: 15        # Requêtes Google maximum
  max_results_per_query: 30     # Résultats par requête
  max_jobs_total: 150          # Offres maximum à traiter
  delay_between_queries: 8      # Délai entre requêtes (sec)
  headless: false              # Mode navigation visible
  random_delays: true          # Délais aléatoires
  rotate_user_agents: true     # Rotation User-Agents
```

### Modifier le calcul du score
Modifiez la méthode `calculate_match_score()` dans `main.py` pour ajuster les critères et leur pondération.

## 🚨 Considérations éthiques

- **Respectez les conditions d'utilisation** des sites web
- **Utilisez des délais appropriés** entre requêtes (configuré à 2 secondes par défaut)
- **Ne surchargez pas les serveurs** avec trop de requêtes simultanées
- **Respectez les robots.txt** des sites

## 🐛 Dépannage

### Interface web ne se lance pas
```bash
# Vérifier l'environnement virtuel
python3 -m venv job_scraper_env
source job_scraper_env/bin/activate  # macOS/Linux
# ou job_scraper_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Port 8080 déjà utilisé
```bash
# Trouver le processus utilisant le port
lsof -i :8080
# Arrêter le processus ou changer de port dans app.py
```

### ChromeDriver non trouvé
```bash
# macOS
brew install chromedriver

# Vérifier l'installation
chromedriver --version
```

### Erreur de base de données
```bash
# Vérifier l'intégrité
sqlite3 jobs.db "PRAGMA integrity_check;"

# Sauvegarder et recréer si corruption
sqlite3 jobs.db ".dump" > backup.sql
rm jobs.db
sqlite3 jobs.db < backup.sql
```

### Pas de résultats
- **Vérifiez** la configuration dans l'interface web
- **Élargissez** les mots-clés et localisations
- **Augmentez** `max_jobs_total` dans la configuration
- **Consultez** les logs dans le terminal

## 🔮 Améliorations futures

- ✅ ~~Interface web avec Flask~~ **FAIT !**
- ✅ ~~Base de données pour historique~~ **FAIT !**
- 🔄 Notifications par email
- 🔄 Support pour plus de sites (Glassdoor, jobs.ch)
- 🔄 Filtres avancés dans l'interface
- 🔄 Analyse de tendances et graphiques
- 🔄 API REST complète
- 🔄 Mode sombre pour l'interface
- 🔄 Alertes personnalisées

## 📞 Support

Pour toute question ou problème :
1. **Consultez** cette documentation mise à jour
2. **Lisez** le [Guide SQLite](SQLITE_GUIDE.md) pour la base de données
3. **Vérifiez** les logs dans le terminal lors du scraping
4. **Testez** votre configuration dans l'interface web
5. **Consultez** l'historique des sessions pour diagnostiquer

### Ressources utiles
- **Interface web** : http://localhost:8080
- **Configuration** : http://localhost:8080/config
- **Guide SQLite** : [SQLITE_GUIDE.md](SQLITE_GUIDE.md)
- **Logs en temps réel** : Terminal lors du scraping

---

**Bon scraping avec votre nouvelle interface web ! 🌐🚀**