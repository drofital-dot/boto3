#!/usr/bin/env python3
"""
Script de prueba para el backup a S3.
Usa un bucket local simulado (moto) para pruebas sin necesidad de AWS real.
"""

import os
import sys
import tempfile
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from s3_backup import S3Backup

try:
    import moto
    from moto import mock_aws
    HAS_MOTO = True
except ImportError:
    try:
        from moto import mock_s3
        mock_aws = mock_s3
        HAS_MOTO = True
    except ImportError:
        print("moto no está instalado. Instálalo con: pip install moto")
        HAS_MOTO = False


def test_basic_backup():
    """Prueba básica del backup."""
    if not HAS_MOTO:
        print("Instalando moto para pruebas...")
        os.system("pip install moto")
        return
    
    print("Iniciando prueba de backup a S3...")
    print("-" * 50)
    
    with mock_aws():
        # Crear cliente S3 para pruebas
        import boto3
        boto3.client('s3').create_bucket(Bucket='test-bucket')
        
        # Crear carpeta de prueba con archivos
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Crear estructura de prueba
            (tmpdir_path / "archivo1.txt").write_text("contenido 1")
            (tmpdir_path / "archivo2.txt").write_text("contenido 2")
            
            subdir = tmpdir_path / "subcarpeta"
            subdir.mkdir()
            (subdir / "archivo3.txt").write_text("contenido 3")
            
            # Crear backup
            backup = S3Backup("test-bucket")
            success = backup.create_backup(str(tmpdir_path), "test-backup")
            
            print("-" * 50)
            print(f"Prueba completada con éxito: {success}")
            
            # Listar contenido del backup
            s3_client = boto3.client('s3')
            response = s3_client.list_objects_v2(Bucket='test-bucket')
            
            print(f"\nArchivos en S3:")
            if 'Contents' in response:
                for obj in response['Contents']:
                    print(f"  - {obj['Key']}")


def test_backup_with_exclude():
    """Prueba del backup con exclusiones."""
    if not HAS_MOTO:
        return
    
    print("\n\nPrueba de backup con exclusiones...")
    print("-" * 50)
    
    with mock_aws():
        import boto3
        boto3.client('s3').create_bucket(Bucket='test-bucket')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Crear archivos
            (tmpdir_path / "archivo.txt").write_text("contenido")
            (tmpdir_path / ".gitignore").write_text("*.log")
            (tmpdir_path / "temp.tmp").write_text("temporal")
            
            subdir = tmpdir_path / ".git"
            subdir.mkdir()
            (subdir / "config").write_text("config")
            
            # Backup con exclusiones
            backup = S3Backup("test-bucket")
            success = backup.create_backup_with_exclude(
                str(tmpdir_path),
                "test-backup",
                exclude_patterns=[".git", ".gitignore", ".tmp"]
            )
            
            print("-" * 50)
            print(f"Prueba completada con éxito: {success}")
            
            # Listar contenido
            s3_client = boto3.client('s3')
            response = s3_client.list_objects_v2(Bucket='test-bucket')
            
            print(f"\nArchivos en S3 (sin exclusiones):")
            if 'Contents' in response:
                for obj in response['Contents']:
                    print(f"  - {obj['Key']}")


if __name__ == "__main__":
    test_basic_backup()
    test_backup_with_exclude()
