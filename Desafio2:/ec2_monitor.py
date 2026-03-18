#!/usr/bin/env python3
"""
Script para listar y monitorear instancias EC2.
Muestra información detallada de todas las instancias en tu cuenta AWS.
"""

import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EC2Monitor:
    """Monitor de instancias EC2."""
    
    def __init__(self, aws_profile: str = None, region: str = None):
        """
        Inicializar monitor de EC2.
        
        Args:
            aws_profile: Perfil de AWS a usar
            region: Región AWS (si None, usa la de las credenciales)
        """
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
            else:
                session = boto3.Session()
            
            # Si region no se especifica, usar la de la sesión
            if region is None:
                region = session.region_name or "us-east-1"
            
            self.ec2_client = session.client('ec2', region_name=region)
            self.region = region
            
            logger.info(f"✓ Conectado a EC2 en región: {region}")
        except NoCredentialsError:
            logger.error("❌ Credenciales de AWS no encontradas")
            raise
        except Exception as e:
            logger.error(f"❌ Error al conectar con EC2: {e}")
            raise
    
    def get_instances(self, filters: Dict = None, state: str = None) -> List[Dict]:
        """
        Obtener instancias EC2.
        
        Args:
            filters: Filtros adicionales (diccionario)
            state: Filtrar por estado (running, stopped, terminated, etc.)
            
        Returns:
            Lista de instancias con información detallada
        """
        try:
            # Construir filtros
            filter_list = []
            
            if state:
                filter_list.append({
                    'Name': 'instance-state-name',
                    'Values': [state]
                })
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_list.append({
                            'Name': key,
                            'Values': value
                        })
                    else:
                        filter_list.append({
                            'Name': key,
                            'Values': [value]
                        })
            
            # Obtener instancias
            response = self.ec2_client.describe_instances(Filters=filter_list)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance.get('InstanceId', 'N/A'),
                        'State': instance.get('State', {}).get('Name', 'N/A'),
                        'InstanceType': instance.get('InstanceType', 'N/A'),
                        'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'LaunchTime': instance.get('LaunchTime', 'N/A'),
                        'Tags': instance.get('Tags', []),
                        'KeyName': instance.get('KeyName', 'N/A'),
                        'SecurityGroups': instance.get('SecurityGroups', []),
                        'SubnetId': instance.get('SubnetId', 'N/A'),
                        'VpcId': instance.get('VpcId', 'N/A'),
                    })
            
            return instances
        
        except ClientError as e:
            logger.error(f"❌ Error al obtener instancias: {e}")
            return []
    
    def display_instances(self, instances: List[Dict], format: str = "table"):
        """
        Mostrar instancias de forma legible.
        
        Args:
            instances: Lista de instancias
            format: Formato de salida (table, json, csv)
        """
        if not instances:
            logger.info("ℹ No hay instancias disponibles")
            return
        
        if format == "json":
            self._display_json(instances)
        elif format == "csv":
            self._display_csv(instances)
        else:
            self._display_table(instances)
    
    def _display_table(self, instances: List[Dict]):
        """Mostrar en formato tabla."""
        print("\n" + "="*140)
        print("INSTANCIAS EC2")
        print("="*140)
        
        # Encabezados
        print(f"{'ID':<19} | {'Estado':<10} | {'Tipo':<12} | {'IP Pública':<18} | {'IP Privada':<16} | {'VPC':<12} | {'Nombre':<25}")
        print("-"*140)
        
        # Filas
        for instance in instances:
            name = self._get_instance_name(instance)
            state_color = self._get_state_color(instance['State'])
            
            # Mostrar IP pública con indicador si no está asignada
            public_ip = instance['PublicIpAddress'] if instance['PublicIpAddress'] != 'N/A' else '(Sin asignar)'
            
            print(f"{instance['InstanceId']:<19} | {state_color}{instance['State']:<10}\033[0m | "
                  f"{instance['InstanceType']:<12} | {public_ip:<18} | "
                  f"{instance['PrivateIpAddress']:<16} | {instance['VpcId']:<12} | {name:<25}")
        
        print("="*140)
    
    def _display_json(self, instances: List[Dict]):
        """Mostrar en formato JSON."""
        print("\n" + json.dumps(instances, indent=2, default=str))
    
    def _display_csv(self, instances: List[Dict]):
        """Mostrar en formato CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'InstanceId', 'State', 'InstanceType', 'PublicIpAddress', 
            'PrivateIpAddress', 'LaunchTime', 'KeyName'
        ])
        
        writer.writeheader()
        for instance in instances:
            writer.writerow({
                'InstanceId': instance['InstanceId'],
                'State': instance['State'],
                'InstanceType': instance['InstanceType'],
                'PublicIpAddress': instance['PublicIpAddress'],
                'PrivateIpAddress': instance['PrivateIpAddress'],
                'LaunchTime': instance['LaunchTime'],
                'KeyName': instance['KeyName']
            })
        
        print("\n" + output.getvalue())
    
    def _get_instance_name(self, instance: Dict) -> str:
        """Obtener nombre de la instancia desde los tags."""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return instance['InstanceId']
    
    def _get_state_color(self, state: str) -> str:
        """Obtener código de color para el estado."""
        colors = {
            'running': '\033[92m',      # Verde
            'stopped': '\033[93m',      # Amarillo
            'terminated': '\033[91m',   # Rojo
            'stopping': '\033[93m',     # Amarillo
            'pending': '\033[94m'       # Azul
        }
        return colors.get(state, '\033[0m')
    
    def get_statistics(self, instances: List[Dict]) -> Dict:
        """
        Obtener estadísticas de instancias.
        
        Args:
            instances: Lista de instancias
            
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total': len(instances),
            'running': len([i for i in instances if i['State'] == 'running']),
            'stopped': len([i for i in instances if i['State'] == 'stopped']),
            'terminated': len([i for i in instances if i['State'] == 'terminated']),
            'with_public_ip': len([i for i in instances if i['PublicIpAddress'] != 'N/A']),
        }
        
        # Contar por tipo
        types = {}
        for instance in instances:
            itype = instance['InstanceType']
            types[itype] = types.get(itype, 0) + 1
        stats['by_type'] = types
        
        return stats
    
    def display_statistics(self, instances: List[Dict]):
        """Mostrar estadísticas."""
        stats = self.get_statistics(instances)
        
        print("\n" + "="*50)
        print("ESTADÍSTICAS")
        print("="*50)
        print(f"Total de instancias: {stats['total']}")
        print(f"  En ejecución: {stats['running']}")
        print(f"  Detenidas: {stats['stopped']}")
        print(f"  Terminadas: {stats['terminated']}")
        print(f"  Con IP pública: {stats['with_public_ip']}")
        
        if stats['by_type']:
            print(f"\nPor tipo de instancia:")
            for itype, count in stats['by_type'].items():
                print(f"  {itype}: {count}")
        
        print("="*50 + "\n")
    
    def show_instance_details(self, instance_id: str):
        """
        Mostrar detalles completos de una instancia.
        
        Args:
            instance_id: ID de la instancia
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            
            if not response['Reservations']:
                logger.error(f"Instancia no encontrada: {instance_id}")
                return
            
            instance = response['Reservations'][0]['Instances'][0]
            
            print("\n" + "="*60)
            print(f"DETALLES DE {instance_id}")
            print("="*60)
            
            # Información básica
            print(f"\n📋 Información Básica:")
            print(f"  Nombre: {self._get_instance_name(instance)}")
            print(f"  Estado: {instance.get('State', {}).get('Name', 'N/A')}")
            print(f"  Tipo: {instance.get('InstanceType', 'N/A')}")
            print(f"  Criada: {instance.get('LaunchTime', 'N/A')}")
            
            # Información de red
            print(f"\n🌐 Información de Red:")
            print(f"  VPC ID: {instance.get('VpcId', 'N/A')}")
            print(f"  Subnet ID: {instance.get('SubnetId', 'N/A')}")
            print(f"  IP Privada: {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"  IP Pública: {instance.get('PublicIpAddress', '(Sin asignar)')}")
            
            # Información de seguridad
            print(f"\n🔐 Security Groups:")
            for sg in instance.get('SecurityGroups', []):
                print(f"  - {sg['GroupName']} ({sg['GroupId']})")
            
            # Network Interfaces
            print(f"\n📡 Network Interfaces:")
            for eni in instance.get('NetworkInterfaces', []):
                print(f"  - {eni['NetworkInterfaceId']}")
                print(f"    IP Privada: {eni['PrivateIpAddress']}")
                if eni.get('Association'):
                    print(f"    IP Pública: {eni['Association'].get('PublicIp', '(Sin asignar)')}")
                print(f"    Estado: {eni.get('Status', 'N/A')}")
            
            # Tags
            print(f"\n🏷️  Tags:")
            if instance.get('Tags'):
                for tag in instance['Tags']:
                    print(f"  {tag['Key']}: {tag['Value']}")
            else:
                print("  (Sin tags)")
            
            # Storage
            print(f"\n💾 Volúmenes:")
            for device in instance.get('BlockDeviceMappings', []):
                print(f"  - {device['DeviceName']}: {device['Ebs']['VolumeId']}")
            
            print("="*60 + "\n")
        
        except Exception as e:
            logger.error(f"Error al obtener detalles: {e}")
    
    def monitor_continuous(self, interval: int = 30, filters: Dict = None):
        """
        Monitorear instancias en tiempo real.
        
        Args:
            interval: Segundos entre actualizaciones
            filters: Filtros para las instancias
        """
        import time
        
        logger.info(f"Iniciando monitoreo continuo (actualización cada {interval}s)")
        logger.info("Presiona Ctrl+C para salir")
        
        try:
            while True:
                # Limpiar pantalla
                import os
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Obtener instancias
                instances = self.get_instances(filters=filters)
                
                # Mostrar
                print(f"\n🔄 Actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.display_instances(instances)
                self.display_statistics(instances)
                
                # Esperar
                print(f"Próxima actualización en {interval}s... (Ctrl+C para salir)")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\nMonitoreo detenido")
            return


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Listar y monitorear instancias EC2")
    parser.add_argument("--profile", default=None, help="Perfil de AWS a usar")
    parser.add_argument("--region", default=None, help="Región AWS (default: usa la de 'aws configure')")
    parser.add_argument("--state", default=None, 
                       choices=['running', 'stopped', 'terminated', 'stopping', 'pending'],
                       help="Filtrar por estado")
    parser.add_argument("--format", default="table", 
                       choices=['table', 'json', 'csv'],
                       help="Formato de salida")
    parser.add_argument("--monitor", action="store_true", help="Modo de monitoreo continuo")
    parser.add_argument("--interval", type=int, default=30, help="Segundos entre actualizaciones (por defecto 30)")
    parser.add_argument("--stats", action="store_true", help="Mostrar solo estadísticas")
    parser.add_argument("--running-only", action="store_true", help="Mostrar solo instancias en ejecución")
    
    args = parser.parse_args()
    
    try:
        # Crear monitor
        monitor = EC2Monitor(args.profile, args.region)
        
        # Filtros
        state_filter = None
        if args.running_only:
            state_filter = 'running'
        elif args.state:
            state_filter = args.state
        
        if args.monitor:
            # Modo continuo
            monitor.monitor_continuous(args.interval, filters=None)
        else:
            # Modo único
            instances = monitor.get_instances(state=state_filter)
            
            if args.stats:
                monitor.display_statistics(instances)
            else:
                monitor.display_instances(instances, format=args.format)
                monitor.display_statistics(instances)
    
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
