#!/usr/bin/env python3
"""
Script para controlar instancias EC2 (iniciar, detener, reiniciar).
Permite gestionar el ciclo de vida de las instancias.
"""

import sys
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EC2Controller:
    """Controlador de instancias EC2."""
    
    def __init__(self, aws_profile: str = None, region: str = None):
        """
        Inicializar controlador de EC2.
        
        Args:
            aws_profile: Perfil de AWS a usar
            region: Región AWS (si None, usa la de las credenciales)
        """
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
            else:
                session = boto3.Session()
            
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
    
    def start_instances(self, instance_ids: List[str]) -> bool:
        """
        Iniciar instancias.
        
        Args:
            instance_ids: Lista de IDs de instancias
            
        Returns:
            True si fue exitoso
        """
        try:
            logger.info(f"Iniciando instancias: {instance_ids}")
            self.ec2_client.start_instances(InstanceIds=instance_ids)
            logger.info("✓ Instancias iniciadas")
            return True
        except ClientError as e:
            logger.error(f"❌ Error al iniciar instancias: {e}")
            return False
    
    def stop_instances(self, instance_ids: List[str], force: bool = False) -> bool:
        """
        Detener instancias.
        
        Args:
            instance_ids: Lista de IDs de instancias
            force: Fuerza la detención (sin esperar)
            
        Returns:
            True si fue exitoso
        """
        try:
            logger.info(f"Deteniendo instancias: {instance_ids}")
            self.ec2_client.stop_instances(InstanceIds=instance_ids, Force=force)
            logger.info("✓ Instancias detenidas")
            return True
        except ClientError as e:
            logger.error(f"❌ Error al detener instancias: {e}")
            return False
    
    def reboot_instances(self, instance_ids: List[str]) -> bool:
        """
        Reiniciar instancias.
        
        Args:
            instance_ids: Lista de IDs de instancias
            
        Returns:
            True si fue exitoso
        """
        try:
            logger.info(f"Reiniciando instancias: {instance_ids}")
            self.ec2_client.reboot_instances(InstanceIds=instance_ids)
            logger.info("✓ Instancias reiniciadas")
            return True
        except ClientError as e:
            logger.error(f"❌ Error al reiniciar instancias: {e}")
            return False
    
    def terminate_instances(self, instance_ids: List[str]) -> bool:
        """
        Terminar instancias (PELIGROSO - no se puede revertir).
        
        Args:
            instance_ids: Lista de IDs de instancias
            
        Returns:
            True si fue exitoso
        """
        try:
            logger.warning(f"⚠️  ADVERTENCIA: Terminando instancias (no se puede revertir): {instance_ids}")
            confirmation = input("¿Estás seguro? (s/n): ").strip().lower()
            
            if confirmation not in ['s', 'si', 'yes']:
                logger.info("Operación cancelada")
                return False
            
            self.ec2_client.terminate_instances(InstanceIds=instance_ids)
            logger.info("✓ Instancias terminadas")
            return True
        except ClientError as e:
            logger.error(f"❌ Error al terminar instancias: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> dict:
        """
        Obtener estado de una instancia.
        
        Args:
            instance_id: ID de la instancia
            
        Returns:
            Diccionario con información de estado
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            
            if response['Reservations']:
                instance = response['Reservations'][0]['Instances'][0]
                return {
                    'InstanceId': instance.get('InstanceId', 'N/A'),
                    'State': instance.get('State', {}).get('Name', 'N/A'),
                    'InstanceType': instance.get('InstanceType', 'N/A'),
                    'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                    'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                    'LaunchTime': instance.get('LaunchTime', 'N/A'),
                }
            return None
        except ClientError as e:
            logger.error(f"❌ Error al obtener estado: {e}")
            return None
    
    def wait_for_state(self, instance_id: str, target_state: str, max_attempts: int = 40) -> bool:
        """
        Esperar a que una instancia alcance un estado.
        
        Args:
            instance_id: ID de la instancia
            target_state: Estado destino
            max_attempts: Máximo de intentos
            
        Returns:
            True si alcanzó el estado
        """
        import time
        
        logger.info(f"Esperando que {instance_id} alcance estado '{target_state}'...")
        
        for attempt in range(max_attempts):
            status = self.get_instance_status(instance_id)
            
            if status and status['State'] == target_state:
                logger.info(f"✓ Instancia en estado '{target_state}'")
                return True
            
            logger.info(f"  Intento {attempt + 1}/{max_attempts}: {status['State'] if status else 'N/A'}")
            time.sleep(3)
        
        logger.warning(f"⚠️  Timeout esperando estado '{target_state}'")
        return False


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Controlar instancias EC2")
    parser.add_argument("--profile", default=None, help="Perfil de AWS a usar")
    parser.add_argument("--region", default=None, help="Región AWS")
    
    # Subcomandos
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # Start
    start_parser = subparsers.add_parser('start', help='Iniciar instancias')
    start_parser.add_argument('instance_ids', nargs='+', help='IDs de instancias')
    
    # Stop
    stop_parser = subparsers.add_parser('stop', help='Detener instancias')
    stop_parser.add_argument('instance_ids', nargs='+', help='IDs de instancias')
    stop_parser.add_argument('--force', action='store_true', help='Fuerza la detención')
    
    # Reboot
    reboot_parser = subparsers.add_parser('reboot', help='Reiniciar instancias')
    reboot_parser.add_argument('instance_ids', nargs='+', help='IDs de instancias')
    
    # Terminate
    terminate_parser = subparsers.add_parser('terminate', help='Terminar instancias')
    terminate_parser.add_argument('instance_ids', nargs='+', help='IDs de instancias')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Verificar estado de instancia')
    status_parser.add_argument('instance_id', help='ID de la instancia')
    status_parser.add_argument('--wait', help='Esperar a este estado')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        controller = EC2Controller(args.profile, args.region)
        
        if args.command == 'start':
            success = controller.start_instances(args.instance_ids)
        
        elif args.command == 'stop':
            success = controller.stop_instances(args.instance_ids, args.force)
        
        elif args.command == 'reboot':
            success = controller.reboot_instances(args.instance_ids)
        
        elif args.command == 'terminate':
            success = controller.terminate_instances(args.instance_ids)
        
        elif args.command == 'status':
            status = controller.get_instance_status(args.instance_id)
            
            if status:
                print(f"\nEstado de {args.instance_id}:")
                print(f"  Estado: {status['State']}")
                print(f"  Tipo: {status['InstanceType']}")
                print(f"  IP Pública: {status['PublicIpAddress']}")
                print(f"  IP Privada: {status['PrivateIpAddress']}")
                print(f"  Iniciada: {status['LaunchTime']}\n")
                
                if args.wait:
                    success = controller.wait_for_state(args.instance_id, args.wait)
            else:
                success = False
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
