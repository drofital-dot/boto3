#!/usr/bin/env python3
"""
Script de backup programado para ejecutar regularmente.
Puede ser usado con APScheduler o ejecutarse directamente.
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path

from s3_backup import S3Backup

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupScheduler:
    """Programador de backups a S3."""
    
    def __init__(self, bucket_name: str, aws_profile: str = None):
        """Inicializar el programador."""
        self.backup = S3Backup(bucket_name, aws_profile)
        self.logger = logger
    
    def backup_folder(self, source_path: str, s3_prefix: str = None, 
                     exclude_patterns: list = None):
        """Ejecutar un backup."""
        try:
            self.logger.info(f"Iniciando backup programado de: {source_path}")
            
            if exclude_patterns:
                success = self.backup.create_backup_with_exclude(
                    source_path,
                    s3_prefix,
                    exclude_patterns
                )
            else:
                success = self.backup.create_backup(source_path, s3_prefix)
            
            status = "completado exitosamente" if success else "completado con errores"
            self.logger.info(f"Backup {status}")
            
        except Exception as e:
            self.logger.error(f"Error en backup programado: {e}")
    
    def schedule_daily(self, source_path: str, s3_prefix: str, 
                      time_str: str = "02:00", exclude_patterns: list = None):
        """Programar backup diario."""
        schedule.every().day.at(time_str).do(
            self.backup_folder,
            source_path=source_path,
            s3_prefix=s3_prefix,
            exclude_patterns=exclude_patterns
        )
        self.logger.info(f"Backup diario programado para las {time_str}")
    
    def schedule_hourly(self, source_path: str, s3_prefix: str, 
                       exclude_patterns: list = None):
        """Programar backup cada hora."""
        schedule.every().hour.do(
            self.backup_folder,
            source_path=source_path,
            s3_prefix=s3_prefix,
            exclude_patterns=exclude_patterns
        )
        self.logger.info("Backup horario programado")
    
    def schedule_interval(self, source_path: str, s3_prefix: str, 
                         minutes: int = 30, exclude_patterns: list = None):
        """Programar backup cada X minutos."""
        schedule.every(minutes).minutes.do(
            self.backup_folder,
            source_path=source_path,
            s3_prefix=s3_prefix,
            exclude_patterns=exclude_patterns
        )
        self.logger.info(f"Backup programado cada {minutes} minutos")
    
    def run_scheduler(self):
        """Ejecutar el planificador en un loop."""
        self.logger.info("Iniciando scheduler de backups...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            self.logger.info("Scheduler detenido por el usuario")


# Configuración de ejemplo
if __name__ == "__main__":
    # ============================================
    # CONFIGURACIÓN - Editar según necesidades
    # ============================================
    
    BUCKET_NAME = "mi-bucket-s3"
    AWS_PROFILE = None  # O usar: "mi-perfil"
    
    # Carpetas a hacer backup
    BACKUPS_CONFIG = [
        {
            "source": "/ruta/a/datos",
            "prefix": "backups/datos",
            "time": "02:00",  # Diario a las 2 AM
            "exclude": [".git", "__pycache__", "*.tmp", ".env"]
        },
        {
            "source": "/ruta/a/documentos",
            "prefix": "backups/documentos",
            "time": "03:00",  # Diario a las 3 AM
            "exclude": [".DS_Store", "~$*"]
        }
    ]
    
    # ============================================
    # INICIO
    # ============================================
    
    scheduler = BackupScheduler(BUCKET_NAME, AWS_PROFILE)
    
    # Programar backups
    for config in BACKUPS_CONFIG:
        scheduler.schedule_daily(
            source_path=config["source"],
            s3_prefix=config["prefix"],
            time_str=config["time"],
            exclude_patterns=config.get("exclude")
        )
    
    # Ejecutar scheduler
    scheduler.run_scheduler()
