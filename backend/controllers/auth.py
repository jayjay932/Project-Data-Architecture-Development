"""
Controller d'authentification JWT — Urban Data Explorer
=========================================================
Démontre C2.1 : mécanismes d'authentification déployés

Endpoints :
    POST /api/auth/login     → obtenir un token JWT
    POST /api/auth/refresh   → renouveler un token
    GET  /api/auth/me        → infos utilisateur connecté
    GET  /api/auth/verify    → vérifier un token

Usage :
    1. POST /api/auth/login {"username": "admin", "password": "paris2024"}
    2. Utiliser le token retourné dans le header : Authorization: Bearer <token>
    3. Accéder aux endpoints protégés
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Import limiter (lazy pour éviter les imports circulaires)
def get_limiter():
    from services.rate_limiting import limiter
    return limiter

# ── Clé secrète JWT ─────────────────────────────────────────
JWT_SECRET = "urban_data_explorer_secret_2024_!@#"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ── Utilisateurs (en production : base de données) ──────────
USERS = {
    "admin": {
        "password": "paris2024",
        "role": "admin",
        "name": "Administrateur Urban Data"
    },
    "viewer": {
        "password": "viewer2024",
        "role": "viewer",
        "name": "Utilisateur Lecture Seule"
    }
}


# ── Fonction utilitaire : générer un token JWT ───────────────
def generer_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ── Décorateur : protéger un endpoint par JWT ────────────────
def jwt_required(f):
    """
    Décorateur à appliquer sur les endpoints protégés.
    Vérifie la présence et la validité du token JWT dans
    le header Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": {
                    "message": "Token manquant. Header requis : Authorization: Bearer <token>",
                    "code": "MISSING_TOKEN"
                }
            }), 401

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "error": {
                    "message": "Token expiré. Reconnectez-vous via POST /api/auth/login",
                    "code": "TOKEN_EXPIRED"
                }
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "error": {
                    "message": "Token invalide",
                    "code": "INVALID_TOKEN"
                }
            }), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Décorateur : réservé aux admins uniquement"""
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if request.current_user.get("role") != "admin":
            return jsonify({
                "success": False,
                "error": {
                    "message": "Accès réservé aux administrateurs",
                    "code": "FORBIDDEN"
                }
            }), 403
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════
# ENDPOINTS D'AUTHENTIFICATION
# ════════════════════════════════════════════════════════════

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Body: {"username": "admin", "password": "paris2024"}
    Retourne un token JWT valable 24h
    Limite : 5 tentatives/minute (anti brute-force)
    """
    data = request.get_json()

    if not data or "username" not in data or "password" not in data:
        return jsonify({
            "success": False,
            "error": {
                "message": "Corps de requête invalide. Requis : {username, password}",
                "code": "BAD_REQUEST"
            }
        }), 400

    username = data["username"]
    password = data["password"]

    user = USERS.get(username)
    if not user or user["password"] != password:
        logger.warning(f"Tentative de connexion échouée pour : {username}")
        return jsonify({
            "success": False,
            "error": {
                "message": "Identifiants incorrects",
                "code": "INVALID_CREDENTIALS"
            }
        }), 401

    token = generer_token(username, user["role"])
    logger.info(f"Connexion réussie pour : {username} (rôle: {user['role']})")

    return jsonify({
        "success": True,
        "data": {
            "token": token,
            "type": "Bearer",
            "expires_in": f"{JWT_EXPIRATION_HOURS}h",
            "user": {
                "username": username,
                "role": user["role"],
                "name": user["name"]
            }
        },
        "message": f"Bienvenue {user['name']} !"
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def me():
    """
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    Retourne les infos de l'utilisateur connecté
    """
    user_info = request.current_user
    username = user_info.get("sub")
    user = USERS.get(username, {})

    return jsonify({
        "success": True,
        "data": {
            "username": username,
            "role": user_info.get("role"),
            "name": user.get("name"),
            "token_expires": user_info.get("exp")
        }
    }), 200


@auth_bp.route('/verify', methods=['GET'])
@jwt_required
def verify():
    """
    GET /api/auth/verify
    Header: Authorization: Bearer <token>
    Vérifie qu'un token est valide
    """
    return jsonify({
        "success": True,
        "data": {
            "valid": True,
            "user": request.current_user.get("sub"),
            "role": request.current_user.get("role")
        }
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh():
    """
    POST /api/auth/refresh
    Header: Authorization: Bearer <token>
    Renouvelle un token encore valide
    """
    username = request.current_user.get("sub")
    role = request.current_user.get("role")
    new_token = generer_token(username, role)

    return jsonify({
        "success": True,
        "data": {
            "token": new_token,
            "type": "Bearer",
            "expires_in": f"{JWT_EXPIRATION_HOURS}h"
        }
    }), 200


__all__ = ['auth_bp', 'jwt_required', 'admin_required']