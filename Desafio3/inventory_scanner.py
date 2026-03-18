#!/usr/bin/env python3
"""
AWS Resource Inventory Scanner
Escanea recursos AWS y genera un inventario completo.

Uso:
    python inventory_scanner.py --help
    python inventory_scanner.py --profile default --region us-east-1 --format table
    python inventory_scanner.py --services ec2 s3 --output inventory.json
"""

import argparse
import json
import csv
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AWSResourceScanner:
    """
    Escáner de recursos AWS que recopila información de múltiples servicios.
    """

    def __init__(self, aws_profile: str = None, region: str = None):
        """
        Inicializa el escáner con credenciales y región.

        Args:
            aws_profile: Perfil de AWS a usar (opcional)
            region: Región de AWS (opcional, usa la del perfil o us-east-1)
        """
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                logger.info(f"✓ Usando perfil AWS: {aws_profile}")
            else:
                session = boto3.Session()
                logger.info("✓ Usando credenciales por defecto")

            # Determinar región
            if region is None:
                region = session.region_name or "us-east-1"

            self.session = session
            self.region = region
            self.account_id = self._get_account_id()

            logger.info(f"✓ Región: {region}")
            logger.info(f"✓ Account ID: {self.account_id}")

        except ProfileNotFound as e:
            logger.error(f"❌ Perfil no encontrado: {e}")
            raise
        except NoCredentialsError:
            logger.error("❌ Credenciales de AWS no encontradas")
            logger.error("   Configura con: aws configure")
            raise
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise

    def _get_account_id(self) -> str:
        """Obtiene el ID de la cuenta AWS."""
        try:
            sts_client = self.session.client('sts', region_name=self.region)
            response = sts_client.get_caller_identity()
            return response['Account']
        except Exception as e:
            logger.warning(f"No se pudo obtener Account ID: {e}")
            return "unknown"

    def scan_all_resources(self) -> Dict[str, Any]:
        """
        Escanea todos los recursos soportados.

        Returns:
            Diccionario con todos los recursos organizados por servicio
        """
        logger.info("🔍 Iniciando escaneo completo de recursos AWS...")

        inventory = {
            'metadata': {
                'account_id': self.account_id,
                'region': self.region,
                'scan_timestamp': datetime.now().isoformat(),
                'scanner_version': '1.0.0'
            },
            'resources': {}
        }

        # Escanear cada servicio
        services = [
            ('ec2', self.scan_ec2_instances),
            ('s3', self.scan_s3_buckets),
            ('rds', self.scan_rds_databases),
            ('lambda', self.scan_lambda_functions),
            ('vpc', self.scan_vpc_resources),
            ('ebs', self.scan_ebs_volumes)
        ]

        for service_name, scan_method in services:
            try:
                logger.info(f"📋 Escaneando {service_name.upper()}...")
                inventory['resources'][service_name] = scan_method()
                logger.info(f"✓ {service_name.upper()}: {len(inventory['resources'][service_name])} recursos encontrados")
            except Exception as e:
                logger.error(f"❌ Error escaneando {service_name.upper()}: {e}")
                inventory['resources'][service_name] = {'error': str(e)}

        return inventory

    def scan_ec2_instances(self) -> List[Dict]:
        """
        Escanea instancias EC2.

        Returns:
            Lista de instancias con detalles
        """
        try:
            ec2_client = self.session.client('ec2', region_name=self.region)
            response = ec2_client.describe_instances()

            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_data = {
                        'InstanceId': instance.get('InstanceId', 'N/A'),
                        'State': instance.get('State', {}).get('Name', 'N/A'),
                        'InstanceType': instance.get('InstanceType', 'N/A'),
                        'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'VpcId': instance.get('VpcId', 'N/A'),
                        'SubnetId': instance.get('SubnetId', 'N/A'),
                        'KeyName': instance.get('KeyName', 'N/A'),
                        'LaunchTime': instance.get('LaunchTime', 'N/A'),
                        'Tags': instance.get('Tags', [])
                    }
                    instances.append(instance_data)

            return instances

        except ClientError as e:
            logger.error(f"Error en EC2: {e}")
            return []

    def scan_s3_buckets(self) -> List[Dict]:
        """
        Escanea buckets S3.

        Returns:
            Lista de buckets con información básica
        """
        try:
            s3_client = self.session.client('s3')
            response = s3_client.list_buckets()

            buckets = []
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']

                # Obtener ubicación del bucket
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket_name)
                    region = location.get('LocationConstraint', 'us-east-1')
                    if region is None:  # Buckets en us-east-1 devuelven None
                        region = 'us-east-1'
                except:
                    region = 'unknown'

                # Contar objetos (aproximado)
                try:
                    objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                    object_count = objects_response.get('KeyCount', 0)
                except:
                    object_count = 'unknown'

                bucket_data = {
                    'Name': bucket_name,
                    'CreationDate': bucket.get('CreationDate', 'N/A'),
                    'Region': region,
                    'ObjectCount': object_count
                }
                buckets.append(bucket_data)

            return buckets

        except ClientError as e:
            logger.error(f"Error en S3: {e}")
            return []

    def scan_rds_databases(self) -> List[Dict]:
        """
        Escanea bases de datos RDS.

        Returns:
            Lista de instancias RDS
        """
        try:
            rds_client = self.session.client('rds', region_name=self.region)
            response = rds_client.describe_db_instances()

            databases = []
            for db in response.get('DBInstances', []):
                db_data = {
                    'DBInstanceIdentifier': db.get('DBInstanceIdentifier', 'N/A'),
                    'DBInstanceStatus': db.get('DBInstanceStatus', 'N/A'),
                    'DBInstanceClass': db.get('DBInstanceClass', 'N/A'),
                    'Engine': db.get('Engine', 'N/A'),
                    'EngineVersion': db.get('EngineVersion', 'N/A'),
                    'Endpoint': db.get('Endpoint', {}).get('Address', 'N/A'),
                    'Port': db.get('Endpoint', {}).get('Port', 'N/A'),
                    'AllocatedStorage': db.get('AllocatedStorage', 'N/A'),
                    'MultiAZ': db.get('MultiAZ', False),
                    'VpcId': db.get('DBSubnetGroup', {}).get('VpcId', 'N/A')
                }
                databases.append(db_data)

            return databases

        except ClientError as e:
            logger.error(f"Error en RDS: {e}")
            return []

    def scan_lambda_functions(self) -> List[Dict]:
        """
        Escanea funciones Lambda.

        Returns:
            Lista de funciones Lambda
        """
        try:
            lambda_client = self.session.client('lambda', region_name=self.region)
            response = lambda_client.list_functions()

            functions = []
            for function in response.get('Functions', []):
                func_data = {
                    'FunctionName': function.get('FunctionName', 'N/A'),
                    'Runtime': function.get('Runtime', 'N/A'),
                    'MemorySize': function.get('MemorySize', 'N/A'),
                    'Timeout': function.get('Timeout', 'N/A'),
                    'LastModified': function.get('LastModified', 'N/A'),
                    'Version': function.get('Version', 'N/A'),
                    'State': function.get('State', 'N/A'),
                    'Architectures': function.get('Architectures', [])
                }
                functions.append(func_data)

            return functions

        except ClientError as e:
            logger.error(f"Error en Lambda: {e}")
            return []

    def scan_vpc_resources(self) -> Dict[str, List[Dict]]:
        """
        Escanea recursos VPC (VPCs, Subnets, Security Groups).

        Returns:
            Diccionario con VPCs, subnets y security groups
        """
        try:
            ec2_client = self.session.client('ec2', region_name=self.region)

            # VPCs
            vpcs_response = ec2_client.describe_vpcs()
            vpcs = []
            for vpc in vpcs_response.get('Vpcs', []):
                vpc_data = {
                    'VpcId': vpc.get('VpcId', 'N/A'),
                    'State': vpc.get('State', 'N/A'),
                    'CidrBlock': vpc.get('CidrBlock', 'N/A'),
                    'IsDefault': vpc.get('IsDefault', False),
                    'Tags': vpc.get('Tags', [])
                }
                vpcs.append(vpc_data)

            # Subnets
            subnets_response = ec2_client.describe_subnets()
            subnets = []
            for subnet in subnets_response.get('Subnets', []):
                subnet_data = {
                    'SubnetId': subnet.get('SubnetId', 'N/A'),
                    'VpcId': subnet.get('VpcId', 'N/A'),
                    'CidrBlock': subnet.get('CidrBlock', 'N/A'),
                    'AvailabilityZone': subnet.get('AvailabilityZone', 'N/A'),
                    'State': subnet.get('State', 'N/A'),
                    'Tags': subnet.get('Tags', [])
                }
                subnets.append(subnet_data)

            # Security Groups
            sg_response = ec2_client.describe_security_groups()
            security_groups = []
            for sg in sg_response.get('SecurityGroups', []):
                sg_data = {
                    'GroupId': sg.get('GroupId', 'N/A'),
                    'GroupName': sg.get('GroupName', 'N/A'),
                    'VpcId': sg.get('VpcId', 'N/A'),
                    'Description': sg.get('Description', 'N/A'),
                    'IpPermissions': sg.get('IpPermissions', []),
                    'IpPermissionsEgress': sg.get('IpPermissionsEgress', []),
                    'Tags': sg.get('Tags', [])
                }
                security_groups.append(sg_data)

            return {
                'vpcs': vpcs,
                'subnets': subnets,
                'security_groups': security_groups
            }

        except ClientError as e:
            logger.error(f"Error en VPC: {e}")
            return {'vpcs': [], 'subnets': [], 'security_groups': []}

    def scan_ebs_volumes(self) -> List[Dict]:
        """
        Escanea volúmenes EBS.

        Returns:
            Lista de volúmenes EBS
        """
        try:
            ec2_client = self.session.client('ec2', region_name=self.region)
            response = ec2_client.describe_volumes()

            volumes = []
            for volume in response.get('Volumes', []):
                volume_data = {
                    'VolumeId': volume.get('VolumeId', 'N/A'),
                    'State': volume.get('State', 'N/A'),
                    'Size': volume.get('Size', 'N/A'),
                    'VolumeType': volume.get('VolumeType', 'N/A'),
                    'Iops': volume.get('Iops', 'N/A'),
                    'AvailabilityZone': volume.get('AvailabilityZone', 'N/A'),
                    'Encrypted': volume.get('Encrypted', False),
                    'Attachments': volume.get('Attachments', [])
                }
                volumes.append(volume_data)

            return volumes

        except ClientError as e:
            logger.error(f"Error en EBS: {e}")
            return []

    def get_summary_stats(self, inventory: Dict) -> Dict[str, Any]:
        """
        Genera estadísticas resumidas del inventario.

        Args:
            inventory: Resultado del escaneo

        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total_resources': 0,
            'services_scanned': len(inventory.get('resources', {})),
            'service_counts': {}
        }

        resources = inventory.get('resources', {})

        # Contar recursos por servicio
        for service, items in resources.items():
            if isinstance(items, list):
                count = len(items)
            elif isinstance(items, dict) and 'error' not in items:
                # Para VPC que tiene sub-diccionarios
                count = sum(len(v) for v in items.values() if isinstance(v, list))
            else:
                count = 0

            stats['service_counts'][service] = count
            stats['total_resources'] += count

        return stats


class InventoryFormatter:
    """
    Formateador de salida para el inventario.
    """

    @staticmethod
    def to_table(inventory: Dict) -> str:
        """Formatea el inventario como tabla de texto."""
        output = []
        output.append("=" * 80)
        output.append("INVENTARIO DE RECURSOS AWS")
        output.append("=" * 80)
        output.append(f"Cuenta: {inventory['metadata']['account_id']}")
        output.append(f"Región: {inventory['metadata']['region']}")
        output.append(f"Fecha: {inventory['metadata']['scan_timestamp']}")
        output.append("")

        resources = inventory.get('resources', {})

        for service, items in resources.items():
            output.append(f"📋 {service.upper()}")
            output.append("-" * 40)

            if isinstance(items, list) and items:
                # Mostrar primeros 5 elementos como ejemplo
                for i, item in enumerate(items[:5]):
                    if service == 'ec2':
                        output.append(f"  {i+1}. {item.get('InstanceId', 'N/A')} - {item.get('State', 'N/A')} ({item.get('InstanceType', 'N/A')})")
                    elif service == 's3':
                        output.append(f"  {i+1}. {item.get('Name', 'N/A')} - {item.get('Region', 'N/A')} ({item.get('ObjectCount', 'N/A')} objetos)")
                    elif service == 'rds':
                        output.append(f"  {i+1}. {item.get('DBInstanceIdentifier', 'N/A')} - {item.get('DBInstanceStatus', 'N/A')} ({item.get('Engine', 'N/A')})")
                    elif service == 'lambda':
                        output.append(f"  {i+1}. {item.get('FunctionName', 'N/A')} - {item.get('Runtime', 'N/A')} ({item.get('MemorySize', 'N/A')}MB)")
                    elif service == 'ebs':
                        output.append(f"  {i+1}. {item.get('VolumeId', 'N/A')} - {item.get('State', 'N/A')} ({item.get('Size', 'N/A')}GB)")

                if len(items) > 5:
                    output.append(f"  ... y {len(items) - 5} más")
            elif isinstance(items, dict) and 'error' not in items:
                # VPC con sub-recursos
                for sub_type, sub_items in items.items():
                    output.append(f"  {sub_type}: {len(sub_items)} recursos")
            elif 'error' in items:
                output.append(f"  ❌ Error: {items['error']}")
            else:
                output.append("  No resources found")

            output.append("")

        return "\n".join(output)

    @staticmethod
    def to_json(inventory: Dict) -> str:
        """Formatea el inventario como JSON."""
        return json.dumps(inventory, indent=2, default=str)

    @staticmethod
    def to_csv(inventory: Dict) -> str:
        """Formatea el inventario como CSV (solo resumen)."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Service', 'ResourceType', 'Count', 'Account', 'Region'])

        resources = inventory.get('resources', {})
        metadata = inventory.get('metadata', {})

        for service, items in resources.items():
            if isinstance(items, list):
                writer.writerow([service, 'items', len(items), metadata.get('account_id'), metadata.get('region')])
            elif isinstance(items, dict) and 'error' not in items:
                for sub_type, sub_items in items.items():
                    writer.writerow([service, sub_type, len(sub_items), metadata.get('account_id'), metadata.get('region')])

        return output.getvalue()


def main():
    """Función principal para CLI."""
    parser = argparse.ArgumentParser(
        description="Escáner de inventario de recursos AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python inventory_scanner.py --profile default --region us-east-1
  python inventory_scanner.py --services ec2 s3 --format json --output inventory.json
  python inventory_scanner.py --all --format table
        """
    )

    parser.add_argument('--profile', help='Perfil de AWS a usar')
    parser.add_argument('--region', help='Región de AWS (por defecto: us-east-1)')
    parser.add_argument('--services', nargs='*',
                       choices=['ec2', 's3', 'rds', 'lambda', 'vpc', 'ebs'],
                       help='Servicios específicos a escanear (por defecto: todos)')
    parser.add_argument('--format', choices=['table', 'json', 'csv'],
                       default='table', help='Formato de salida (por defecto: table)')
    parser.add_argument('--output', help='Archivo de salida (opcional)')
    parser.add_argument('--all', action='store_true',
                       help='Escanear todos los servicios (por defecto)')

    args = parser.parse_args()

    try:
        # Crear escáner
        scanner = AWSResourceScanner(aws_profile=args.profile, region=args.region)

        # Escanear recursos
        if args.services:
            # Escanear servicios específicos (no implementado aún)
            logger.warning("Escaneo de servicios específicos no implementado aún. Usando --all")
            inventory = scanner.scan_all_resources()
        else:
            inventory = scanner.scan_all_resources()

        # Generar estadísticas
        stats = scanner.get_summary_stats(inventory)
        inventory['summary'] = stats

        # Formatear salida
        if args.format == 'json':
            output = InventoryFormatter.to_json(inventory)
        elif args.format == 'csv':
            output = InventoryFormatter.to_csv(inventory)
        else:
            output = InventoryFormatter.to_table(inventory)

        # Mostrar o guardar
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"✓ Inventario guardado en: {args.output}")
        else:
            print(output)

        logger.info(f"✓ Escaneo completado. {stats['total_resources']} recursos encontrados.")

    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())