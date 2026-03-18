#!/usr/bin/env python3
"""
Script de verificación de configuración de AWS.
Antes de usar los scripts de backup, ejecuta esto para verificar que todo está correcto.
"""

import sys
import json
import logging
import boto3

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_aws_credentials():
    """Verificar si las credenciales de AWS están configuradas."""
    logger.info("="*60)
    logger.info("Verificando credenciales de AWS...")
    logger.info("="*60)
    
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            logger.error("❌ No se encontraron credenciales de AWS")
            logger.info("\nSoluciones:")
            logger.info("  1. Ejecuta: aws configure")
            logger.info("  2. O establece variables de entorno:")
            logger.info("     export AWS_ACCESS_KEY_ID=<tu_key>")
            logger.info("     export AWS_SECRET_ACCESS_KEY=<tu_secret>")
            logger.info("  3. O crea ~/.aws/credentials")
            return False
        
        logger.info("✓ Credenciales de AWS encontradas")
        logger.info(f"  Región: {session.region_name or 'default (us-east-1)'}")
        return True
        
    except ImportError:
        logger.error("❌ boto3 no está instalado")
        logger.info("Instálalo con: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"❌ Error al verificar credenciales: {e}")
        return False


def bucket_exists(bucket_name):
    """Verificar si un bucket existe."""
    try:
        import boto3
        s3_client = boto3.client('s3')
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except Exception:
        return False


def check_s3_access(bucket_name):
    """Verificar acceso a un bucket S3 y crearlo si no existe."""
    logger.info("\n" + "="*60)
    logger.info(f"Verificando acceso a bucket: {bucket_name}")
    logger.info("="*60)
    
    try:
        import boto3
        s3_client = boto3.client('s3')
        
        # Verificar si el bucket existe
        if not bucket_exists(bucket_name):
            logger.warning(f"⚠ El bucket no existe: {bucket_name}")
            
            # Preguntar si crear
            response = input(f"\n¿Deseas crear el bucket '{bucket_name}'? (s/n): ").strip().lower()
            
            if response == 's' or response == 'si':
                return create_bucket_interactive(s3_client, bucket_name)
            else:
                logger.info("Bucket no creado")
                return False
        
        # Intentar listar el bucket
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        logger.info(f"✓ Acceso exitoso a bucket: {bucket_name}")
        return True
        
    except Exception as e:
        if "AccessDenied" in str(e):
            logger.error(f"❌ Acceso denegado al bucket: {bucket_name}")
            logger.info("Verifica tus permisos IAM")
        else:
            logger.error(f"❌ Error al acceder al bucket: {e}")
        return False


def create_bucket_interactive(s3_client, bucket_name):
    """Crear bucket de forma interactiva con configuración."""
    logger.info("\nConfiguración del bucket:")
    
    # Obtener región de la sesión
    session = boto3.Session()
    default_region = session.region_name or "us-east-1"
    
    region = input(f"Región AWS (default: {default_region}): ").strip() or default_region
    
    try:
        logger.info(f"Creando bucket: {bucket_name} en región {region}...")
        
        # Crear bucket
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        logger.info(f"✓ Bucket creado: {bucket_name}")
        
        # Agregar política
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                    "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        logger.info("✓ Política de acceso configurada")
        
        # Bloquear acceso público
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        logger.info("✓ Acceso público bloqueado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al crear bucket: {e}")
        return False


def check_local_folder(folder_path):
    """Verificar que una carpeta local existe."""
    logger.info("\n" + "="*60)
    logger.info(f"Verificando carpeta local: {folder_path}")
    logger.info("="*60)
    
    from pathlib import Path
    path = Path(folder_path).resolve()
    
    if not path.exists():
        logger.error(f"❌ La carpeta no existe: {path}")
        return False
    
    if not path.is_dir():
        logger.error(f"❌ No es una carpeta: {path}")
        return False
    
    # Contar archivos
    files = list(path.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    dir_count = len([f for f in files if f.is_dir()])
    
    logger.info(f"✓ Carpeta accesible: {path}")
    logger.info(f"  Archivos: {file_count}")
    logger.info(f"  Subcarpetas: {dir_count}")
    
    return True


def main():
    """Ejecutar todas las verificaciones."""
    logger.info("\n🔍 VERIFICACIÓN DE CONFIGURACIÓN DE BACKUP\n")
    
    results = {
        "Credenciales AWS": check_aws_credentials(),
    }
    
    # Obtener entrada del usuario
    bucket_name = input("\n¿Nombre del bucket S3 a verificar? (o Enter para saltar): ").strip()
    if bucket_name:
        results["Acceso a S3"] = check_s3_access(bucket_name)
    
    folder_path = input("\n¿Carpeta local a verificar? (o Enter para saltar): ").strip()
    if folder_path:
        results["Carpeta local"] = check_local_folder(folder_path)
    
    # Resumen
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE VERIFICACIÓN")
    logger.info("="*60)
    
    all_ok = True
    for check, result in results.items():
        status = "✓" if result else "❌"
        logger.info(f"{status} {check}")
        if not result:
            all_ok = False
    
    logger.info("="*60)
    
    if all_ok and results:
        logger.info("\n✓ ¡Todo está configurado correctamente!")
        logger.info("Puedes ejecutar: python s3_backup.py --help")
        return 0
    else:
        logger.error("\n❌ Hay problemas de configuración a resolver")
        return 1


if __name__ == "__main__":
    sys.exit(main())
