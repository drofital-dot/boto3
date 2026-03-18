# Configuración de ejemplo para backup_scheduler.py
# Copia esta configuración a backup_scheduler.py y personalízala

# Nombre del bucket S3
BUCKET_NAME = "mi-bucket-produccion"

# Perfil de AWS a usar (opcional, usa el perfil default si es None)
AWS_PROFILE = None  # O: "produccion", "development", etc.

# Configuración de carpetas a hacer backup
BACKUPS_CONFIG = [
    # Backup de carpeta de datos - Diario a las 2 AM
    {
        "source": "/home/usuario/datos",
        "prefix": "backups/datos",
        "time": "02:00",
        "exclude": [".git", "__pycache__", "*.tmp", ".env", "*.log"]
    },
    
    # Backup de documentos importantes - Diario a las 3 AM
    {
        "source": "/home/usuario/Documentos",
        "prefix": "backups/documentos",
        "time": "03:00",
        "exclude": [".DS_Store", "~$*", "*.tmp"]
    },
    
    # Backup de código - Diario a las 4 AM (excluye node_modules, .git, etc)
    {
        "source": "/home/usuario/proyectos",
        "prefix": "backups/proyectos",
        "time": "04:00",
        "exclude": [
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            ".env",
            "*.pyc",
            ".DS_Store"
        ]
    },
]


# ============================================
# Alternativas de programación
# ============================================

# Para programación HORARIA (cada hora):
# scheduler.schedule_hourly(
#     source_path="/ruta/datos",
#     s3_prefix="backups/datos",
#     exclude_patterns=[".git", "__pycache__"]
# )

# Para programación cada X MINUTOS (ej: cada 30 minutos):
# scheduler.schedule_interval(
#     source_path="/ruta/datos",
#     s3_prefix="backups/datos",
#     minutes=30,
#     exclude_patterns=[".git", "__pycache__"]
# )
