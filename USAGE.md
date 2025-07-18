# 🚀 Guide d'utilisation - Job Ad Scraper

## 📋 Aperçu

Ce scraper utilise **Google Search + Selenium** pour trouver des offres d'emploi **partout sur internet**. Il est optimisé pour les ingénieurs logiciels recherchant des postes en **Suisse romande**, **Lille**, ou en **télétravail**.

## 🎯 Configuration actuelle

### Profil ciblé
- **Poste** : Ingénieur logiciel / Développeur full stack
- **Expérience** : 5 ans
- **Compétences** : Python, JavaScript, React, Node.js, Docker, AWS...

### Zones de recherche
1. **Suisse romande** : Genève, Lausanne, Vaud, Fribourg, Neuchâtel
2. **France** : Lille, Métropole Lilloise, Nord
3. **Télétravail** : Offres 100% remote

### Critères salariaux
- **Minimum** : 60 000€ annuels
- **Maximum** : 120 000€ annuels

## 🚀 Utilisation

### 1. Lancement rapide
```bash
# Activer l'environnement
source job_scraper_env/bin/activate

# Lancer le scraper
python3 main.py

# Ou utiliser le script interactif
./start_scraper.sh
```

### 2. Personnalisation
Éditez `config.yaml` pour adapter :
- **Compétences** : Ajoutez/supprimez des technologies
- **Localisations** : Modifiez les zones géographiques
- **Salaires** : Ajustez les fourchettes
- **Mots-clés** : Changez les types de postes recherchés

### 3. Résultats
Les résultats sont sauvegardés dans `results/` :
- **JSON** : Données complètes pour analyse
- **CSV** : Import dans Excel/Google Sheets
- **Excel** : Format prêt pour filtrage

## 📊 Fonctionnement

### Phase 1 : Recherche Google
- Génère ~15 requêtes de recherche optimisées
- Utilise Selenium pour simuler un navigateur
- Respecte les délais anti-détection

### Phase 2 : Scraping multi-sites
- Visite chaque URL d'offre trouvée
- Extrait : titre, entreprise, lieu, salaire, description
- Supporte : Indeed, LinkedIn, Glassdoor, jobs.ch

### Phase 3 : Déduplication
- Supprime automatiquement les doublons
- Utilise titre + entreprise + lieu comme clé

### Phase 4 : Scoring
- **40%** : Correspondance des compétences
- **30%** : Adéquation salariale
- **20%** : Localisation (avec priorité)
- **10%** : Télétravail

## 🎯 Conseils d'optimisation

### Maximiser les résultats
1. **Lancez le scraper le matin** (moins de trafic)
2. **Attendez 24h** entre deux sessions
3. **Vérifiez config.yaml** avant chaque lancement
4. **Analysez les scores** : focalisez sur 70%+

### Éviter les blocages
1. **Respectez les délais** configurés
2. **N'exécutez pas trop fréquemment**
3. **Surveillez les performances** système
4. **Arrêtez si détection** (erreurs répétées)

## 🔧 Maintenance

### Mise à jour des dépendances
```bash
source job_scraper_env/bin/activate
pip install --upgrade -r requirements.txt
```

### Mise à jour ChromeDriver
```bash
brew upgrade chromedriver
```

### Ajout de nouveaux sites
1. Ajouter le domaine dans `is_job_url()`
2. Créer une méthode `scrape_nouveau_site()`
3. Ajouter le routage dans `scrape_job_url()`

## 📈 Performances typiques

### Résultats attendus
- **Durée** : 30-45 minutes
- **Offres trouvées** : 100-200
- **Offres uniques** : 80-150
- **Score moyen** : 60-80%

### Ressources système
- **CPU** : 30-50% pendant l'exécution
- **RAM** : 300-600MB
- **Réseau** : 1-2 requêtes/seconde

## 🚨 Dépannage

### Problèmes fréquents

#### ChromeDriver non trouvé
```bash
brew install chromedriver
```

#### Timeout Google
```yaml
# Dans config.yaml
scraper_settings:
  delay_between_queries: 12
  headless: true
```

#### Pas de résultats
```yaml
# Élargir les critères
search_criteria:
  salary_min: 50000
  locations: ["Suisse", "France", "télétravail"]
```

## 🎉 Bonnes pratiques

1. **Vérifiez la configuration** avant chaque lancement
2. **Analysez les résultats** pour affiner les critères
3. **Sauvegardez les bons résultats** avant modification
4. **Respectez les conditions** d'utilisation des sites
5. **Utilisez les données** de manière responsable

---

**🚀 Prêt à trouver votre emploi idéal ? Lancez `python3 main.py` !**