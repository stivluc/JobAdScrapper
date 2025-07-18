#!/usr/bin/env python3
"""
Scraper d'emploi v2 - Recherche Google + Selenium
Architecture modulaire pour scraper TOUTES les offres d'emploi via Google
"""

import json
import yaml
import time
import random
import re
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, urljoin
import hashlib

# Imports pour le web scraping
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Pour afficher la progression
from tqdm import tqdm
import pandas as pd
from pathlib import Path

class GoogleJobSearcher:
    """
    Module de recherche d'offres d'emploi via Google Search
    """
    
    def __init__(self, config: Dict):
        """
        Initialise le chercheur Google
        
        Args:
            config (Dict): Configuration du scraper
        """
        self.config = config
        self.driver = None
        self.found_urls = set()
        
        # User agents pour rotation anti-détection
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        Configure et initialise le driver Selenium
        
        Returns:
            webdriver.Chrome: Driver configuré
        """
        chrome_options = Options()
        
        # Configuration anti-détection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent rotatif
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Mode fenêtré pour éviter la détection (optionnel)
        if self.config['scraper_settings'].get('headless', False):
            chrome_options.add_argument("--headless")
        
        # Taille de fenêtre réaliste
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Script anti-détection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du driver: {e}")
            print("💡 Assurez-vous que ChromeDriver est installé et dans le PATH")
            raise
    
    def build_search_queries(self) -> List[str]:
        """
        Construit les requêtes de recherche Google optimisées
        
        Returns:
            List[str]: Liste des requêtes à exécuter
        """
        keywords = self.config['search_criteria']['keywords']
        locations = self.config['search_criteria']['locations']
        
        queries = []
        
        # Requêtes de base avec chaque localisation
        for keyword in keywords:
            for location in locations:
                # Recherche générale
                query = f'"{keyword}" "emploi" "{location}" 2024'
                queries.append(query)
                
                # Recherche avec salaire (seulement pour les localisations principales)
                if self.config['search_criteria'].get('salary_min') and location in locations[:5]:
                    salary_min = self.config['search_criteria']['salary_min']
                    query_salary = f'"{keyword}" "{location}" "{salary_min}€" "salaire"'
                    queries.append(query_salary)
        
        # Requêtes télétravail (sans localisation spécifique)
        if self.config['search_criteria'].get('remote_ok'):
            for keyword in keywords[:3]:  # Limite pour éviter trop de requêtes
                query_remote = f'"{keyword}" "télétravail" "remote" "100%" 2024'
                queries.append(query_remote)
        
        # Requêtes par site spécifique (seulement localisations principales)
        target_sites = [
            'indeed.fr', 'indeed.com', 'indeed.ch',
            'linkedin.com', 'welcometothejungle.com',
            'glassdoor.fr', 'glassdoor.com', 'glassdoor.ch',
            'monster.fr', 'monster.ch', 'jobs.ch'
        ]
        
        primary_locations = locations[:4]  # Genève, Lausanne, Vaud, Fribourg
        
        for site in target_sites:
            for keyword in keywords[:2]:  # Limite pour éviter trop de requêtes
                for location in primary_locations:
                    query = f'site:{site} "{keyword}" "{location}"'
                    queries.append(query)
        
        # Exclusions pour éviter les stages/alternances
        exclusions = ['-stage', '-stagiaire', '-alternance', '-internship', '-apprenti']
        
        # Ajout des exclusions aux requêtes principales
        enhanced_queries = []
        for query in queries:
            enhanced_query = f"{query} {' '.join(exclusions)}"
            enhanced_queries.append(enhanced_query)
        
        return enhanced_queries[:self.config['scraper_settings'].get('max_google_queries', 15)]
    
    def search_google(self, query: str, max_results: int = 50) -> List[str]:
        """
        Effectue une recherche Google et extrait les URLs d'offres
        
        Args:
            query (str): Requête de recherche
            max_results (int): Nombre maximum de résultats à récupérer
            
        Returns:
            List[str]: URLs des offres trouvées
        """
        if not self.driver:
            self.driver = self.setup_driver()
        
        print(f"🔍 Recherche Google: {query}")
        
        try:
            # Aller sur Google
            self.driver.get("https://www.google.com")
            
            # Attendre que la page se charge
            self.random_wait(1, 3)
            
            # Accepter les cookies si nécessaire
            try:
                accept_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepter') or contains(text(), 'Accept')]"))
                )
                accept_button.click()
                self.random_wait(1, 2)
            except TimeoutException:
                pass  # Pas de bouton de cookies
            
            # Trouver la barre de recherche
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Saisir la requête
            search_box.clear()
            search_box.send_keys(query)
            self.random_wait(0.5, 1.5)
            search_box.send_keys(Keys.RETURN)
            
            # Attendre les résultats
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            urls = []
            page_count = 0
            max_pages = min(5, max_results // 10)  # Environ 10 résultats par page
            
            while page_count < max_pages and len(urls) < max_results:
                # Extraire les URLs de la page actuelle
                page_urls = self.extract_job_urls_from_page()
                urls.extend(page_urls)
                
                # Passer à la page suivante
                if not self.goto_next_page():
                    break
                    
                page_count += 1
                self.random_wait(2, 4)  # Pause entre les pages
            
            print(f"✅ Trouvé {len(urls)} URLs pour: {query}")
            return urls[:max_results]
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche Google: {e}")
            return []
    
    def extract_job_urls_from_page(self) -> List[str]:
        """
        Extrait les URLs d'offres d'emploi de la page Google actuelle
        
        Returns:
            List[str]: URLs des offres trouvées
        """
        urls = []
        
        try:
            # Sélecteurs pour les liens de résultats Google
            result_links = self.driver.find_elements(By.CSS_SELECTOR, "div.g a[href]")
            
            for link in result_links:
                try:
                    url = link.get_attribute("href")
                    if url and self.is_job_url(url):
                        urls.append(url)
                except:
                    continue
            
            return urls
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des URLs: {e}")
            return []
    
    def is_job_url(self, url: str) -> bool:
        """
        Détermine si une URL pointe vers une offre d'emploi
        
        Args:
            url (str): URL à analyser
            
        Returns:
            bool: True si c'est une offre d'emploi
        """
        # Éviter les doublons
        if url in self.found_urls:
            return False
        
        # Domaines d'emploi connus
        job_domains = [
            'indeed.fr', 'indeed.com',
            'linkedin.com',
            'welcometothejungle.com',
            'glassdoor.fr', 'glassdoor.com',
            'monster.fr', 'monster.com',
            'apec.fr',
            'pole-emploi.fr',
            'leboncoin.fr',
            'cadremploi.fr',
            'regionsjob.com',
            'meteojob.com'
        ]
        
        # Mots-clés d'URLs d'emploi
        job_keywords = [
            '/job', '/emploi', '/offre', '/career', '/careers',
            '/recrutement', '/postes', '/jobs', '/opportunites'
        ]
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            
            # Vérifier les domaines connus
            if any(job_domain in domain for job_domain in job_domains):
                self.found_urls.add(url)
                return True
            
            # Vérifier les mots-clés dans le chemin
            if any(keyword in path for keyword in job_keywords):
                self.found_urls.add(url)
                return True
            
            return False
            
        except Exception:
            return False
    
    def goto_next_page(self) -> bool:
        """
        Navigue vers la page suivante des résultats Google
        
        Returns:
            bool: True si la navigation a réussi
        """
        try:
            # Chercher le bouton "Suivant"
            next_button = self.driver.find_element(By.ID, "pnnext")
            if next_button.is_enabled():
                next_button.click()
                self.random_wait(2, 4)
                return True
            return False
            
        except NoSuchElementException:
            return False
    
    def random_wait(self, min_seconds: float, max_seconds: float):
        """
        Attente aléatoire pour simuler un comportement humain
        
        Args:
            min_seconds (float): Temps minimum d'attente
            max_seconds (float): Temps maximum d'attente
        """
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def search_all_queries(self) -> List[str]:
        """
        Exécute toutes les requêtes de recherche et retourne les URLs
        
        Returns:
            List[str]: Toutes les URLs d'offres trouvées
        """
        all_urls = []
        queries = self.build_search_queries()
        
        print(f"🎯 Exécution de {len(queries)} requêtes de recherche")
        
        try:
            for i, query in enumerate(queries, 1):
                print(f"\n📊 Requête {i}/{len(queries)}")
                
                urls = self.search_google(
                    query, 
                    self.config['scraper_settings'].get('max_results_per_query', 20)
                )
                
                all_urls.extend(urls)
                
                # Pause entre les requêtes pour éviter la détection
                if i < len(queries):
                    wait_time = random.uniform(
                        self.config['scraper_settings'].get('delay_between_queries', 5),
                        self.config['scraper_settings'].get('delay_between_queries', 5) + 5
                    )
                    print(f"⏱️ Pause de {wait_time:.1f}s avant la prochaine requête...")
                    time.sleep(wait_time)
        
        finally:
            if self.driver:
                self.driver.quit()
        
        # Déduplication
        unique_urls = list(set(all_urls))
        print(f"🎉 Total: {len(unique_urls)} URLs uniques trouvées")
        
        return unique_urls

class SiteSpecificScraper:
    """
    Scraper spécialisé pour différents sites d'emploi
    """
    
    def __init__(self, config: Dict):
        """
        Initialise le scraper spécialisé
        
        Args:
            config (Dict): Configuration du scraper
        """
        self.config = config
        self.session = requests.Session()
        
        # Configuration de la session
        self.session.headers.update({
            'User-Agent': random.choice([
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ])
        })
    
    def scrape_job_url(self, url: str) -> Optional[Dict]:
        """
        Scrape une URL d'offre d'emploi spécifique
        
        Args:
            url (str): URL de l'offre à scraper
            
        Returns:
            Optional[Dict]: Données de l'offre ou None si échec
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            # Routage vers le scraper approprié
            if 'indeed' in domain:
                return self.scrape_indeed(url)
            elif 'linkedin' in domain:
                return self.scrape_linkedin(url)
            elif 'welcometothejungle' in domain:
                return self.scrape_wttj(url)
            elif 'glassdoor' in domain:
                return self.scrape_glassdoor(url)
            else:
                return self.scrape_generic(url)
                
        except Exception as e:
            print(f"⚠️ Erreur lors du scraping de {url}: {e}")
            return None
    
    def scrape_indeed(self, url: str) -> Optional[Dict]:
        """
        Scrape une offre Indeed
        
        Args:
            url (str): URL Indeed
            
        Returns:
            Optional[Dict]: Données extraites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction des données Indeed
            title = self.safe_extract_text(soup, 'h1[data-jk]', 'h1.jobsearch-JobInfoHeader-title')
            company = self.safe_extract_text(soup, 'div[data-testid="inlineHeader-companyName"]', 'span.companyName')
            location = self.safe_extract_text(soup, 'div[data-testid="job-location"]', 'div.companyLocation')
            
            # Salaire
            salary = self.safe_extract_text(soup, 'span[data-testid="job-compensation"]', 'span.salaryText')
            
            # Description
            description_elem = soup.find('div', {'id': 'jobDescriptionText'}) or soup.find('div', class_='jobsearch-jobDescriptionText')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'description': description,
                'url': url,
                'source': 'Indeed',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur Indeed {url}: {e}")
            return None
    
    def scrape_linkedin(self, url: str) -> Optional[Dict]:
        """
        Scrape une offre LinkedIn (limité sans authentification)
        
        Args:
            url (str): URL LinkedIn
            
        Returns:
            Optional[Dict]: Données extraites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # LinkedIn nécessite souvent une authentification
            # Extraction basique des métadonnées
            title = self.safe_extract_text(soup, 'h1', 'title')
            
            # Nettoyage du titre
            if title and ' - ' in title:
                title = title.split(' - ')[0]
            
            return {
                'title': title,
                'company': 'LinkedIn (auth required)',
                'location': '',
                'salary': '',
                'description': 'Authentification requise pour LinkedIn',
                'url': url,
                'source': 'LinkedIn',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur LinkedIn {url}: {e}")
            return None
    
    def scrape_wttj(self, url: str) -> Optional[Dict]:
        """
        Scrape une offre Welcome to the Jungle
        
        Args:
            url (str): URL WTTJ
            
        Returns:
            Optional[Dict]: Données extraites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Sélecteurs WTTJ
            title = self.safe_extract_text(soup, 'h1[data-testid="job-title"]', 'h1')
            company = self.safe_extract_text(soup, 'a[data-testid="company-name"]', 'span[data-testid="company-name"]')
            location = self.safe_extract_text(soup, 'span[data-testid="job-location"]')
            
            # Description
            description_elem = soup.find('div', {'data-testid': 'job-description'})
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'salary': '',
                'description': description,
                'url': url,
                'source': 'Welcome to the Jungle',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur WTTJ {url}: {e}")
            return None
    
    def scrape_glassdoor(self, url: str) -> Optional[Dict]:
        """
        Scrape une offre Glassdoor
        
        Args:
            url (str): URL Glassdoor
            
        Returns:
            Optional[Dict]: Données extraites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Sélecteurs Glassdoor
            title = self.safe_extract_text(soup, 'div[data-test="job-title"]', 'h2')
            company = self.safe_extract_text(soup, 'div[data-test="employer-name"]', 'span[data-test="employer-name"]')
            location = self.safe_extract_text(soup, 'div[data-test="job-location"]')
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'salary': '',
                'description': 'Données limitées sur Glassdoor',
                'url': url,
                'source': 'Glassdoor',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur Glassdoor {url}: {e}")
            return None
    
    def scrape_generic(self, url: str) -> Optional[Dict]:
        """
        Scraper générique pour sites inconnus
        
        Args:
            url (str): URL du site inconnu
            
        Returns:
            Optional[Dict]: Données extraites
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction générique basée sur les balises communes
            title = self.safe_extract_text(soup, 'h1', 'title')
            
            # Nettoyage du titre
            if title and ' - ' in title:
                title = title.split(' - ')[0]
            
            # Recherche de mots-clés d'entreprise
            company = self.extract_company_from_text(soup.get_text())
            
            return {
                'title': title,
                'company': company,
                'location': '',
                'salary': '',
                'description': 'Site générique - données limitées',
                'url': url,
                'source': urlparse(url).netloc,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur scraping générique {url}: {e}")
            return None
    
    def safe_extract_text(self, soup: BeautifulSoup, *selectors: str) -> str:
        """
        Extrait le texte en essayant plusieurs sélecteurs
        
        Args:
            soup (BeautifulSoup): Objet BeautifulSoup
            *selectors (str): Sélecteurs CSS à essayer
            
        Returns:
            str: Texte extrait ou chaîne vide
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except:
                continue
        return ""
    
    def extract_company_from_text(self, text: str) -> str:
        """
        Extrait le nom d'entreprise du texte avec des heuristiques
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            str: Nom d'entreprise probable
        """
        # Patterns communs pour les entreprises
        patterns = [
            r'chez\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+recrute',
            r'Entreprise\s*:\s*([A-Z][a-zA-Z\s]+)',
            r'Company\s*:\s*([A-Z][a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Entreprise non spécifiée"

class JobDeduplicator:
    """
    Gestionnaire de déduplication des offres d'emploi
    """
    
    def __init__(self):
        """
        Initialise le déduplicateur
        """
        self.seen_hashes = set()
    
    def deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Supprime les doublons d'une liste d'offres
        
        Args:
            jobs (List[Dict]): Liste des offres à dédupliquer
            
        Returns:
            List[Dict]: Liste sans doublons
        """
        unique_jobs = []
        
        for job in jobs:
            job_hash = self.calculate_job_hash(job)
            
            if job_hash not in self.seen_hashes:
                self.seen_hashes.add(job_hash)
                unique_jobs.append(job)
        
        print(f"🔄 Déduplication: {len(jobs)} -> {len(unique_jobs)} offres uniques")
        return unique_jobs
    
    def calculate_job_hash(self, job: Dict) -> str:
        """
        Calcule un hash unique pour une offre
        
        Args:
            job (Dict): Données de l'offre
            
        Returns:
            str: Hash unique
        """
        # Éléments pour identifier l'unicité
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        location = job.get('location', '').lower().strip()
        
        # Normalisation
        title = re.sub(r'[^\w\s]', '', title)
        company = re.sub(r'[^\w\s]', '', company)
        location = re.sub(r'[^\w\s]', '', location)
        
        # Création du hash
        unique_string = f"{title}|{company}|{location}"
        return hashlib.md5(unique_string.encode()).hexdigest()

class EnhancedJobScraper:
    """
    Scraper d'emploi v2 - Architecture complète
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialise le scraper v2
        
        Args:
            config_path (str): Chemin vers la configuration
        """
        self.config = self.load_config(config_path)
        self.jobs_data = []
        
        # Modules spécialisés
        self.google_searcher = GoogleJobSearcher(self.config)
        self.site_scraper = SiteSpecificScraper(self.config)
        self.deduplicator = JobDeduplicator()
        
        print(f"🚀 Scraper initialisé - Profil Ingénieur Full Stack")
        print(f"📍 Recherche: {', '.join(self.config['search_criteria']['keywords'][:3])}...")
        print(f"🏠 Localisations: {', '.join(self.config['search_criteria']['locations'][:3])}...")
        print(f"🔍 Mode: Recherche Google + Scraping multi-sites")
    
    def load_config(self, config_path: str) -> Dict:
        """
        Charge la configuration
        
        Args:
            config_path (str): Chemin vers le fichier de configuration
            
        Returns:
            Dict: Configuration chargée
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"✅ Configuration chargée depuis {config_path}")
                return config
        except Exception as e:
            print(f"❌ Erreur lors du chargement de la configuration: {e}")
            raise
    
    def calculate_match_score(self, job_data: Dict) -> float:
        """
        Calcule le score de compatibilité
        
        Args:
            job_data (Dict): Données de l'offre
            
        Returns:
            float: Score de compatibilité (0-100)
        """
        score = 0
        total_criteria = 0
        
        # Vérification des compétences (40%)
        user_skills = [skill.strip().lower() for skill in 
                      self.config['user_profile']['skills'].split(',')]
        
        job_description = job_data.get('description', '').lower()
        job_title = job_data.get('title', '').lower()
        
        # Recherche des compétences dans titre + description
        skill_matches = sum(1 for skill in user_skills 
                          if skill in job_description or skill in job_title)
        
        if user_skills:
            score += (skill_matches / len(user_skills)) * 40
            total_criteria += 40
        
        # Vérification du salaire (30%)
        salary_text = job_data.get('salary', '').lower()
        if salary_text and any(char.isdigit() for char in salary_text):
            # Extraction simple du salaire
            salary_numbers = re.findall(r'\d+', salary_text)
            if salary_numbers:
                job_salary = int(salary_numbers[0])
                if job_salary >= 1000:  # Salaire mensuel probable
                    job_salary *= 12  # Convertir en annuel
                
                target_salary = self.config['search_criteria']['salary_max']
                if job_salary >= self.config['search_criteria']['salary_min']:
                    salary_score = min(job_salary / target_salary, 1) * 30
                    score += salary_score
            total_criteria += 30
        else:
            total_criteria += 30  # Compter même si pas de salaire
        
        # Vérification de la localisation (20%)
        job_location = job_data.get('location', '').lower()
        user_locations = [loc.lower() for loc in self.config['search_criteria']['locations']]
        
        # Calcul du score de localisation avec priorité
        location_score = 0
        for i, user_loc in enumerate(user_locations):
            if user_loc in job_location:
                # Score dégressif selon la priorité de la localisation
                priority_bonus = max(0, 20 - (i * 2))  # Moins de points pour les localisations moins prioritaires
                location_score = max(location_score, priority_bonus)
                break
        
        score += location_score
        total_criteria += 20
        
        # Vérification du télétravail (10%)
        if self.config['search_criteria']['remote_ok']:
            remote_keywords = ['télétravail', 'remote', 'distance', 'hybride']
            if any(keyword in job_description or keyword in job_title 
                  for keyword in remote_keywords):
                score += 10
        total_criteria += 10
        
        return (score / total_criteria) * 100 if total_criteria > 0 else 0
    
    def run(self) -> None:
        """
        Lance le processus de scraping complet v2
        """
        print("🎯 Démarrage du scraping v2 (Google + Multi-sites)...")
        
        # Phase 1: Recherche Google
        print("\n📊 Phase 1: Recherche Google")
        print("=" * 40)
        
        job_urls = self.google_searcher.search_all_queries()
        
        if not job_urls:
            print("❌ Aucune URL trouvée via Google")
            return
        
        # Phase 2: Scraping des offres
        print("\n📊 Phase 2: Scraping des offres")
        print("=" * 40)
        
        max_jobs = self.config['scraper_settings'].get('max_jobs_total', 100)
        jobs_to_process = job_urls[:max_jobs]
        
        scraped_jobs = []
        
        for i, url in enumerate(tqdm(jobs_to_process, desc="Scraping des offres"), 1):
            job_data = self.site_scraper.scrape_job_url(url)
            
            if job_data:
                # Calcul du score de compatibilité
                job_data['match_score'] = self.calculate_match_score(job_data)
                scraped_jobs.append(job_data)
            
            # Délai entre les requêtes
            if i % 10 == 0:  # Pause plus longue tous les 10 scrapes
                time.sleep(random.uniform(3, 6))
            else:
                time.sleep(random.uniform(1, 3))
        
        # Phase 3: Déduplication
        print("\n📊 Phase 3: Déduplication")
        print("=" * 40)
        
        self.jobs_data = self.deduplicator.deduplicate_jobs(scraped_jobs)
        
        # Phase 4: Tri et résultats
        print("\n📊 Phase 4: Analyse des résultats")
        print("=" * 40)
        
        # Tri par score de compatibilité
        self.jobs_data.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Affichage des résultats
        print(f"\n📈 Résultats du scraping v2:")
        print(f"💼 {len(self.jobs_data)} offres uniques trouvées")
        
        if self.jobs_data:
            print(f"🏆 Meilleur score de compatibilité: {self.jobs_data[0]['match_score']:.1f}%")
            
            # Statistiques par source
            sources = {}
            for job in self.jobs_data:
                source = job.get('source', 'Inconnu')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n📊 Répartition par source:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                print(f"   {source}: {count} offres")
            
            # Top 5 des offres
            print(f"\n🎯 Top 5 des offres les plus compatibles:")
            for i, job in enumerate(self.jobs_data[:5], 1):
                print(f"{i}. {job['title']} chez {job['company']} "
                      f"({job['match_score']:.1f}% compatibilité)")
        
        # Sauvegarde
        if self.jobs_data:
            self.save_results('json')
            self.save_results('csv')
            self.save_results('excel')
    
    def save_results(self, format_type: str = 'json') -> str:
        """
        Sauvegarde les résultats
        
        Args:
            format_type (str): Format de sauvegarde
            
        Returns:
            str: Chemin du fichier sauvegardé
        """
        if not self.jobs_data:
            return ""
        
        # Création du dossier de résultats
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Nom du fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            filename = f"job_results_v2_{timestamp}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
        
        elif format_type == 'csv':
            filename = f"job_results_v2_{timestamp}.csv"
            filepath = results_dir / filename
            
            df = pd.DataFrame(self.jobs_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        elif format_type == 'excel':
            filename = f"job_results_v2_{timestamp}.xlsx"
            filepath = results_dir / filename
            
            df = pd.DataFrame(self.jobs_data)
            df.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f"💾 Résultats sauvegardés dans {filepath}")
        return str(filepath)

def main():
    """
    Fonction principale du scraper v2
    """
    try:
        print("🎯 Job Scraper v2 - Recherche Google + Multi-sites")
        print("=" * 60)
        
        # Création et lancement du scraper
        scraper = EnhancedJobScraper()
        scraper.run()
        
    except KeyboardInterrupt:
        print("\n❌ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        raise

if __name__ == "__main__":
    main()