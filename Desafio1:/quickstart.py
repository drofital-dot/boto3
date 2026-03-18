#!/usr/bin/env python3
"""
Script de inicio rápido para configurar todo el sistema de backup.
Instala dependencias, crea el bucket y realiza un primer backup.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run_command(command, description=""):
    """Ejecutar un comando y retornar el resultado."""
    if description:
        logger.info(f"\n{description}...")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✓ Completado")
            return True
        else:
            logger.error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def install_dependencies():
    """Instalar dependencias."""
    logger.info("\n" + "="*60)
    logger.info("PASO 1: Instalar dependencias")
    logger.info("="*60)
    
    if not run_command("pip install -r requirements.txt", "Instalando dependencias"):
        return False
    
    logger.info("✓ Dependencias instaladas")
    return True


def verify_aws_credentials():
    """Verificar credenciales de AWS."""
    logger.info("\n" + "="*60)
    logger.info("PASO 2: Verificar credenciales de AWS")
    logger.info("="*60)
    
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            logger.error("❌ Credenciales no encontradas")
            logger.info("\nConfiguración de credenciales:")
            logger.info("  1. Ejecuta: aws configure")
            logger.info("  2. O establece variables:")
            logger.info("     export AWS_ACCESS_KEY_ID=...")
            logger.info("     export AWS_SECRET_ACCESS_KEY=...")
            return False
        
        logger.info("✓ Credenciales de AWS encontradas")
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def create_bucket():
    """Crear bucket de S3."""
    logger.info("\n" + "="*60)
    logger.info("PASO 3: Crear bucket de S3")
    logger.info("="*60)
    
    bucket_name = input("\nNombre del bucket S3: ").strip()
    
    if not bucket_name:
        logger.error("Nombre del bucket requerido")
        return None
    
    if not run_command(f"python create_s3_bucket.py {bucket_name}", 
                      f"Creando bucket '{bucket_name}'"):
        logger.warning("⚠ No se pudo crear el bucket automáticamente")
        response = input("¿Continuar de todas formas? (s/n): ").strip().lower()
        if response != 's' and response != 'si':
            return None
    
    logger.info(f"✓ Bucket '{bucket_name}' listo")
    return bucket_name


def make_first_backup(bucket_name):
    """Hacer primer backup de prueba."""
    logger.info("\n" + "="*60)
    logger.info("PASO 4: Primer backup de prueba")
    logger.info("="*60)
    
    folder = input("\nRuta de la carpeta a hacer backup (o Enter para saltar): ").strip()
    
    if not folder:
        logger.info("Saltado")
        return True
    
    folder = Path(folder).expanduser().resolve()
    
    if not folder.is_dir():
        logger.error(f"Carpeta no existe: {folder}")
        return False
    
    logger.info(f"\nHaciendo backup de: {folder}")
    
    if not run_command(f"python s3_backup.py '{folder}' --bucket {bucket_name}",
                      "Ejecutando backup"):
        logger.error("Error en el backup")
        return False
    
    logger.info(f"✓ Backup completado en bucket: {bucket_name}")
    return True


def schedule_backup():
    """Configurar backup automático."""
    logger.info("\n" + "="*60)
    logger.info("PASO 5: Backup automático (opcional)")
    logger.info("="*60)
    
    response = input("\n¿Configurar backups automáticos? (s/n): ").strip().lower()
    
    if response != 's' and response != 'si':
        return True
    
    logger.info("Ver: python backup_scheduler.py --help")
    logger.info("Editar: config_example.py para la configuración")
    
    return True


def main():
    """Función principal."""
    logger.info("\n" + "🚀 "*15)
    logger.info("CONFIGURACIÓN INICIAL DE BACKUP A S3")
    logger.info("🚀 "*15 + "\n")
    
    # Paso 1: Instalar dependencias
    if not install_dependencies():
        logger.error("Cancela. No se pudieron instalar dependencias")
        return False
    
    # Paso 2: Verificar AWS
    if not verify_aws_credentials():
        logger.error("Cancela. No hay credenciales de AWS")
        return False
    
    # Paso 3: Crear bucket
    bucket_name = create_bucket()
    if not bucket_name:
        logger.error("Cancela. No se pudo crear el bucket")
        return False
    
    # Paso 4: Primer backup
    if not make_first_backup(bucket_name):
        logger.warning("⚠ Hubo un problema con el backup")
    
    # Paso 5: Backup automático
    schedule_backup()
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info("✓ CONFIGURACIÓN COMPLETADA")
    logger.info("="*60)
    logger.info(f"\nPróximos pasos:")
    logger.info(f"  1. Ver contenido del bucket:")
    logger.info(f"     aws s3 ls s3://{bucket_name}/ --recursive")
    logger.info(f"\n  2. Hacer más backups:")
    logger.info(f"     python s3_backup.py /ruta --bucket {bucket_name}")
    logger.info(f"\n  3. Configurar backups automáticos:")
    logger.info(f"     python backup_scheduler.py")
    logger.info(f"\n  4. Ver documentación:")
    logger.info(f"     cat README.md")
    logger.info("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nCancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
