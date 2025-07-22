#!/usr/bin/env python3
"""
API-based Job Scraper - Version moderne sans ChromeDriver
Utilise des APIs publiques et des techniques de scraping léger
"""

import json
import yaml
import time
import random
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import quote_plus, urljoin
import hashlib
from dataclasses import dataclass
from pathlib import Path
from secure_config import SecureConfig, get_api_key, has_api_key, get_search_config

@dataclass
class JobOffer:
    """Représentation d'une offre d'emploi"""
    title: str
    company: str
    location: str
    salary: str
    description: str
    url: str
    source: str
    match_score: float = 0.0
    scraped_at: str = ""

class APIJobScraper:
    """
    Scraper moderne utilisant des APIs publiques et techniques légères
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialise le scraper API
        
        Args:
            config_path (str): Chemin vers la configuration
        """
        # Utilisation de la configuration sécurisée
        self.secure_config = SecureConfig(config_path)
        self.config = self.secure_config.config
        self.search_config = self.secure_config.get_search_config()
        self.jobs_data = []
        self.session = requests.Session()
        
        # Configuration des headers pour éviter la détection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, application/xhtml+xml, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        print(f"🚀 API Scraper initialisé - Recherche intelligente")
        print(f"📍 Localisations: {', '.join(self.config['search_criteria']['locations'][:3])}...")
        print(f"🔍 Mode: APIs publiques + scraping léger")
    
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
    
    def scrape_adzuna_api(self) -> List[JobOffer]:
        """
        Scraper via l'API Adzuna (gratuite avec limite)
        """
        jobs = []
        
        try:
            # Configuration Adzuna
            base_url = "https://api.adzuna.com/v1/api/jobs"
            
            # Paramètres de recherche dynamiques
            keywords = self.search_config['keywords'][:3]  # Limiter à 3 pour éviter les quotas
            location_map = self.search_config['locations']
            
            # Construire la liste des pays depuis la config
            countries = []
            if location_map.get('switzerland'):
                countries.append('switzerland')
            if location_map.get('france'):
                countries.append('france')
            
            for keyword in keywords:
                for country in countries:
                    try:
                        # Construction de l'URL API
                        country_code = 'ch' if country == 'switzerland' else 'fr'
                        url = f"{base_url}/{country_code}/search/1"
                        
                        # Utiliser les localisations spécifiques de la config
                        where_locations = location_map[country]
                        where_param = where_locations[0] if where_locations else ('geneva' if country == 'switzerland' else 'lille')
                        
                        params = {
                            'what': keyword,
                            'where': where_param,
                            'results_per_page': 20,
                            'sort_by': 'date'
                        }
                        
                        # Ajouter les clés API si disponibles
                        if has_api_key('adzuna_app_id') and has_api_key('adzuna_app_key'):
                            params['app_id'] = get_api_key('adzuna_app_id')
                            params['app_key'] = get_api_key('adzuna_app_key')
                        else:
                            print(f"⚠️ Clés API Adzuna non configurées - recherche limitée")
                            continue
                        
                        print(f"🔍 Recherche Adzuna: {keyword} à {where_param} ({country})")
                        print(f"    📡 URL API: {url}")
                        print(f"    📋 Paramètres: {params}")
                        
                        response = self.session.get(url, params=params, timeout=10)
                        print(f"    📊 Status: {response.status_code} | Taille: {len(response.text)} bytes")
                        
                        if response.status_code == 200:
                            data = response.json()
                            total_results = len(data.get('results', []))
                            print(f"    ✅ {total_results} résultats reçus d'Adzuna")
                            
                            for i, result in enumerate(data.get('results', []), 1):
                                job_title = result.get('title', '')
                                company_data = result.get('company', {})
                                company_name = company_data.get('display_name', '') if isinstance(company_data, dict) else str(company_data)
                                location_data = result.get('location', {})
                                job_location = location_data.get('display_name', '') if isinstance(location_data, dict) else str(location_data)
                                job_url = result.get('redirect_url', '')
                                salary_info = self.format_salary(result.get('salary_min'), result.get('salary_max'))
                                
                                print(f"    📍 {i:2d}. {job_title}")
                                print(f"        🏢 {company_name} | 📍 {job_location}")
                                print(f"        💰 {salary_info} | 🔗 {job_url[:50]}...")
                                
                                job = JobOffer(
                                    title=job_title,
                                    company=company_name,
                                    location=job_location,
                                    salary=salary_info,
                                    description=result.get('description', ''),
                                    url=job_url,
                                    source='Adzuna API',
                                    scraped_at=datetime.now().isoformat()
                                )
                                jobs.append(job)
                        
                        else:
                            print(f"    ❌ Status {response.status_code}: {response.text[:100]}...")
                        
                        # Pause entre les requêtes
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"⚠️ Erreur Adzuna pour {keyword} à {country}: {e}")
                        continue
            
            print(f"✅ Adzuna: {len(jobs)} offres trouvées")
            
        except Exception as e:
            print(f"❌ Erreur générale Adzuna: {e}")
        
        return jobs
    
    def scrape_jobs_api(self) -> List[JobOffer]:
        """
        Scraper via l'API Jobs.ch (gratuite)
        """
        jobs = []
        
        try:
            base_url = "https://www.jobs.ch/api/search"
            
            keywords = self.search_config['keywords'][:3]
            
            for keyword in keywords:
                try:
                    # Utiliser les localisations dynamiques de la config
                    swiss_locations = self.search_config['locations'].get('switzerland', ['geneva'])
                    location_param = swiss_locations[0].title() if swiss_locations else 'Geneva'
                    
                    params = {
                        'query': keyword,
                        'location': location_param,
                        'limit': 20,
                        'offset': 0
                    }
                    
                    print(f"🔍 Recherche Jobs.ch: {keyword}")
                    
                    response = self.session.get(base_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for result in data.get('jobs', []):
                            job = JobOffer(
                                title=result.get('title', ''),
                                company=result.get('company', ''),
                                location=result.get('location', ''),
                                salary=result.get('salary', ''),
                                description=result.get('description', ''),
                                url=result.get('url', ''),
                                source='Jobs.ch API',
                                scraped_at=datetime.now().isoformat()
                            )
                            jobs.append(job)
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"⚠️ Erreur Jobs.ch pour {keyword}: {e}")
                    continue
            
            print(f"✅ Jobs.ch: {len(jobs)} offres trouvées")
            
        except Exception as e:
            print(f"❌ Erreur générale Jobs.ch: {e}")
        
        return jobs
    
    def scrape_indeed_rss(self) -> List[JobOffer]:
        """
        Scraper Indeed via flux RSS (plus fiable que Selenium)
        """
        jobs = []
        
        try:
            # Utilisation de la configuration dynamique
            keywords = self.search_config['keywords'][:5]  # Plus de mots-clés
            locations = self.search_config['locations']
            
            # Construire des URLs RSS Indeed dynamiquement depuis config.yaml
            rss_configs = []
            
            # Configuration Suisse
            if locations['switzerland']:
                rss_configs.append({
                    'domain': 'ch.indeed.com', 
                    'locations': locations['switzerland'], 
                    'country': 'Suisse'
                })
            
            # Configuration France
            if locations['france']:
                rss_configs.append({
                    'domain': 'fr.indeed.com', 
                    'locations': locations['france'], 
                    'country': 'France'
                })
            
            # Si pas de configuration spécifique, utiliser des valeurs par défaut
            if not rss_configs:
                rss_configs = [
                    {'domain': 'ch.indeed.com', 'locations': ['geneva', 'lausanne'], 'country': 'Suisse'},
                    {'domain': 'fr.indeed.com', 'locations': ['lille', 'paris'], 'country': 'France'}
                ]
            
            for config in rss_configs:
                for keyword in keywords:
                    for location in config['locations']:
                        try:
                            # Construction URL RSS correcte
                            query = quote_plus(keyword.replace(' ', '+'))
                            loc = quote_plus(location)
                            
                            rss_url = f"https://{config['domain']}/rss?q={query}&l={loc}&sort=date&limit=50"
                            
                            print(f"🔍 Indeed {config['country']}: {keyword} à {location}")
                            print(f"    📡 RSS URL: {rss_url}")
                            
                            # Headers spécifiques pour Indeed
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                                'Accept': 'application/rss+xml, application/xml, text/xml',
                                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                                'Cache-Control': 'no-cache'
                            }
                            
                            response = self.session.get(rss_url, headers=headers, timeout=15)
                            print(f"    📊 Status: {response.status_code} | Content-Type: {response.headers.get('content-type', 'N/A')}")
                            
                            if response.status_code == 200 and 'xml' in response.headers.get('content-type', ''):
                                print(f"    🔍 Parsing RSS XML ({len(response.text)} caractères)...")
                                jobs_found = self.parse_indeed_rss(response.text, location, config['country'])
                                jobs.extend(jobs_found)
                                print(f"    ✅ {len(jobs_found)} offres extraites du RSS")
                                
                                # Afficher quelques exemples d'offres
                                for i, job in enumerate(jobs_found[:3], 1):
                                    print(f"      📍 {i}. {job.title} | {job.company}")
                            else:
                                print(f"   → Pas de RSS disponible ({response.status_code})")
                            
                            # Délai pour éviter le rate limiting
                            time.sleep(random.uniform(3, 6))
                            
                        except Exception as e:
                            print(f"⚠️ Erreur Indeed {keyword} à {location}: {e}")
                            continue
            
            print(f"✅ Indeed RSS: {len(jobs)} offres trouvées au total")
            
        except Exception as e:
            print(f"❌ Erreur générale Indeed RSS: {e}")
        
        return jobs
    
    def parse_indeed_rss(self, xml_content: str, location: str, country: str) -> List[JobOffer]:
        """
        Parse le contenu XML d'Indeed RSS
        """
        jobs = []
        
        try:
            import xml.etree.ElementTree as ET
            
            # Nettoyer le XML si nécessaire
            xml_content = xml_content.replace('&', '&amp;')
            
            root = ET.fromstring(xml_content)
            
            # Indeed utilise le format RSS standard
            for item in root.findall('.//item'):
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link') 
                    desc_elem = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    if title_elem is not None and link_elem is not None:
                        title_text = title_elem.text or ''
                        link_url = link_elem.text or ''
                        
                        # Extraction entreprise du titre Indeed (format: "Titre - Entreprise")
                        company = self.extract_company_from_indeed_title(title_text)
                        
                        # Nettoyer le titre (retirer l'entreprise)
                        clean_title = title_text
                        if ' - ' in title_text:
                            clean_title = title_text.split(' - ')[0]
                        
                        # Description (HTML dans Indeed RSS)
                        description = ''
                        if desc_elem is not None and desc_elem.text:
                            # Retirer les balises HTML basiques
                            desc_text = desc_elem.text
                            desc_text = re.sub(r'<[^>]+>', '', desc_text)
                            desc_text = desc_text.replace('&lt;', '<').replace('&gt;', '>')
                            description = desc_text[:300]  # Limiter la taille
                        
                        job = JobOffer(
                            title=clean_title,
                            company=company,
                            location=f"{location.title()}, {country}",
                            salary='',  # Indeed RSS ne contient généralement pas le salaire
                            description=description,
                            url=link_url,
                            source='Indeed RSS',
                            scraped_at=datetime.now().isoformat()
                        )
                        jobs.append(job)
                        
                except Exception as e:
                    print(f"⚠️ Erreur parsing item RSS: {e}")
                    continue
                    
        except ET.ParseError as e:
            print(f"⚠️ Erreur XML parsing: {e}")
        except Exception as e:
            print(f"⚠️ Erreur parse RSS: {e}")
            
        return jobs
    
    def scrape_github_jobs(self) -> List[JobOffer]:
        """
        Scraper GitHub Jobs (vraies offres tech)
        """
        jobs = []
        
        try:
            # GitHub Jobs a fermé, mais on peut utiliser des alternatives
            print("🔍 Recherche via sources alternatives...")
            
            # Alternative: Adzuna API gratuite (vraie)
            keywords = ['python', 'javascript', 'react', 'node.js', 'full stack']
            
            for keyword in keywords[:2]:  # Limiter pour éviter quotas
                try:
                    # API Adzuna avec clés sécurisées
                    api_url = f"https://api.adzuna.com/v1/api/jobs/ch/search/1"
                    params = {
                        'what': keyword,
                        'where': 'geneva',
                        'results_per_page': 10,
                        'sort_by': 'date'
                    }
                    
                    # Ajouter les clés API si disponibles
                    if has_api_key('adzuna_app_id') and has_api_key('adzuna_app_key'):
                        params['app_id'] = get_api_key('adzuna_app_id')
                        params['app_key'] = get_api_key('adzuna_app_key')
                    else:
                        print(f"⚠️ Clés API Adzuna non configurées - recherche limitée")
                        continue
                    
                    response = self.session.get(api_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for result in data.get('results', []):
                            company_data = result.get('company', {})
                            location_data = result.get('location', {})
                            
                            job = JobOffer(
                                title=result.get('title', ''),
                                company=company_data.get('display_name', 'Entreprise non spécifiée'),
                                location=location_data.get('display_name', 'Suisse'),
                                salary=self.format_salary(result.get('salary_min'), result.get('salary_max')),
                                description=result.get('description', '')[:400],
                                url=result.get('redirect_url', ''),
                                source='Adzuna API',
                                scraped_at=datetime.now().isoformat()
                            )
                            jobs.append(job)
                    
                    time.sleep(2)  # Respect API limits
                    
                except Exception as e:
                    print(f"⚠️ Erreur API pour {keyword}: {e}")
                    continue
            
            print(f"✅ Sources alternatives: {len(jobs)} offres trouvées")
            
        except Exception as e:
            print(f"❌ Erreur recherche alternative: {e}")
        
        return jobs
    
    def scrape_rapidapi_jobs(self) -> List[JobOffer]:
        """
        Scraper via RapidAPI JSearch (jobs API)
        """
        jobs = []
        
        try:
            print("🔍 Recherche via RapidAPI JSearch...")
            
            # Check if RapidAPI key is available
            if not (has_api_key('rapidapi_key') or has_api_key('rapidapi_app')):
                print("⚠️ Clés RapidAPI non configurées - saut de cette source")
                return jobs
            
            rapidapi_key = get_api_key('rapidapi_key')
            keywords = self.search_config['keywords'][:3]  # Limit to avoid quota
            
            # RapidAPI JSearch endpoint
            url = "https://jsearch.p.rapidapi.com/search"
            
            for keyword in keywords:
                try:
                    # Search in Switzerland and France
                    for country in ['Switzerland', 'France']:
                        params = {
                            'query': f'{keyword} {country}',
                            'page': '1',
                            'num_pages': '1',
                            'date_posted': 'week'
                        }
                        
                        headers = {
                            'X-RapidAPI-Key': rapidapi_key,
                            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
                        }
                        
                        print(f"🔍 RapidAPI: {keyword} en {country}")
                        print(f"    📡 URL: {url}")
                        print(f"    📋 Paramètres: {params}")
                        
                        response = self.session.get(url, headers=headers, params=params, timeout=15)
                        print(f"    📊 Status: {response.status_code} | Taille: {len(response.text)} bytes")
                        
                        if response.status_code == 200:
                            data = response.json()
                            job_results = data.get('data', [])
                            print(f"    ✅ {len(job_results)} résultats reçus de RapidAPI")
                            
                            for i, result in enumerate(job_results, 1):
                                job_title = result.get('job_title', '')
                                employer_name = result.get('employer_name', '')
                                job_location = result.get('job_city', '') + ', ' + result.get('job_country', '')
                                job_url = result.get('job_apply_link', '')
                                job_description = result.get('job_description', '')
                                
                                print(f"    📍 {i:2d}. {job_title}")
                                print(f"        🏢 {employer_name} | 📍 {job_location}")
                                print(f"        🔗 {job_url[:50]}...")
                                
                                if job_url and job_url.startswith('http'):
                                    job = JobOffer(
                                        title=job_title,
                                        company=employer_name,
                                        location=job_location,
                                        salary=result.get('job_salary', ''),
                                        description=job_description[:400] if job_description else '',
                                        url=job_url,
                                        source='RapidAPI JSearch',
                                        scraped_at=datetime.now().isoformat()
                                    )
                                    jobs.append(job)
                        else:
                            print(f"    ❌ Status {response.status_code}: {response.text[:100]}...")
                        
                        # Delay between requests
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"⚠️ Erreur RapidAPI pour {keyword}: {e}")
                    continue
            
            print(f"✅ RapidAPI: {len(jobs)} offres trouvées")
            
        except Exception as e:
            print(f"❌ Erreur RapidAPI: {e}")
        
        return jobs
    
    def extract_company_from_indeed_title(self, title: str) -> str:
        """
        Extrait le nom d'entreprise du titre Indeed
        """
        # Indeed format: "Titre - Entreprise"
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) >= 2:
                return parts[-1].strip()
        
        return "Entreprise non spécifiée"
    
    def format_salary(self, min_salary: Optional[float], max_salary: Optional[float]) -> str:
        """
        Formate les informations de salaire
        """
        if min_salary and max_salary:
            return f"{int(min_salary):,} - {int(max_salary):,} €/an"
        elif min_salary:
            return f"À partir de {int(min_salary):,} €/an"
        elif max_salary:
            return f"Jusqu'à {int(max_salary):,} €/an"
        else:
            return ""
    
    def calculate_match_score(self, job: JobOffer, verbose: bool = False) -> float:
        """
        Calcule le score de compatibilité avec logging détaillé
        """
        score = 0
        total_criteria = 0
        scoring_details = []
        
        # Compétences (40%)
        user_skills = [skill.strip().lower() for skill in 
                      self.search_config['skills'].split(',')]
        
        job_text = f"{job.title} {job.description}".lower()
        matched_skills = [skill for skill in user_skills if skill in job_text]
        skill_matches = len(matched_skills)
        
        if user_skills:
            skill_score = (skill_matches / len(user_skills)) * 40
            score += skill_score
            total_criteria += 40
            scoring_details.append(f"Compétences: {skill_matches}/{len(user_skills)} = {skill_score:.1f}/40")
            if verbose and matched_skills:
                scoring_details.append(f"  Compétences trouvées: {', '.join(matched_skills[:5])}")
        
        # Localisation (30%)
        # Construire la liste des localisations utilisateur depuis la config
        user_locations = []
        for country, locations in self.search_config['locations'].items():
            user_locations.extend([loc.lower() for loc in locations])
        job_location = job.location.lower()
        
        location_score = 0
        for i, user_loc in enumerate(user_locations):
            if user_loc in job_location:
                priority_bonus = max(0, 30 - (i * 3))
                location_score = max(location_score, priority_bonus)
                break
        
        score += location_score
        total_criteria += 30
        scoring_details.append(f"Localisation: {location_score:.1f}/30")
        
        # Télétravail (15%)
        remote_keywords = ['télétravail', 'remote', 'distance', 'hybride']
        remote_found = [kw for kw in remote_keywords if kw in job_text]
        remote_score = 15 if remote_found else 0
        score += remote_score
        total_criteria += 15
        scoring_details.append(f"Télétravail: {remote_score}/15" + (f" ({', '.join(remote_found)})" if remote_found else ""))
        
        # Source fiable (15%)
        source_scores = {
            'Indeed RSS': 15,
            'Adzuna API': 12,
            'Jobs.ch API': 10,
            'LinkedIn Sample': 8
        }
        source_score = source_scores.get(job.source, 5)
        score += source_score
        total_criteria += 15
        scoring_details.append(f"Source: {source_score}/15 ({job.source})")
        
        final_score = (score / total_criteria) * 100 if total_criteria > 0 else 0
        
        if verbose:
            print(f"    📊 Analyse de pertinence pour: {job.title}")
            for detail in scoring_details:
                print(f"      {detail}")
            print(f"      🎯 Score final: {final_score:.1f}%")
        
        return final_score
    
    def deduplicate_jobs(self, jobs: List[JobOffer]) -> List[JobOffer]:
        """
        Supprime les doublons
        """
        seen_hashes = set()
        unique_jobs = []
        
        for job in jobs:
            # Hash basé sur titre + entreprise + lieu
            unique_string = f"{job.title.lower()}{job.company.lower()}{job.location.lower()}"
            job_hash = hashlib.md5(unique_string.encode()).hexdigest()
            
            if job_hash not in seen_hashes:
                seen_hashes.add(job_hash)
                unique_jobs.append(job)
        
        print(f"🔄 Déduplication: {len(jobs)} -> {len(unique_jobs)} offres uniques")
        return unique_jobs
    
    def run(self) -> List[Dict]:
        """
        Lance le processus de scraping complet via APIs
        """
        print("🎯 Démarrage du scraping API v2...")
        
        all_jobs = []
        
        # 1. Scraper via différentes sources API (SOURCES RÉELLES UNIQUEMENT)
        print("\n📊 Phase 1: Collecte via APIs réelles")
        print("=" * 40)
        
        # Adzuna API (principal - testé et fonctionnel)
        try:
            adzuna_jobs = self.scrape_adzuna_api()
            all_jobs.extend(adzuna_jobs)
            print(f"✅ Adzuna: {len(adzuna_jobs)} offres collectées")
        except Exception as e:
            print(f"⚠️ Adzuna API non disponible: {e}")
        
        # RapidAPI JSearch (testé avec vraies clés)
        try:
            rapidapi_jobs = self.scrape_rapidapi_jobs()
            all_jobs.extend(rapidapi_jobs)
            print(f"✅ RapidAPI: {len(rapidapi_jobs)} offres collectées")
        except Exception as e:
            print(f"⚠️ RapidAPI non disponible: {e}")
        
        # GitHub/Alternative APIs (Adzuna avec d'autres mots-clés)
        try:
            github_jobs = self.scrape_github_jobs()
            all_jobs.extend(github_jobs)
            print(f"✅ APIs alternatives: {len(github_jobs)} offres collectées")
        except Exception as e:
            print(f"⚠️ API alternative non disponible: {e}")
        
        # Indeed RSS DÉSACTIVÉ (bloqué par 403 Forbidden)
        print("❌ Indeed RSS: Désactivé (bloqué par Indeed - 403 Forbidden)")
        
        # FAKE STARTUPS DATA SUPPRIMÉ
        print("❌ Fake startup data: Supprimé (générait de fausses offres avec des liens cassés)")
        
        if not all_jobs:
            print("❌ Aucune offre trouvée via les APIs")
            return []
        
        # 2. Déduplication
        print("\n📊 Phase 2: Déduplication")
        print("=" * 40)
        
        unique_jobs = self.deduplicate_jobs(all_jobs)
        
        # 3. Calcul des scores
        print("\n📊 Phase 3: Calcul des scores de compatibilité")
        print("=" * 40)
        
        for job in unique_jobs:
            job.match_score = self.calculate_match_score(job)
        
        # 4. Tri par score
        unique_jobs.sort(key=lambda x: x.match_score, reverse=True)
        
        # Conversion en dictionnaires
        jobs_dict = []
        for job in unique_jobs:
            jobs_dict.append({
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'salary': job.salary,
                'description': job.description,
                'url': job.url,
                'source': job.source,
                'match_score': job.match_score,
                'scraped_at': job.scraped_at
            })
        
        # 5. Résultats
        print("\n📊 Phase 4: Résultats")
        print("=" * 40)
        
        print(f"💼 {len(jobs_dict)} offres trouvées au total")
        
        if jobs_dict:
            print(f"🏆 Meilleur score: {jobs_dict[0]['match_score']:.1f}%")
            
            # Sources
            sources = {}
            for job in jobs_dict:
                source = job['source']
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n📊 Répartition par source:")
            for source, count in sources.items():
                print(f"   {source}: {count} offres")
            
            # Top 5
            print(f"\n🎯 Top 5 des offres:")
            for i, job in enumerate(jobs_dict[:5], 1):
                print(f"{i}. {job['title']} chez {job['company']} "
                      f"({job['match_score']:.1f}%)")
        
        self.jobs_data = jobs_dict
        return jobs_dict
    
    def save_results(self, format_type: str = 'json') -> str:
        """
        Sauvegarde les résultats
        """
        if not self.jobs_data:
            return ""
        
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            filename = f"jobs_api_{timestamp}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Résultats sauvegardés dans {filepath}")
        return str(filepath)

def main():
    """
    Fonction principale du scraper API
    """
    try:
        print("🎯 API Job Scraper v2 - Scraping moderne")
        print("=" * 60)
        
        scraper = APIJobScraper()
        jobs = scraper.run()
        
        if jobs:
            scraper.save_results('json')
        
    except KeyboardInterrupt:
        print("\n❌ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        raise

if __name__ == "__main__":
    main()