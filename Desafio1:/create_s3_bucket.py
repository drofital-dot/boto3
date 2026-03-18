#!/usr/bin/env python3
"""
Script para crear un bucket de S3 con políticas automáticas.
Crea el bucket y asigna permisos para que el usuario pueda subir archivos.
"""

import sys
import json
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class S3BucketSetup:
    """Gestor para crear y configurar buckets S3."""
    
    def __init__(self, aws_profile: str = None, region: str = None):
        """
        Inicializar cliente S3.
        
        Args:
            aws_profile: Perfil de AWS a usar
            region: Región de AWS (si None, usa la de las credenciales)
        """
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
            else:
                session = boto3.Session()
            
            # Si region no se especifica, usar la de la sesión
            if region is None:
                region = session.region_name or "us-east-1"
            
            self.s3_client = session.client('s3', region_name=region)
            
            logger.info(f"✓ Conectado a AWS en región: {region}")
        except NoCredentialsError:
            logger.error("❌ Credenciales de AWS no encontradas")
            raise
        except Exception as e:
            logger.error(f"❌ Error al conectar con AWS: {e}")
            raise
        
        self.region = region
        self.aws_profile = aws_profile
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Verificar si un bucket existe.
        
        Args:
            bucket_name: Nombre del bucket
            
        Returns:
            True si existe, False si no
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"✓ Bucket existe: {bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"ℹ Bucket no existe: {bucket_name}")
                return False
            else:
                logger.error(f"❌ Error al verificar bucket: {e}")
                raise
    
    def create_bucket(self, bucket_name: str) -> bool:
        """
        Crear un nuevo bucket en S3.
        
        Args:
            bucket_name: Nombre del bucket (debe ser único globalmente)
            
        Returns:
            True si se creó exitosamente, False si no
        """
        try:
            # Validar nombre del bucket
            if len(bucket_name) < 3 or len(bucket_name) > 63:
                logger.error("❌ Nombre inválido: debe tener 3-63 caracteres")
                return False
            
            if not all(c.isalnum() or c == '-' for c in bucket_name):
                logger.error("❌ Nombre inválido: solo puede contener letras, números y guiones")
                return False
            
            if bucket_name.startswith('-') or bucket_name.endswith('-'):
                logger.error("❌ No puede empezar o terminar con guión")
                return False
            
            logger.info(f"Creando bucket: {bucket_name}")
            
            # Crear bucket
            if self.region == "us-east-1":
                # us-east-1 es la región default, se crea sin LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            logger.info(f"✓ Bucket creado exitosamente: {bucket_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                logger.error(f"❌ El bucket ya existe: {bucket_name}")
            elif e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"✓ Bucket ya existe y te pertenece: {bucket_name}")
                return True
            else:
                logger.error(f"❌ Error al crear bucket: {e}")
            return False
    
    def add_bucket_policy(self, bucket_name: str, policy_type: str = "backup") -> bool:
        """
        Agregar política al bucket.
        
        Args:
            bucket_name: Nombre del bucket
            policy_type: Tipo de política: 'backup' (solo escribir), 'public', 'full'
            
        Returns:
            True si se asignó exitosamente
        """
        try:
            # Obtener account ID
            sts_client = boto3.client('sts')
            account_id = sts_client.get_caller_identity()['Account']
            
            logger.info(f"Asignando política: {policy_type}")
            
            if policy_type == "backup":
                # Política para backup: permitir PutObject, ListBucket, GetObject
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": f"arn:aws:iam::{account_id}:root"
                            },
                            "Action": [
                                "s3:PutObject",
                                "s3:PutObjectAcl",
                                "s3:GetObject",
                                "s3:ListBucket"
                            ],
                            "Resource": [
                                f"arn:aws:s3:::{bucket_name}",
                                f"arn:aws:s3:::{bucket_name}/*"
                            ]
                        }
                    ]
                }
            
            elif policy_type == "public":
                # Política para lectura pública
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
            
            elif policy_type == "full":
                # Política de acceso completo (no recomendado en producción)
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": f"arn:aws:iam::{account_id}:root"
                            },
                            "Action": "s3:*",
                            "Resource": [
                                f"arn:aws:s3:::{bucket_name}",
                                f"arn:aws:s3:::{bucket_name}/*"
                            ]
                        }
                    ]
                }
            
            else:
                logger.error(f"❌ Tipo de política desconocido: {policy_type}")
                return False
            
            # Aplicar política
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
            
            logger.info(f"✓ Política '{policy_type}' asignada al bucket")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error al asignar política: {e}")
            return False
    
    def enable_versioning(self, bucket_name: str) -> bool:
        """
        Habilitar versionado de objetos en el bucket.
        
        Args:
            bucket_name: Nombre del bucket
            
        Returns:
            True si se habilitó exitosamente
        """
        try:
            logger.info("Habilitando versionado...")
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            logger.info("✓ Versionado habilitado")
            return True
        except ClientError as e:
            logger.error(f"❌ Error al habilitar versionado: {e}")
            return False
    
    def enable_lifecycle_policy(self, bucket_name: str, days: int = 90) -> bool:
        """
        Configurar política de ciclo de vida (archivar después de X días).
        
        Args:
            bucket_name: Nombre del bucket
            days: Días antes de archivar a Glacier
            
        Returns:
            True si se configuró exitosamente, False si no (pero no es crítico)
        """
        try:
            logger.info(f"Configurando ciclo de vida (archivar después de {days} días)...")
            
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'ArchiveBackups',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},  # Aplicar a todos los objetos
                        'Transitions': [
                            {
                                'Days': days,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            
            logger.info(f"✓ Ciclo de vida configurado")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                logger.error(f"❌ El bucket no existe: {bucket_name}")
            elif error_code == 'AccessDenied':
                logger.warning(f"⚠ Acceso denegado para configurar ciclo de vida (pero el bucket funciona)")
                return True  # No es crítico
            else:
                logger.warning(f"⚠ No se pudo configurar ciclo de vida: {e}")
                return True  # No es crítico, continuar
        except Exception as e:
            logger.warning(f"⚠ Error al configurar ciclo de vida (no crítico): {e}")
            return True  # No es crítico
    
    def block_public_access(self, bucket_name: str) -> bool:
        """
        Bloquear todo acceso público al bucket (recomendado en producción).
        
        Args:
            bucket_name: Nombre del bucket
            
        Returns:
            True si se configuró exitosamente
        """
        try:
            logger.info("Bloqueando acceso público...")
            
            self.s3_client.put_public_access_block(
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
            
        except ClientError as e:
            logger.error(f"❌ Error al bloquear acceso público: {e}")
            return False
    
    def setup_complete(self, bucket_name: str, enable_versioning: bool = True,
                      enable_lifecycle: bool = True, block_public: bool = True,
                      policy_type: str = "backup") -> bool:
        """
        Configuración completa del bucket.
        
        Args:
            bucket_name: Nombre del bucket
            enable_versioning: Habilitar versionado
            enable_lifecycle: Habilitar ciclo de vida
            block_public: Bloquear acceso público
            policy_type: Tipo de política a aplicar
            
        Returns:
            True si todo se configuró exitosamente
        """
        logger.info("\n" + "="*60)
        logger.info("CONFIGURACIÓN COMPLETA DE BUCKET S3")
        logger.info("="*60 + "\n")
        
        all_ok = True
        
        # Crear bucket
        if not self.bucket_exists(bucket_name):
            if not self.create_bucket(bucket_name):
                return False
        
        # Agregar política
        if not self.add_bucket_policy(bucket_name, policy_type):
            all_ok = False
        
        # Habilitar versioning
        if enable_versioning:
            if not self.enable_versioning(bucket_name):
                all_ok = False
        
        # Habilitar ciclo de vida
        if enable_lifecycle:
            if not self.enable_lifecycle_policy(bucket_name):
                all_ok = False
        
        # Bloquear acceso público
        if block_public:
            if not self.block_public_access(bucket_name):
                all_ok = False
        
        logger.info("\n" + "="*60)
        if all_ok:
            logger.info("✓ Bucket configurado exitosamente")
            logger.info(f"Puedes usarlo con: python s3_backup.py /ruta --bucket {bucket_name}")
        else:
            logger.warning("⚠ Bucket creado pero hay errores en la configuración")
        logger.info("="*60 + "\n")
        
        return all_ok


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crear y configurar bucket S3")
    parser.add_argument("bucket", help="Nombre del bucket S3 a crear")
    parser.add_argument("--region", default=None, help="Región AWS (default: usa la de 'aws configure')")
    parser.add_argument("--profile", default=None, help="Perfil de AWS a usar")
    parser.add_argument("--policy", default="backup", 
                       choices=["backup", "public", "full"],
                       help="Tipo de política (default: backup)")
    parser.add_argument("--no-versioning", action="store_true", 
                       help="No habilitar versionado")
    parser.add_argument("--no-lifecycle", action="store_true",
                       help="No configurar ciclo de vida")
    parser.add_argument("--allow-public", action="store_true",
                       help="Permitir acceso público")
    
    args = parser.parse_args()
    
    try:
        setup = S3BucketSetup(args.profile, args.region)
        
        success = setup.setup_complete(
            args.bucket,
            enable_versioning=not args.no_versioning,
            enable_lifecycle=not args.no_lifecycle,
            block_public=not args.allow_public,
            policy_type=args.policy
        )
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
