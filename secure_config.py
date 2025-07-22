#!/usr/bin/env python3
"""
Configuration sécurisée pour le Job Scraper
Gestion des clés API et variables sensibles
"""

import os
import yaml
from typing import Dict, Optional
from pathlib import Path

class SecureConfig:
    """
    Gestionnaire de configuration sécurisé
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialise la configuration sécurisée
        
        Args:
            config_path (str): Chemin vers config.yaml
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.load_env_variables()
    
    def load_config(self) -> Dict:
        """
        Charge la configuration depuis config.yaml
        
        Returns:
            Dict: Configuration chargée
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                return config
        except Exception as e:
            print(f"❌ Erreur chargement configuration: {e}")
            raise
    
    def load_env_variables(self):
        """
        Charge les variables d'environnement depuis .env si disponible
        """
        env_path = Path('.env')
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                print("✅ Variables d'environnement chargées depuis .env")
            except Exception as e:
                print(f"⚠️ Erreur chargement .env: {e}")
        else:
            print("ℹ️ Fichier .env non trouvé - utilisation des variables système")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Récupère une clé API de façon sécurisée
        
        Args:
            service (str): Nom du service (adzuna, rapidapi, etc.)
            
        Returns:
            Optional[str]: Clé API ou None si non disponible
        """
        key_mappings = {
            'adzuna_app_id': 'ADZUNA_APP_ID',
            'adzuna_app_key': 'ADZUNA_APP_KEY',
            'rapidapi_key': 'RAPIDAPI_KEY',
            'rapidapi_app': 'RAPIDAPI_APP',
            'rapidapi': 'RAPIDAPI_KEY',  # Backward compatibility
            'github': 'GITHUB_TOKEN',
            'linkedin': 'LINKEDIN_API_KEY'
        }
        
        env_var = key_mappings.get(service.lower())
        if env_var:
            return os.environ.get(env_var)
        
        return None
    
    def has_api_key(self, service: str) -> bool:
        """
        Vérifie si une clé API est disponible
        
        Args:
            service (str): Nom du service
            
        Returns:
            bool: True si la clé est disponible
        """
        key = self.get_api_key(service)
        return key is not None and key.strip() != ''
    
    def get_search_locations(self) -> Dict:
        """
        Récupère les localisations configurées dynamiquement
        
        Returns:
            Dict: Mapping des localisations par pays
        """
        locations = self.config['search_criteria']['locations']
        
        # Mapping intelligent basé sur config.yaml
        location_mapping = {
            'switzerland': [],
            'france': [],
            'remote': []
        }
        
        for location in locations:
            location_lower = location.lower()
            
            # Détection automatique du pays
            if any(swiss in location_lower for swiss in ['suisse', 'switzerland', 'genève', 'geneva', 'lausanne', 'zurich', 'berne', 'vaud', 'fribourg', 'neuchâtel', 'jura', 'valais']):
                if 'genève' in location_lower or 'geneva' in location_lower:
                    location_mapping['switzerland'].append('geneva')
                elif 'lausanne' in location_lower:
                    location_mapping['switzerland'].append('lausanne')
                elif 'zurich' in location_lower:
                    location_mapping['switzerland'].append('zurich')
                else:
                    location_mapping['switzerland'].append('switzerland')
            
            elif any(french in location_lower for french in ['france', 'lille', 'paris', 'lyon', 'marseille', 'toulouse', 'nord']):
                if 'lille' in location_lower:
                    location_mapping['france'].append('lille')
                elif 'paris' in location_lower:
                    location_mapping['france'].append('paris')
                elif 'lyon' in location_lower:
                    location_mapping['france'].append('lyon')
                else:
                    location_mapping['france'].append('france')
            
            elif any(remote in location_lower for remote in ['télétravail', 'remote', 'distance', 'full remote']):
                location_mapping['remote'].append('remote')
        
        # Suppression des doublons
        for country in location_mapping:
            location_mapping[country] = list(set(location_mapping[country]))
            
        # Si aucune localisation n'est détectée, utiliser des valeurs par défaut
        if not any(location_mapping.values()):
            location_mapping = {
                'switzerland': ['geneva', 'lausanne'],
                'france': ['lille', 'paris'],
                'remote': ['remote']
            }
            
        return location_mapping
    
    def get_search_config(self) -> Dict:
        """
        Récupère la configuration de recherche complète
        
        Returns:
            Dict: Configuration de recherche adaptée
        """
        return {
            'keywords': self.config['search_criteria']['keywords'],
            'locations': self.get_search_locations(),
            'skills': self.config['user_profile']['skills'],
            'experience_years': self.config['user_profile'].get('experience_years', 0),
            'salary_min': self.config['search_criteria'].get('salary_min', 0),
            'salary_max': self.config['search_criteria'].get('salary_max', 999999),
            'remote_ok': self.config['search_criteria'].get('remote_ok', True),
            'scraper_settings': self.config.get('scraper_settings', {})
        }
    
    def get_flask_config(self) -> Dict:
        """
        Configuration Flask sécurisée
        
        Returns:
            Dict: Configuration Flask
        """
        return {
            'SECRET_KEY': os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production'),
            'DEBUG': os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
        }
    
    def create_sample_env(self):
        """
        Crée un fichier .env d'exemple si il n'existe pas
        """
        env_path = Path('.env')
        example_path = Path('.env.example')
        
        if not env_path.exists() and example_path.exists():
            try:
                # Copier l'exemple vers .env
                with open(example_path, 'r') as example:
                    content = example.read()
                
                with open(env_path, 'w') as env_file:
                    env_file.write(content)
                
                print("✅ Fichier .env créé depuis .env.example")
                print("⚠️ IMPORTANT: Éditez .env avec vos vraies clés API")
                
            except Exception as e:
                print(f"⚠️ Erreur création .env: {e}")

# Instance globale
secure_config = SecureConfig()

# Fonctions d'aide pour compatibilité
def get_api_key(service: str) -> Optional[str]:
    """Helper function pour récupérer les clés API"""
    return secure_config.get_api_key(service)

def has_api_key(service: str) -> bool:
    """Helper function pour vérifier les clés API"""
    return secure_config.has_api_key(service)

def get_search_config() -> Dict:
    """Helper function pour la configuration de recherche"""
    return secure_config.get_search_config()