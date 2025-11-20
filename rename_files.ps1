# Créer les dossiers
New-Item -ItemType Directory -Force -Path "backend/models"
New-Item -ItemType Directory -Force -Path "backend/controllers"
New-Item -ItemType Directory -Force -Path "backend/services"
New-Item -ItemType Directory -Force -Path "backend/views"
New-Item -ItemType Directory -Force -Path "backend/middleware"
New-Item -ItemType Directory -Force -Path "backend/tests"

# Configuration
Move-Item "backend/backend_app.py" "backend/app.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_config.py" "backend/config.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_requirements.txt" "backend/requirements.txt" -Force -ErrorAction SilentlyContinue

# Models
Move-Item "backend/backend_models_base.py" "backend/models/base.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_model_arrondissement.py" "backend/models/arrondissement.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_model_prix.py" "backend/models/prix.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_models_logement.py" "backend/models/logement.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_models_transport.py" "backend/models/transport.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_models_pollution.py" "backend/models/pollution.py" -Force -ErrorAction SilentlyContinue

# Controllers
Move-Item "backend/backend_controller_prix.py" "backend/controllers/prix_controller.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_controller_logement.py" "backend/controllers/logement_controller.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_controller_transport.py" "backend/controllers/transport_controller.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_controller_pollution.py" "backend/controllers/pollution_controller.py" -Force -ErrorAction SilentlyContinue

# Services
Move-Item "backend/backend_data_loader.py" "backend/services/data_loader.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_services_calculator.py" "backend/services/calculator.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_services_cache.py" "backend/services/cache.py" -Force -ErrorAction SilentlyContinue

# Views
Move-Item "backend/backend_response_formatter.py" "backend/views/response_formatter.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_views_schemas.py" "backend/views/schemas.py" -Force -ErrorAction SilentlyContinue

# Middleware
Move-Item "backend/backend_middleware_error_handler.py" "backend/middleware/error_handler.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_middleware_cors.py" "backend/middleware/cors.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_middleware_logger.py" "backend/middleware/logger.py" -Force -ErrorAction SilentlyContinue

# Tests
Move-Item "backend/backend_tests_test_models.py" "backend/tests/test_models.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_tests_test_controllers.py" "backend/tests/test_controllers.py" -Force -ErrorAction SilentlyContinue
Move-Item "backend/backend_tests_test_integration.py" "backend/tests/test_integration.py" -Force -ErrorAction SilentlyContinue

# Créer __init__.py
New-Item -ItemType File -Path "backend/__init__.py" -Force
New-Item -ItemType File -Path "backend/models/__init__.py" -Force
New-Item -ItemType File -Path "backend/controllers/__init__.py" -Force
New-Item -ItemType File -Path "backend/services/__init__.py" -Force
New-Item -ItemType File -Path "backend/views/__init__.py" -Force
New-Item -ItemType File -Path "backend/middleware/__init__.py" -Force
New-Item -ItemType File -Path "backend/tests/__init__.py" -Force

Write-Host "Termine !" -ForegroundColor Green