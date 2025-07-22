#!/usr/bin/env python3
"""
Interface web pour le Job Ad Scraper
Application Flask avec SQLite pour gérer le scraping d'emploi
"""

import os
import json
import yaml
import time
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# Import du nouveau scraper API
try:
    from api_scraper import APIJobScraper
    SCRAPER_CLASS = APIJobScraper
    print("✅ Utilisation du nouveau scraper API")
except ImportError:
    from main import EnhancedJobScraper
    SCRAPER_CLASS = EnhancedJobScraper
    print("⚠️ Fallback sur l'ancien scraper Selenium")

app = Flask(__name__)
app.secret_key = 'job_scraper_secret_key_change_me'

# Configuration
DATABASE_PATH = 'jobs.db'
SCRAPER_STATUS = {
    'running': False,
    'progress': 0,
    'current_task': '',
    'start_time': None,
    'end_time': None,
    'total_jobs': 0,
    'error': None
}

# Log buffer pour la console en temps réel
CONSOLE_LOGS = []
MAX_CONSOLE_LOGS = 100

def add_console_log(level: str, message: str):
    """
    Ajoute un log à la console en temps réel
    
    Args:
        level (str): Niveau du log (info, success, error, warning)
        message (str): Message du log
    """
    global CONSOLE_LOGS
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    
    CONSOLE_LOGS.append(log_entry)
    
    # Limiter le nombre de logs en mémoire
    if len(CONSOLE_LOGS) > MAX_CONSOLE_LOGS:
        CONSOLE_LOGS.pop(0)
    
    # Afficher aussi dans la console serveur
    print(f"[{timestamp}] {level.upper()}: {message}")

class DatabaseManager:
    """
    Gestionnaire de base de données SQLite
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialise le gestionnaire de base de données
        
        Args:
            db_path (str): Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        Initialise la base de données avec les tables nécessaires
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table des offres d'emploi
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    description TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    match_score REAL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des sessions de scraping
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    total_jobs INTEGER,
                    unique_jobs INTEGER,
                    status TEXT,
                    error_message TEXT,
                    config_snapshot TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index pour optimiser les requêtes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_date ON scraping_sessions(created_at DESC)')
            
            conn.commit()
    
    def save_job(self, job_data: dict) -> int:
        """
        Sauvegarde une offre d'emploi dans la base de données
        
        Args:
            job_data (dict): Données de l'offre
            
        Returns:
            int: ID de l'offre sauvegardée
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (title, company, location, salary, description, url, source, match_score, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('salary', ''),
                job_data.get('description', ''),
                job_data.get('url', ''),
                job_data.get('source', ''),
                job_data.get('match_score', 0.0),
                job_data.get('scraped_at', datetime.now().isoformat())
            ))
            
            return cursor.lastrowid
    
    def get_jobs(self, limit: int = 100, offset: int = 0, min_score: float = 0) -> list:
        """
        Récupère les offres d'emploi de la base de données
        
        Args:
            limit (int): Nombre maximum d'offres à récupérer
            offset (int): Décalage pour la pagination
            min_score (float): Score minimum de compatibilité
            
        Returns:
            list: Liste des offres d'emploi
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE match_score >= ? 
                ORDER BY match_score DESC, created_at DESC 
                LIMIT ? OFFSET ?
            ''', (min_score, limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_job_stats(self) -> dict:
        """
        Récupère les statistiques des offres d'emploi
        
        Returns:
            dict: Statistiques
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute('SELECT COUNT(*) as total FROM jobs')
            total_jobs = cursor.fetchone()['total']
            
            cursor.execute('SELECT AVG(match_score) as avg_score FROM jobs')
            avg_score = cursor.fetchone()['avg_score'] or 0
            
            cursor.execute('SELECT COUNT(DISTINCT company) as unique_companies FROM jobs')
            unique_companies = cursor.fetchone()['unique_companies']
            
            cursor.execute('SELECT COUNT(DISTINCT source) as unique_sources FROM jobs')
            unique_sources = cursor.fetchone()['unique_sources']
            
            # Top entreprises
            cursor.execute('''
                SELECT company, COUNT(*) as count 
                FROM jobs 
                GROUP BY company 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_companies = [dict(row) for row in cursor.fetchall()]
            
            # Top sources
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM jobs 
                GROUP BY source 
                ORDER BY count DESC
            ''')
            top_sources = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_jobs': total_jobs,
                'avg_score': round(avg_score, 1),
                'unique_companies': unique_companies,
                'unique_sources': unique_sources,
                'top_companies': top_companies,
                'top_sources': top_sources
            }
    
    def save_scraping_session(self, session_data: dict) -> int:
        """
        Sauvegarde une session de scraping
        
        Args:
            session_data (dict): Données de la session
            
        Returns:
            int: ID de la session sauvegardée
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scraping_sessions 
                (start_time, end_time, duration_seconds, total_jobs, unique_jobs, status, error_message, config_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data.get('start_time'),
                session_data.get('end_time'),
                session_data.get('duration_seconds'),
                session_data.get('total_jobs', 0),
                session_data.get('unique_jobs', 0),
                session_data.get('status', 'completed'),
                session_data.get('error_message'),
                json.dumps(session_data.get('config_snapshot', {}))
            ))
            
            return cursor.lastrowid
    
    def get_scraping_sessions(self, limit: int = 20) -> list:
        """
        Récupère l'historique des sessions de scraping
        
        Args:
            limit (int): Nombre maximum de sessions à récupérer
            
        Returns:
            list: Liste des sessions
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM scraping_sessions 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]

# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()

class APIWebScraper:
    """
    Version web du nouveau scraper API avec base de données et callbacks
    """
    
    def __init__(self, config_path: str = "config.yaml", progress_callback=None):
        """
        Initialise le scraper web API
        
        Args:
            config_path (str): Chemin vers la configuration
            progress_callback (callable): Callback pour les mises à jour de progression
        """
        self.api_scraper = SCRAPER_CLASS(config_path)
        self.progress_callback = progress_callback
        self.session_start_time = None
        self.session_data = {}
        
        # Clear console logs at start
        global CONSOLE_LOGS
        CONSOLE_LOGS.clear()
    
    def update_progress(self, progress: int, task: str):
        """
        Met à jour la progression du scraping
        
        Args:
            progress (int): Progression en pourcentage
            task (str): Tâche en cours
        """
        SCRAPER_STATUS['progress'] = progress
        SCRAPER_STATUS['current_task'] = task
        
        # Log détaillé pour la console dashboard
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {progress:3d}% | {task}")
        
        if self.progress_callback:
            self.progress_callback(progress, task)
    
    def run_with_database(self):
        """
        Lance le scraping API avec sauvegarde en base de données
        """
        global SCRAPER_STATUS
        
        try:
            SCRAPER_STATUS['running'] = True
            SCRAPER_STATUS['start_time'] = datetime.now()
            SCRAPER_STATUS['progress'] = 0
            SCRAPER_STATUS['error'] = None
            
            self.session_start_time = datetime.now()
            self.session_data = {
                'start_time': self.session_start_time.isoformat(),
                'config_snapshot': self.api_scraper.config,
                'status': 'running'
            }
            
            self.update_progress(5, "🔧 Chargement de la configuration...")
            add_console_log('info', '🔧 Chargement de la configuration sécurisée...')
            add_console_log('info', f'📍 Localisations configurées: {", ".join(self.api_scraper.config["search_criteria"]["locations"][:3])}...')
            add_console_log('info', f'🔍 {len(self.api_scraper.config["search_criteria"]["keywords"])} mots-clés configurés')
            time.sleep(1)
            
            self.update_progress(10, "🚀 Initialisation du scraper API...")
            add_console_log('success', '🚀 Scraper API initialisé avec succès')
            add_console_log('info', '🌐 Mode: APIs publiques + scraping léger RSS')
            time.sleep(1)
            
            # Phase 1: Scraping Indeed RSS
            self.update_progress(15, "📡 Recherche via Indeed RSS...")
            add_console_log('info', '📡 Démarrage des requêtes Indeed RSS...')
            indeed_jobs = self.api_scraper.scrape_indeed_rss()
            
            self.update_progress(30, f"✅ Indeed: {len(indeed_jobs)} offres trouvées")
            add_console_log('success', f'📊 Indeed RSS: {len(indeed_jobs)} offres collectées')
            
            # Phase 2: APIs alternatives
            self.update_progress(40, "🔍 Recherche via APIs alternatives...")
            add_console_log('info', '🔍 Recherche via APIs alternatives (Adzuna)...')
            try:
                github_jobs = self.api_scraper.scrape_github_jobs()
                self.update_progress(55, f"✅ APIs: {len(github_jobs)} offres trouvées")
                add_console_log('success', f'📊 APIs alternatives: {len(github_jobs)} offres collectées')
            except Exception as e:
                add_console_log('warning', f'⚠️ APIs alternatives non disponibles: {e}')
                github_jobs = []
            
            self.update_progress(60, "🚀 Recherche startups et entreprises...")
            add_console_log('info', '🚀 Collecte d\'offres startups et entreprises locales...')
            try:
                startup_jobs = self.api_scraper.scrape_startups_jobs()
                self.update_progress(70, f"✅ Startups: {len(startup_jobs)} offres trouvées")
                add_console_log('success', f'📊 Startups: {len(startup_jobs)} offres collectées')
            except Exception as e:
                add_console_log('warning', f'⚠️ Startups non disponibles: {e}')
                startup_jobs = []
            
            self.update_progress(75, "🔄 Combinaison des résultats...")
            add_console_log('info', '🔄 Combinaison et analyse des résultats...')
            
            # Combinaison des résultats
            all_jobs = indeed_jobs + github_jobs + startup_jobs
            add_console_log('info', f'📊 Total brut: {len(all_jobs)} offres collectées')
            
            if not all_jobs:
                add_console_log('error', '❌ Aucune offre trouvée via les APIs')
                raise Exception("❌ Aucune offre trouvée via les APIs")
            
            self.update_progress(80, f"🔄 Déduplication de {len(all_jobs)} offres...")
            add_console_log('info', f'🔄 Déduplication de {len(all_jobs)} offres...')
            unique_jobs = self.api_scraper.deduplicate_jobs(all_jobs)
            add_console_log('success', f'✅ {len(unique_jobs)} offres uniques après déduplication')
            
            self.update_progress(85, "📊 Calcul des scores de compatibilité...")
            add_console_log('info', '📊 Calcul des scores de pertinence...')
            add_console_log('info', '🎯 Critères: Compétences (40%) + Localisation (30%) + Télétravail (15%) + Source (15%)')
            
            # Sauvegarde en base et calcul des scores
            saved_count = 0
            print(f"\n📊 ANALYSE DE PERTINENCE DES OFFRES")
            print("=" * 50)
            
            for i, job in enumerate(unique_jobs, 1):
                # Analyse détaillée pour les 5 meilleures offres potentielles
                verbose = i <= 5
                job.match_score = self.api_scraper.calculate_match_score(job, verbose=verbose)
                
                if verbose:
                    add_console_log('info', f'📊 Analyse #{i}: {job.title} | {job.company} → {job.match_score:.1f}%')
                    print(f"\n{'='*50}")
                
                # Conversion en dict pour la base de données
                job_dict = {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'salary': job.salary,
                    'description': job.description,
                    'url': job.url,
                    'source': job.source,
                    'match_score': job.match_score,
                    'scraped_at': job.scraped_at
                }
                
                try:
                    db_manager.save_job(job_dict)
                    saved_count += 1
                except Exception as e:
                    # Ignorer les doublons (contrainte UNIQUE)
                    if "UNIQUE constraint failed" not in str(e):
                        print(f"⚠️ Erreur sauvegarde: {e}")
            
            self.update_progress(95, f"💾 {saved_count} nouvelles offres sauvegardées")
            add_console_log('success', f'💾 {saved_count} nouvelles offres sauvegardées en base')
            
            # Tri par score
            unique_jobs.sort(key=lambda x: x.match_score, reverse=True)
            
            # Affichage du résumé final
            print(f"\n🎯 RÉSUMÉ FINAL DU SCRAPING")
            print("=" * 50)
            print(f"📊 Total des offres trouvées: {len(all_jobs)}")
            print(f"🔄 Offres uniques après déduplication: {len(unique_jobs)}")
            print(f"💾 Nouvelles offres sauvegardées: {saved_count}")
            
            if unique_jobs:
                add_console_log('success', f'🏆 TOP 5 DES MEILLEURES OFFRES:')
                print(f"\n🏆 TOP 5 DES MEILLEURES OFFRES:")
                for i, job in enumerate(unique_jobs[:5], 1):
                    print(f"  {i}. {job.title} | {job.company} | {job.match_score:.1f}%")
                    print(f"     🔗 {job.url}")
                    add_console_log('info', f'  {i}. {job.title} | {job.company} | {job.match_score:.1f}%')
                
                # Statistiques des scores
                scores = [job.match_score for job in unique_jobs]
                high_scores = len([s for s in scores if s >= 80])
                medium_scores = len([s for s in scores if 60 <= s < 80])
                low_scores = len([s for s in scores if s < 60])
                
                print(f"\n📊 RÉPARTITION DES SCORES:")
                print(f"  🟢 Excellent (≥80%): {high_scores} offres")
                print(f"  🟡 Bon (60-79%): {medium_scores} offres")
                print(f"  🔴 Faible (<60%): {low_scores} offres")
                
                add_console_log('info', f'📊 Répartition: {high_scores} excellentes (≥80%), {medium_scores} bonnes (60-79%), {low_scores} faibles (<60%)')
            
            # Sauvegarde de la session
            session_end_time = datetime.now()
            duration = (session_end_time - self.session_start_time).total_seconds()
            
            self.session_data.update({
                'end_time': session_end_time.isoformat(),
                'duration_seconds': int(duration),
                'total_jobs': len(all_jobs),
                'unique_jobs': len(unique_jobs),
                'status': 'completed'
            })
            
            db_manager.save_scraping_session(self.session_data)
            
            SCRAPER_STATUS['total_jobs'] = len(unique_jobs)
            SCRAPER_STATUS['end_time'] = session_end_time
            duration_str = f"{int(duration//60)}min {int(duration%60)}s"
            
            if unique_jobs:
                best_score = unique_jobs[0].match_score
                self.update_progress(100, f"🎉 Terminé ! {len(unique_jobs)} offres (meilleur score: {best_score:.1f}%) en {duration_str}")
                add_console_log('success', f'🎉 SCRAPING TERMINÉ avec succès !')
                add_console_log('info', f'⏱️ Durée: {duration_str} | 🏆 Meilleur score: {best_score:.1f}%')
            else:
                self.update_progress(100, f"✅ Terminé en {duration_str} - Aucune nouvelle offre")
                add_console_log('info', f'✅ Scraping terminé en {duration_str} - Aucune nouvelle offre')
            
        except Exception as e:
            SCRAPER_STATUS['error'] = str(e)
            SCRAPER_STATUS['progress'] = 0  # Reset progress on error
            add_console_log('error', f'❌ ERREUR CRITIQUE: {str(e)}')
            add_console_log('error', f'💥 Le scraping a été interrompu')
            self.session_data.update({
                'end_time': datetime.now().isoformat(),
                'status': 'error',
                'error_message': str(e)
            })
            db_manager.save_scraping_session(self.session_data)
            self.update_progress(0, f"❌ Erreur: {str(e)}")
        
        finally:
            SCRAPER_STATUS['running'] = False
            # Si aucune erreur n'a été définie, s'assurer que l'état final est correct
            if SCRAPER_STATUS['progress'] == 100 and not SCRAPER_STATUS['error']:
                SCRAPER_STATUS['current_task'] = 'Terminé'
            elif SCRAPER_STATUS['error']:
                SCRAPER_STATUS['current_task'] = f"Erreur: {SCRAPER_STATUS['error']}"

# Routes Flask
@app.route('/')
def index():
    """
    Page d'accueil avec tableau de bord
    """
    stats = db_manager.get_job_stats()
    recent_jobs = db_manager.get_jobs(limit=5)
    recent_sessions = db_manager.get_scraping_sessions(limit=5)
    
    return render_template('index.html', 
                         stats=stats, 
                         recent_jobs=recent_jobs,
                         recent_sessions=recent_sessions,
                         scraper_status=SCRAPER_STATUS)

@app.route('/jobs')
def jobs():
    """
    Page des offres d'emploi
    """
    page = request.args.get('page', 1, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    per_page = 20
    
    jobs_list = db_manager.get_jobs(
        limit=per_page, 
        offset=(page-1)*per_page,
        min_score=min_score
    )
    
    return render_template('jobs.html', 
                         jobs=jobs_list,
                         page=page,
                         min_score=min_score,
                         scraper_status=SCRAPER_STATUS)

@app.route('/config')
def config():
    """
    Page de configuration
    """
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config_content = f.read()
            config_data = yaml.safe_load(config_content)
    except Exception as e:
        flash(f'Erreur lors du chargement de la configuration: {e}', 'error')
        config_content = ""
        config_data = {}
    
    return render_template('config.html', 
                         config_content=config_content,
                         config_data=config_data,
                         scraper_status=SCRAPER_STATUS)

@app.route('/config/save', methods=['POST'])
def save_config():
    """
    Sauvegarde de la configuration
    """
    try:
        config_content = request.form.get('config_content')
        
        # Validation YAML
        yaml.safe_load(config_content)
        
        # Sauvegarde
        with open('config.yaml', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        flash('Configuration sauvegardée avec succès!', 'success')
        
    except yaml.YAMLError as e:
        flash(f'Erreur YAML: {e}', 'error')
    except Exception as e:
        flash(f'Erreur lors de la sauvegarde: {e}', 'error')
    
    return redirect(url_for('config'))

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """
    Lance le scraping en arrière-plan
    """
    if SCRAPER_STATUS['running']:
        return jsonify({'error': 'Le scraping est déjà en cours'})
    
    def run_scraper():
        scraper = APIWebScraper()
        scraper.run_with_database()
    
    # Lancement en thread séparé
    scraper_thread = threading.Thread(target=run_scraper)
    scraper_thread.daemon = True
    scraper_thread.start()
    
    return jsonify({'message': 'Scraping démarré'})

@app.route('/scraping_status')
def scraping_status():
    """
    API pour récupérer le statut du scraping
    """
    return jsonify(SCRAPER_STATUS)

@app.route('/console_logs')
def console_logs():
    """
    API pour récupérer les logs de console en temps réel
    """
    return jsonify({
        'logs': CONSOLE_LOGS,
        'total': len(CONSOLE_LOGS)
    })

@app.route('/sessions')
def sessions():
    """
    Page de l'historique des sessions
    """
    sessions_list = db_manager.get_scraping_sessions()
    return render_template('sessions.html', sessions=sessions_list, scraper_status=SCRAPER_STATUS)

@app.route('/api/jobs')
def api_jobs():
    """
    API REST pour récupérer les offres d'emploi
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    
    jobs_list = db_manager.get_jobs(
        limit=per_page,
        offset=(page-1)*per_page,
        min_score=min_score
    )
    
    return jsonify({
        'jobs': jobs_list,
        'page': page,
        'per_page': per_page,
        'min_score': min_score
    })

if __name__ == '__main__':
    # Création du dossier templates s'il n'existe pas
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    
    print("🌐 Interface web du Job Scraper")
    print("=" * 40)
    print("📱 Accès: http://localhost:8080")
    print("🔧 Configuration: http://localhost:8080/config")
    print("💼 Offres: http://localhost:8080/jobs")
    print("📊 Sessions: http://localhost:8080/sessions")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=8080)