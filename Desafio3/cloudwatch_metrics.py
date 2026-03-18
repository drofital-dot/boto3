#!/usr/bin/env python3
"""
Sistema de Alertas con CloudWatch - Métricas Personalizadas
Crea métricas personalizadas en CloudWatch desde datos de inventario AWS.

Uso:
    python cloudwatch_metrics.py --help
    python cloudwatch_metrics.py --inventory-file inventory.json --send-metrics
    python cloudwatch_metrics.py --create-alarms
"""

import argparse
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudWatchMetricsPublisher:
    """
    Publicador de métricas personalizadas en CloudWatch.
    """

    def __init__(self, aws_profile: str = None, region: str = None, namespace: str = "AWS/Resources"):
        """
        Inicializa el publicador de métricas.

        Args:
            aws_profile: Perfil de AWS a usar (opcional)
            region: Región de AWS (opcional)
            namespace: Namespace para las métricas (por defecto: AWS/Resources)
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
            self.namespace = namespace
            self.cloudwatch_client = session.client('cloudwatch', region_name=region)

            logger.info(f"✓ Región: {region}")
            logger.info(f"✓ Namespace: {namespace}")

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

    def publish_inventory_metrics(self, inventory: Dict[str, Any]) -> bool:
        """
        Publica métricas basadas en el inventario de recursos.

        Args:
            inventory: Diccionario del inventario generado por AWSResourceScanner

        Returns:
            True si se publicaron exitosamente, False en caso contrario
        """
        try:
            logger.info("📊 Publicando métricas en CloudWatch...")

            # Extraer datos del inventario
            resources = inventory.get('resources', {})
            metadata = inventory.get('metadata', {})

            # Preparar métricas
            metrics_data = []

            # Métrica general: Total de recursos
            total_resources = inventory.get('summary', {}).get('total_resources', 0)
            metrics_data.append({
                'MetricName': 'TotalResources',
                'Value': total_resources,
                'Unit': 'Count',
                'Timestamp': datetime.now(),
                'Dimensions': [
                    {
                        'Name': 'Account',
                        'Value': metadata.get('account_id', 'unknown')
                    },
                    {
                        'Name': 'Region',
                        'Value': metadata.get('region', 'unknown')
                    }
                ]
            })

            # Métricas por servicio
            service_counts = inventory.get('summary', {}).get('service_counts', {})
            for service, count in service_counts.items():
                metrics_data.append({
                    'MetricName': f'{service.upper()}Count',
                    'Value': count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {
                            'Name': 'Account',
                            'Value': metadata.get('account_id', 'unknown')
                        },
                        {
                            'Name': 'Region',
                            'Value': metadata.get('region', 'unknown')
                        }
                    ]
                })

            # Métricas específicas por servicio
            metrics_data.extend(self._generate_service_specific_metrics(resources, metadata))

            # Publicar métricas en lotes (máximo 20 por llamada)
            batch_size = 20
            for i in range(0, len(metrics_data), batch_size):
                batch = metrics_data[i:i + batch_size]
                self.cloudwatch_client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
                logger.info(f"✓ Publicados {len(batch)} métricas (lote {i//batch_size + 1})")

            logger.info(f"✓ Total métricas publicadas: {len(metrics_data)}")
            return True

        except ClientError as e:
            logger.error(f"❌ Error publicando métricas: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return False

    def _generate_service_specific_metrics(self, resources: Dict, metadata: Dict) -> List[Dict]:
        """
        Genera métricas específicas para cada servicio.

        Args:
            resources: Diccionario de recursos por servicio
            metadata: Metadatos del inventario

        Returns:
            Lista de métricas específicas
        """
        metrics = []
        account_id = metadata.get('account_id', 'unknown')
        region = metadata.get('region', 'unknown')

        # EC2 métricas específicas
        if 'ec2' in resources and isinstance(resources['ec2'], list):
            ec2_instances = resources['ec2']
            running_count = len([i for i in ec2_instances if i.get('State') == 'running'])
            stopped_count = len([i for i in ec2_instances if i.get('State') == 'stopped'])

            metrics.extend([
                {
                    'MetricName': 'EC2RunningInstances',
                    'Value': running_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                },
                {
                    'MetricName': 'EC2StoppedInstances',
                    'Value': stopped_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                }
            ])

        # RDS métricas específicas
        if 'rds' in resources and isinstance(resources['rds'], list):
            rds_instances = resources['rds']
            available_count = len([db for db in rds_instances if db.get('DBInstanceStatus') == 'available'])
            stopped_count = len([db for db in rds_instances if db.get('DBInstanceStatus') == 'stopped'])

            metrics.extend([
                {
                    'MetricName': 'RDSAvailableInstances',
                    'Value': available_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                },
                {
                    'MetricName': 'RDSStoppedInstances',
                    'Value': stopped_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                }
            ])

        # Lambda métricas específicas
        if 'lambda' in resources and isinstance(resources['lambda'], list):
            lambda_functions = resources['lambda']
            active_count = len([f for f in lambda_functions if f.get('State') == 'Active'])
            total_memory = sum([f.get('MemorySize', 0) for f in lambda_functions if f.get('State') == 'Active'])

            metrics.extend([
                {
                    'MetricName': 'LambdaActiveFunctions',
                    'Value': active_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                },
                {
                    'MetricName': 'LambdaTotalMemoryMB',
                    'Value': total_memory,
                    'Unit': 'Megabytes',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                }
            ])

        # EBS métricas específicas
        if 'ebs' in resources and isinstance(resources['ebs'], list):
            ebs_volumes = resources['ebs']
            in_use_count = len([v for v in ebs_volumes if v.get('State') == 'in-use'])
            available_count = len([v for v in ebs_volumes if v.get('State') == 'available'])
            total_size = sum([v.get('Size', 0) for v in ebs_volumes])

            metrics.extend([
                {
                    'MetricName': 'EBSVolumesInUse',
                    'Value': in_use_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                },
                {
                    'MetricName': 'EBSVolumesAvailable',
                    'Value': available_count,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                },
                {
                    'MetricName': 'EBSTotalSizeGB',
                    'Value': total_size,
                    'Unit': 'Gigabytes',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Account', 'Value': account_id},
                        {'Name': 'Region', 'Value': region}
                    ]
                }
            ])

        # S3 métricas específicas
        if 's3' in resources and isinstance(resources['s3'], list):
            s3_buckets = resources['s3']
            total_objects = sum([b.get('ObjectCount', 0) for b in s3_buckets if isinstance(b.get('ObjectCount'), int)])

            metrics.append({
                'MetricName': 'S3TotalObjects',
                'Value': total_objects,
                'Unit': 'Count',
                'Timestamp': datetime.now(),
                'Dimensions': [
                    {'Name': 'Account', 'Value': account_id}
                ]
            })

        return metrics

    def create_alarms(self) -> bool:
        """
        Crea alarmas predefinidas basadas en las métricas personalizadas.

        Returns:
            True si se crearon exitosamente, False en caso contrario
        """
        try:
            logger.info("🚨 Creando alarmas de CloudWatch...")

            alarms_created = 0

            # Definir alarmas predefinidas
            alarms = [
                {
                    'AlarmName': 'HighEC2InstanceCount',
                    'MetricName': 'EC2RunningInstances',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Threshold': 10,
                    'EvaluationPeriods': 1,
                    'Statistic': 'Maximum',
                    'Description': 'Alarma cuando hay más de 10 instancias EC2 ejecutándose'
                },
                {
                    'AlarmName': 'HighRDSInstanceCount',
                    'MetricName': 'RDSAvailableInstances',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Threshold': 5,
                    'EvaluationPeriods': 1,
                    'Statistic': 'Maximum',
                    'Description': 'Alarma cuando hay más de 5 instancias RDS disponibles'
                },
                {
                    'AlarmName': 'HighLambdaMemoryUsage',
                    'MetricName': 'LambdaTotalMemoryMB',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Threshold': 1024,
                    'EvaluationPeriods': 1,
                    'Statistic': 'Maximum',
                    'Description': 'Alarma cuando el uso total de memoria Lambda supera 1024MB'
                },
                {
                    'AlarmName': 'HighEBSVolumeCount',
                    'MetricName': 'EBSVolumesInUse',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Threshold': 20,
                    'EvaluationPeriods': 1,
                    'Statistic': 'Maximum',
                    'Description': 'Alarma cuando hay más de 20 volúmenes EBS en uso'
                }
            ]

            for alarm_config in alarms:
                try:
                    # Verificar si la alarma ya existe
                    existing_alarms = self.cloudwatch_client.describe_alarms(
                        AlarmNames=[alarm_config['AlarmName']]
                    )

                    if existing_alarms['MetricAlarms']:
                        logger.info(f"⚠️  Alarma '{alarm_config['AlarmName']}' ya existe, omitiendo")
                        continue

                    # Crear la alarma
                    self.cloudwatch_client.put_metric_alarm(
                        AlarmName=alarm_config['AlarmName'],
                        AlarmDescription=alarm_config['Description'],
                        MetricName=alarm_config['MetricName'],
                        Namespace=self.namespace,
                        Statistic=alarm_config['Statistic'],
                        ComparisonOperator=alarm_config['ComparisonOperator'],
                        Threshold=alarm_config['Threshold'],
                        EvaluationPeriods=alarm_config['EvaluationPeriods'],
                        TreatMissingData='notBreaching'
                    )

                    logger.info(f"✓ Alarma creada: {alarm_config['AlarmName']}")
                    alarms_created += 1

                except ClientError as e:
                    logger.error(f"❌ Error creando alarma '{alarm_config['AlarmName']}': {e}")

            logger.info(f"✓ Total alarmas creadas: {alarms_created}")
            return True

        except Exception as e:
            logger.error(f"❌ Error creando alarmas: {e}")
            return False

    def list_custom_metrics(self) -> List[Dict]:
        """
        Lista las métricas personalizadas en el namespace.

        Returns:
            Lista de métricas encontradas
        """
        try:
            logger.info(f"📋 Listando métricas en namespace: {self.namespace}")

            response = self.cloudwatch_client.list_metrics(Namespace=self.namespace)

            metrics = []
            for metric in response.get('Metrics', []):
                metrics.append({
                    'MetricName': metric.get('MetricName'),
                    'Dimensions': metric.get('Dimensions', []),
                    'Namespace': self.namespace
                })

            logger.info(f"✓ Encontradas {len(metrics)} métricas")
            return metrics

        except ClientError as e:
            logger.error(f"❌ Error listando métricas: {e}")
            return []

    def display_metrics_table(self, metrics: List[Dict]):
        """
        Muestra las métricas en formato de tabla.

        Args:
            metrics: Lista de métricas a mostrar
        """
        if not metrics:
            print("No se encontraron métricas personalizadas.")
            return

        print("\n" + "=" * 80)
        print(f"MÉTRICAS PERSONALIZADAS - Namespace: {self.namespace}")
        print("=" * 80)
        print(f"{'Métrica':<25} | {'Dimensiones'}")
        print("-" * 80)

        for metric in metrics:
            dimensions_str = ", ".join([
                f"{d['Name']}={d['Value']}" for d in metric.get('Dimensions', [])
            ])
            print(f"{metric['MetricName']:<25} | {dimensions_str}")

        print()


def load_inventory_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Carga un inventario desde un archivo JSON.

    Args:
        file_path: Ruta al archivo JSON

    Returns:
        Diccionario del inventario o None si hay error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        logger.info(f"✓ Inventario cargado desde: {file_path}")
        return inventory
    except FileNotFoundError:
        logger.error(f"❌ Archivo no encontrado: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error cargando archivo: {e}")
        return None


def main():
    """Función principal para CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema de alertas con métricas personalizadas en CloudWatch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python cloudwatch_metrics.py --inventory-file inventory.json --send-metrics
  python cloudwatch_metrics.py --create-alarms
  python cloudwatch_metrics.py --list-metrics --namespace AWS/Resources
        """
    )

    parser.add_argument('--profile', help='Perfil de AWS a usar')
    parser.add_argument('--region', help='Región de AWS (por defecto: us-east-1)')
    parser.add_argument('--namespace', default='AWS/Resources',
                       help='Namespace para métricas (por defecto: AWS/Resources)')
    parser.add_argument('--inventory-file', help='Archivo JSON del inventario para publicar métricas')
    parser.add_argument('--send-metrics', action='store_true',
                       help='Enviar métricas a CloudWatch desde el archivo de inventario')
    parser.add_argument('--create-alarms', action='store_true',
                       help='Crear alarmas predefinidas en CloudWatch')
    parser.add_argument('--list-metrics', action='store_true',
                       help='Listar métricas personalizadas')

    args = parser.parse_args()

    # Validar argumentos
    if not any([args.send_metrics, args.create_alarms, args.list_metrics]):
        parser.error("Debes especificar al menos una acción: --send-metrics, --create-alarms, o --list-metrics")

    if args.send_metrics and not args.inventory_file:
        parser.error("--send-metrics requiere --inventory-file")

    try:
        # Crear publicador
        publisher = CloudWatchMetricsPublisher(
            aws_profile=args.profile,
            region=args.region,
            namespace=args.namespace
        )

        # Ejecutar acciones
        success = True

        if args.send_metrics:
            inventory = load_inventory_from_file(args.inventory_file)
            if inventory:
                success &= publisher.publish_inventory_metrics(inventory)
            else:
                success = False

        if args.create_alarms:
            success &= publisher.create_alarms()

        if args.list_metrics:
            metrics = publisher.list_custom_metrics()
            publisher.display_metrics_table(metrics)

        if success:
            logger.info("✓ Operación completada exitosamente")
            return 0
        else:
            logger.error("❌ Una o más operaciones fallaron")
            return 1

    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        return 1
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())