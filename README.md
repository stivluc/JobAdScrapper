# 🎯 Job Ad Scraper - Scraper d'Emploi Intelligent

Un scraper d'emploi puissant qui utilise **Google Search + Selenium** pour trouver des offres d'emploi **partout sur internet**, optimisé pour les ingénieurs logiciels.

## 🚀 Fonctionnalités

- ✅ **Recherche Google intelligente** : Trouve les offres sur TOUS les sites d'emploi
- ✅ **Localisations multiples** : Suisse romande, Lille, télétravail
- ✅ **Score de compatibilité** : Calcule automatiquement la pertinence de chaque offre
- ✅ **Multi-sites** : Indeed, LinkedIn, Glassdoor, Welcome to the Jungle, jobs.ch
- ✅ **Déduplication** : Supprime automatiquement les doublons
- ✅ **Anti-détection** : Rotation User-Agent, délais aléatoires
- ✅ **Export multiple** : JSON, CSV, Excel

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

### 4. Lancement

```bash
# Lancer le scraper
python main.py
```

## 📁 Structure du projet

```
JobAdScrapper/
├── main.py           # Script principal
├── config.yaml       # Configuration utilisateur
├── requirements.txt  # Dépendances Python
├── README.md         # Documentation
└── results/          # Dossier des résultats (créé automatiquement)
    ├── job_results_20240101_120000.json
    ├── job_results_20240101_120000.csv
    └── job_results_20240101_120000.xlsx
```

## ⚙️ Configuration détaillée

### Profil utilisateur (`user_profile`)

```yaml
user_profile:
  name: "Votre Nom"
  email: "votre.email@example.com"
  skills: "Python, JavaScript, SQL, Git, Docker"
  experience_years: 3
  education_level: "Master"
```

### Critères de recherche (`search_criteria`)

```yaml
search_criteria:
  keywords: ["développeur", "developer", "python", "data"]
  location: "Paris, France"
  salary_min: 40000
  salary_max: 70000
  contract_types: ["CDI", "CDD", "Freelance"]
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

## 📊 Formats de sortie

### JSON
```json
{
  "title": "Développeur Python",
  "company": "TechCorp",
  "location": "Paris",
  "salary": "45000€-55000€",
  "description": "Développement d'applications web...",
  "link": "https://...",
  "source": "Indeed",
  "match_score": 87.5,
  "scraped_at": "2024-01-01T12:00:00"
}
```

### CSV
Tableau avec colonnes : titre, entreprise, localisation, salaire, description, lien, source, score, date

### Excel
Même structure que CSV mais avec formatage et possibilité de filtres

## 🔧 Personnalisation

### Ajouter un nouveau site

1. Ajoutez le site dans `config.yaml`
2. Créez une méthode `scrape_nomdusite()` dans la classe `JobScraper`
3. Ajoutez l'appel dans la méthode `run()`

### Modifier le calcul du score

Modifiez la méthode `calculate_match_score()` pour ajuster les critères et leur pondération.

## 🚨 Considérations éthiques

- **Respectez les conditions d'utilisation** des sites web
- **Utilisez des délais appropriés** entre requêtes (configuré à 2 secondes par défaut)
- **Ne surchargez pas les serveurs** avec trop de requêtes simultanées
- **Respectez les robots.txt** des sites

## 🐛 Dépannage

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Erreur de connexion
- Vérifiez votre connexion internet
- Certains sites peuvent bloquer les scripts automatisés
- Augmentez le délai entre requêtes dans `config.yaml`

### Pas de résultats
- Vérifiez que les mots-clés sont appropriés
- Élargissez la zone géographique
- Vérifiez que les sites sont activés dans la configuration

## 🔮 Améliorations futures

- Interface web avec Flask
- Base de données pour historique
- Notifications par email
- Support pour plus de sites
- Filtres avancés
- Analyse de tendances

## 📞 Support

Pour toute question ou problème :
1. Vérifiez cette documentation
2. Consultez les messages d'erreur dans le terminal
3. Vérifiez votre fichier de configuration

---

**Bon scraping et bonne recherche d'emploi ! 🚀**