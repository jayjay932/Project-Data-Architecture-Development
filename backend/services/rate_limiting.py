"""
Rate Limiting — Urban Data Explorer (C2.1)
===========================================
Ajoute des quotas et limitations de débit sur l'API
pour démontrer le critère C2.1 :
"Les autorisations et les quotas imposés aux utilisateurs
de l'API sont faciles à comprendre et à intégrer."

Règles appliquées :
    - Global          : 200 requêtes/minute
    - /api/auth/login : 5 tentatives/minute (anti brute-force)
    - /api/arrondissements/* : 60 requêtes/minute
    - /api/prix/*     : 60 requêtes/minute
    - /api/stats      : 10 requêtes/minute

Usage :
    pip install flask-limiter
    Intégrer dans app.py (voir instructions ci-dessous)
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ── Initialisation du limiter ────────────────────────────────
# get_remote_address : identifie le client par son IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://"
)


def init_rate_limiting(app):
    """
    Initialise le rate limiting sur l'application Flask.
    À appeler dans create_app() après la création de l'app.

    Règles :
        - Limite globale : 200 req/min par IP
        - Login : 5 req/min (protection brute-force)
        - Endpoints data : 60 req/min
        - Stats : 10 req/min
    """
    limiter.init_app(app)

    # Message d'erreur personnalisé quand la limite est dépassée
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        from flask import jsonify
        return jsonify({
            "success": False,
            "error": {
                "message": "Trop de requêtes. Quota dépassé.",
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": "Réessayez dans 60 secondes",
                "limits": {
                    "global": "200 requêtes/minute",
                    "login": "5 tentatives/minute",
                    "data": "60 requêtes/minute"
                }
            }
        }), 429

    return limiter


# ── Décorateurs à appliquer sur les routes ───────────────────
# Usage dans les controllers :
#
# from services.rate_limiting import limiter
#
# @auth_bp.route('/login', methods=['POST'])
# @limiter.limit("5 per minute")   ← anti brute-force
# def login():
#     ...
#
# @prix_bp.route('/m2/<int:arrondissement>')
# @limiter.limit("60 per minute")
# def get_prix_m2():
#     ...
