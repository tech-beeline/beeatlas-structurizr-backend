#from models import *

# Импорт моделей для system-service API
from .model_system_service import (
    SystemServiceClient,
    SystemServiceConfig,
    SystemServiceResponse,
    SystemServiceError,
    # Основные типы данных
    System,
    Container,
    Interface,
    Method,
    SystemPurpose,
    SystemE2EParticipation,
    SystemAssessmentResult,
    SystemMonitoringResult,
    MethodSLA,
    SystemApiMetricTemplate,
    SystemProvidedApi,
    SystemQueryLevel
)