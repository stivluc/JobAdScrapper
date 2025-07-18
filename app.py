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

# Import du scraper
from main import EnhancedJobScraper

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

class WebScraper(EnhancedJobScraper):
    """
    Version web du scraper avec base de données et callbacks
    """
    
    def __init__(self, config_path: str = "config.yaml", progress_callback=None):
        """
        Initialise le scraper web
        
        Args:
            config_path (str): Chemin vers la configuration
            progress_callback (callable): Callback pour les mises à jour de progression
        """
        super().__init__(config_path)
        self.progress_callback = progress_callback
        self.session_start_time = None
        self.session_data = {}
    
    def update_progress(self, progress: int, task: str):
        """
        Met à jour la progression du scraping
        
        Args:
            progress (int): Progression en pourcentage
            task (str): Tâche en cours
        """
        SCRAPER_STATUS['progress'] = progress
        SCRAPER_STATUS['current_task'] = task
        
        if self.progress_callback:
            self.progress_callback(progress, task)
    
    def run_with_database(self):
        """
        Lance le scraping avec sauvegarde en base de données
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
                'config_snapshot': self.config,
                'status': 'running'
            }
            
            self.update_progress(10, "Initialisation du scraping...")
            
            # Phase 1: Recherche Google
            self.update_progress(20, "Recherche Google en cours...")
            job_urls = self.google_searcher.search_all_queries()
            
            if not job_urls:
                raise Exception("Aucune URL trouvée via Google")
            
            self.update_progress(40, f"Scraping de {len(job_urls)} offres...")
            
            # Phase 2: Scraping des offres
            max_jobs = self.config['scraper_settings'].get('max_jobs_total', 100)
            jobs_to_process = job_urls[:max_jobs]
            
            scraped_jobs = []
            total_jobs = len(jobs_to_process)
            
            for i, url in enumerate(jobs_to_process):
                progress = 40 + int((i / total_jobs) * 40)
                self.update_progress(progress, f"Scraping offre {i+1}/{total_jobs}")
                
                job_data = self.site_scraper.scrape_job_url(url)
                
                if job_data:
                    job_data['match_score'] = self.calculate_match_score(job_data)
                    scraped_jobs.append(job_data)
                    
                    # Sauvegarde en base de données
                    db_manager.save_job(job_data)
                
                time.sleep(1)  # Délai entre les requêtes
            
            self.update_progress(85, "Déduplication des offres...")
            
            # Phase 3: Déduplication (déjà gérée par SQLite UNIQUE)
            unique_jobs = scraped_jobs
            
            self.update_progress(95, "Finalisation...")
            
            # Sauvegarde de la session
            session_end_time = datetime.now()
            duration = (session_end_time - self.session_start_time).total_seconds()
            
            self.session_data.update({
                'end_time': session_end_time.isoformat(),
                'duration_seconds': int(duration),
                'total_jobs': len(scraped_jobs),
                'unique_jobs': len(unique_jobs),
                'status': 'completed'
            })
            
            db_manager.save_scraping_session(self.session_data)
            
            SCRAPER_STATUS['total_jobs'] = len(unique_jobs)
            SCRAPER_STATUS['end_time'] = session_end_time
            self.update_progress(100, f"Terminé ! {len(unique_jobs)} offres trouvées")
            
        except Exception as e:
            SCRAPER_STATUS['error'] = str(e)
            self.session_data.update({
                'end_time': datetime.now().isoformat(),
                'status': 'error',
                'error_message': str(e)
            })
            db_manager.save_scraping_session(self.session_data)
            self.update_progress(0, f"Erreur: {str(e)}")
        
        finally:
            SCRAPER_STATUS['running'] = False

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
        scraper = WebScraper()
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
    print("📱 Accès: http://localhost:5000")
    print("🔧 Configuration: http://localhost:5000/config")
    print("💼 Offres: http://localhost:5000/jobs")
    print("📊 Sessions: http://localhost:5000/sessions")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=5000)