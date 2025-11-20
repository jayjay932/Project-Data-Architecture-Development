#!/usr/bin/env python3
"""
Script d'installation automatique du Dashboard Immobilier Paris
Copie tous les fichiers depuis /outputs/ vers leur destination finale
"""

import os
import shutil
from pathlib import Path

# Mapping des fichiers : source → destination
FICHIERS = {
    # Documentation
    'ARCHITECTURE.md': 'docs/ARCHITECTURE.md',
    'README.md': 'README.md',
    'QUICKSTART.md': 'QUICKSTART.md',
    '.gitignore': '.gitignore',
    
    # Backend - Configuration
    'backend_requirements.txt': 'backend/requirements.txt',
    'backend_config.py': 'backend/config.py',
    'backend_app.py': 'backend/app.py',
    
    # Backend - Services
    'backend_data_loader.py': 'backend/services/data_loader.py',
    
    # Backend - Models
    'backend_model_arrondissement.py': 'backend/models/arrondissement.py',
    
    # Backend - Controllers
    'backend_controller_prix.py': 'backend/controllers/prix_controller.py',
    'backend_controller_logement.py': 'backend/controllers/logement_controller.py',
    'backend_controller_transport.py': 'backend/controllers/transport_controller.py',
    'backend_controller_pollution.py': 'backend/controllers/pollution_controller.py',
    
    # Backend - Views
    'backend_response_formatter.py': 'backend/views/response_formatter.py',
    
    # Backend - Middleware
    'backend_middleware_error_handler.py': 'backend/middleware/error_handler.py',
    
    # Frontend
    'frontend_index.html': 'frontend/index.html',
    'frontend_style.css': 'frontend/assets/css/style.css',
    'frontend_api.js': 'frontend/assets/js/api.js',
    'frontend_map.js': 'frontend/assets/js/map.js',
    'frontend_ui.js': 'frontend/assets/js/ui.js',
    'frontend_utils.js': 'frontend/assets/js/utils.js',
    'frontend_main.js': 'frontend/assets/js/main.js',
}

# Fichiers __init__.py à créer
INIT_FILES = [
    'backend/__init__.py',
    'backend/models/__init__.py',
    'backend/controllers/__init__.py',
    'backend/services/__init__.py',
    'backend/views/__init__.py',
    'backend/middleware/__init__.py',
    'backend/tests/__init__.py',
]

# Contenu des __init__.py
INIT_CONTENT = {
    'backend/models/__init__.py': '''"""Models package"""
from .arrondissement import Arrondissement

__all__ = ['Arrondissement']
''',
    'backend/controllers/__init__.py': '''"""Controllers package"""
from .prix_controller import prix_bp
from .logement_controller import logement_bp
from .transport_controller import transport_bp
from .pollution_controller import pollution_bp

__all__ = [
    'prix_bp',
    'logement_bp',
    'transport_bp',
    'pollution_bp'
]
''',
    'backend/services/__init__.py': '''"""Services package"""
from .data_loader import DataLoader, initialize_data_loader

__all__ = ['DataLoader', 'initialize_data_loader']
''',
    'backend/views/__init__.py': '''"""Views package"""
from .response_formatter import (
    format_response,
    format_error,
    format_not_found
)

__all__ = [
    'format_response',
    'format_error',
    'format_not_found'
]
''',
    'backend/middleware/__init__.py': '''"""Middleware package"""
from .error_handler import register_error_handlers

__all__ = ['register_error_handlers']
''',
}


def create_directory_structure():
    """Crée la structure de dossiers nécessaire"""
    print("📁 Création de la structure de dossiers...")
    
    directories = [
        'docs',
        'backend/models',
        'backend/controllers',
        'backend/services',
        'backend/views',
        'backend/middleware',
        'backend/tests',
        'frontend/assets/css',
        'frontend/assets/js',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}")
    
    print()


def copy_files(source_dir='/mnt/user-data/outputs'):
    """Copie tous les fichiers depuis le dossier source"""
    print("📋 Copie des fichiers...")
    
    source_path = Path(source_dir)
    copied = 0
    errors = 0
    
    for source_file, dest_file in FICHIERS.items():
        source = source_path / source_file
        dest = Path(dest_file)
        
        try:
            if source.exists():
                # Créer le dossier parent si nécessaire
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Copier le fichier
                shutil.copy2(source, dest)
                print(f"   ✓ {source_file} → {dest_file}")
                copied += 1
            else:
                print(f"   ⚠ {source_file} non trouvé")
                errors += 1
        except Exception as e:
            print(f"   ✗ Erreur lors de la copie de {source_file}: {e}")
            errors += 1
    
    print(f"\n   Fichiers copiés: {copied}/{len(FICHIERS)}")
    if errors > 0:
        print(f"   Erreurs: {errors}")
    print()


def create_init_files():
    """Crée les fichiers __init__.py"""
    print("🔧 Création des fichiers __init__.py...")
    
    for init_file in INIT_FILES:
        path = Path(init_file)
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Contenu personnalisé ou vide
            content = INIT_CONTENT.get(init_file, '"""Package initialization"""\n')
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✓ {init_file}")
        except Exception as e:
            print(f"   ✗ Erreur lors de la création de {init_file}: {e}")
    
    print()


def create_env_example():
    """Crée un fichier .env.example"""
    print("🔐 Création du fichier .env.example...")
    
    env_content = '''# Configuration Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=change-this-in-production

# CORS
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO

# Port (optionnel)
PORT=5000
'''
    
    try:
        with open('backend/.env.example', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("   ✓ backend/.env.example créé")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
    
    print()


def verify_installation():
    """Vérifie que tous les fichiers sont en place"""
    print("✅ Vérification de l'installation...")
    
    all_ok = True
    
    # Vérifier les fichiers principaux
    critical_files = [
        'backend/app.py',
        'backend/config.py',
        'backend/requirements.txt',
        'frontend/index.html',
        'README.md',
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} MANQUANT")
            all_ok = False
    
    print()
    
    if all_ok:
        print("🎉 Installation terminée avec succès !")
        print("\n📖 Prochaines étapes:")
        print("   1. Installer les dépendances: cd backend && pip install -r requirements.txt")
        print("   2. Lancer le backend: python app.py")
        print("   3. Lancer le frontend: cd frontend && python -m http.server 8000")
        print("   4. Ouvrir http://localhost:8000 dans votre navigateur")
    else:
        print("⚠️  Installation incomplète. Vérifiez les fichiers manquants.")
    
    return all_ok


def main():
    """Fonction principale"""
    print("=" * 70)
    print("  INSTALLATION DU DASHBOARD IMMOBILIER PARIS")
    print("=" * 70)
    print()
    
    # Vérifier qu'on est dans le bon dossier
    if not Path('data').exists():
        print("⚠️  Attention : Le dossier 'data' n'existe pas.")
        print("   Assurez-vous d'exécuter ce script depuis la racine du projet.")
        response = input("\n   Continuer quand même ? (o/N) ")
        if response.lower() != 'o':
            print("   Installation annulée.")
            return
        print()
    
    # Étapes d'installation
    try:
        create_directory_structure()
        copy_files()
        create_init_files()
        create_env_example()
        verify_installation()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")


if __name__ == '__main__':
    main()
