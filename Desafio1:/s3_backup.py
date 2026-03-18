#!/usr/bin/env python3
"""
Script de backup automático de carpetas locales a Amazon S3.
Sube todos los archivos de una carpeta local a S3 manteniendo la estructura
de directorios y creando una carpeta con fecha/timestamp.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class S3Backup:
    """Gestor de backups a S3."""
    
    def __init__(self, bucket_name: str, aws_profile: str = None):
        """
        Inicializar el cliente de S3.
        
        Args:
            bucket_name: Nombre del bucket S3
            aws_profile: Perfil de AWS a usar (opcional)
        """
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                self.s3_client = session.client('s3')
            else:
                self.s3_client = boto3.client('s3')
            
            logger.info(f"Conectado a S3 con bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("Credenciales de AWS no encontradas. Verifica tu configuración.")
            raise
        except Exception as e:
            logger.error(f"Error al conectar con S3: {e}")
            raise
        
        self.bucket_name = bucket_name
    
    def create_backup(self, source_path: str, s3_prefix: str = None):
        """
        Crear backup de una carpeta local a S3.
        
        Args:
            source_path: Ruta de la carpeta local a hacer backup
            s3_prefix: Prefijo opcional en S3 (p.ej., 'backups/proyecto1')
        """
        source_path = Path(source_path).resolve()
        
        # Validar que la carpeta exista
        if not source_path.is_dir():
            logger.error(f"La carpeta no existe: {source_path}")
            return False
        
        # Crear prefix con fecha si no se proporciona
        if not s3_prefix:
            s3_prefix = "backup"
        
        # Agregar timestamp a la carpeta
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"{s3_prefix}/{timestamp}"
        
        logger.info(f"Iniciando backup de: {source_path}")
        logger.info(f"Destino S3: s3://{self.bucket_name}/{backup_folder}/")
        
        files_uploaded = 0
        files_failed = 0
        
        try:
            # Recorrer todos los archivos en la carpeta
            for local_file_path in source_path.rglob("*"):
                if local_file_path.is_file():
                    # Calcular la ruta relativa
                    relative_path = local_file_path.relative_to(source_path)
                    
                    # Crear la clave S3 combinando prefix + ruta relativa
                    s3_key = f"{backup_folder}/{relative_path}".replace("\\", "/")
                    
                    try:
                        # Subir el archivo
                        self.s3_client.upload_file(
                            str(local_file_path),
                            self.bucket_name,
                            s3_key
                        )
                        logger.info(f"✓ Subido: {relative_path}")
                        files_uploaded += 1
                    
                    except ClientError as e:
                        logger.error(f"✗ Error al subir {relative_path}: {e}")
                        files_failed += 1
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Backup completado:")
            logger.info(f"  Archivos subidos: {files_uploaded}")
            logger.info(f"  Errores: {files_failed}")
            logger.info(f"  Carpeta S3: {backup_folder}")
            logger.info(f"{'='*50}")
            
            return files_failed == 0
        
        except Exception as e:
            logger.error(f"Error durante el backup: {e}")
            return False
    
    def create_backup_with_exclude(self, source_path: str, s3_prefix: str = None, 
                                   exclude_patterns: list = None):
        """
        Crear backup excluyendo ciertos patrones de archivo.
        
        Args:
            source_path: Ruta de la carpeta local
            s3_prefix: Prefijo en S3
            exclude_patterns: Lista de patrones a excluir (p.ej., ['.git', '__pycache__', '*.tmp'])
        """
        if exclude_patterns is None:
            exclude_patterns = []
        
        source_path = Path(source_path).resolve()
        
        if not source_path.is_dir():
            logger.error(f"La carpeta no existe: {source_path}")
            return False
        
        if not s3_prefix:
            s3_prefix = "backup"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"{s3_prefix}/{timestamp}"
        
        logger.info(f"Iniciando backup de: {source_path}")
        logger.info(f"Patrones excluidos: {exclude_patterns}")
        logger.info(f"Destino S3: s3://{self.bucket_name}/{backup_folder}/")
        
        files_uploaded = 0
        files_failed = 0
        files_excluded = 0
        
        def should_exclude(file_path: Path, patterns: list) -> bool:
            """Verificar si un archivo debe ser excluido."""
            for pattern in patterns:
                if pattern in str(file_path):
                    return True
            return False
        
        try:
            for local_file_path in source_path.rglob("*"):
                if local_file_path.is_file():
                    if should_exclude(local_file_path, exclude_patterns):
                        files_excluded += 1
                        continue
                    
                    relative_path = local_file_path.relative_to(source_path)
                    s3_key = f"{backup_folder}/{relative_path}".replace("\\", "/")
                    
                    try:
                        self.s3_client.upload_file(
                            str(local_file_path),
                            self.bucket_name,
                            s3_key
                        )
                        logger.info(f"✓ Subido: {relative_path}")
                        files_uploaded += 1
                    
                    except ClientError as e:
                        logger.error(f"✗ Error al subir {relative_path}: {e}")
                        files_failed += 1
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Backup completado:")
            logger.info(f"  Archivos subidos: {files_uploaded}")
            logger.info(f"  Archivos excluidos: {files_excluded}")
            logger.info(f"  Errores: {files_failed}")
            logger.info(f"  Carpeta S3: {backup_folder}")
            logger.info(f"{'='*50}")
            
            return files_failed == 0
        
        except Exception as e:
            logger.error(f"Error durante el backup: {e}")
            return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Hacer backup automático de carpetas locales a S3"
    )
    parser.add_argument(
        "source",
        help="Ruta de la carpeta a hacer backup"
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="Nombre del bucket S3"
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Prefijo en S3 (p.ej., backups/proyecto1). Por defecto: 'backup'"
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Perfil de AWS a usar (opcional)"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Patrones a excluir (p.ej., .git __pycache__ *.tmp)"
    )
    
    args = parser.parse_args()
    
    try:
        # Crear instancia de backup
        backup = S3Backup(args.bucket, args.profile)
        
        # Realizar backup
        if args.exclude:
            success = backup.create_backup_with_exclude(
                args.source,
                args.prefix,
                args.exclude
            )
        else:
            success = backup.create_backup(args.source, args.prefix)
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
