#!/usr/bin/env python3
"""
EC2 Detailed View - Visualizador interactivo de detalles de instancias EC2
Permite seleccionar una instancia y ver toda la información de red disponible
"""

import sys
import logging
from typing import List, Dict
from ec2_monitor import EC2Monitor
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EC2DetailedView:
    """Interfaz interactiva para ver detalles de instancias EC2"""
    
    def __init__(self):
        """Inicializar monitor EC2"""
        self.monitor = EC2Monitor()
        self.instances = []
    
    def refresh_instances(self) -> bool:
        """
        Refrescar lista de instancias
        
        Returns:
            True si hay instancias, False si no
        """
        try:
            self.instances = self.monitor.get_instances()
            return len(self.instances) > 0
        except Exception as e:
            logger.error(f"Error al obtener instancias: {e}")
            return False
    
    def show_instance_list(self):
        """Mostrar lista de instancias numerada"""
        if not self.instances:
            print("\n❌ No hay instancias EC2 disponibles en esta región.")
            print("   Considera crear una instancia para ver detalles de red.\n")
            return False
        
        print("\n" + "="*70)
        print("INSTANCIAS EC2 DISPONIBLES")
        print("="*70)
        
        for idx, instance in enumerate(self.instances, 1):
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            instance_type = instance.get('InstanceType', 'N/A')
            name = self._get_instance_name(instance)
            
            # Emoji según estado
            state_emoji = {
                'running': '🟢',
                'stopped': '🔴',
                'stopping': '🟡',
                'starting': '🟡',
                'terminated': '⚫',
                'terminating': '⚫'
            }
            
            emoji = state_emoji.get(state, '❓')
            
            print(f"\n  {idx}. {emoji} {instance_id}")
            print(f"     Nombre: {name}")
            print(f"     Estado: {state}")
            print(f"     Tipo: {instance_type}")
            print(f"     IP Privada: {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"     IP Pública: {instance.get('PublicIpAddress', '(Sin asignar)')}")
        
        print("\n" + "="*70 + "\n")
        return True
    
    def _get_instance_name(self, instance: Dict) -> str:
        """Obtener nombre de instancia desde tags"""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return '(Sin nombre)'
    
    def show_networking_details(self, instance_id: str):
        """Mostrar detalles completos de red"""
        try:
            response = self.monitor.ec2_client.describe_instances(
                InstanceIds=[instance_id]
            )
            
            if not response['Reservations']:
                print(f"\n❌ Instancia no encontrada: {instance_id}\n")
                return
            
            instance = response['Reservations'][0]['Instances'][0]
            
            print("\n" + "="*70)
            print(f"DETALLES DE RED: {instance_id}")
            print("="*70)
            
            # Información básica
            print(f"\n📋 Información Básica:")
            print(f"  Nombre: {self._get_instance_name(instance)}")
            print(f"  Estado: {instance.get('State', {}).get('Name', 'N/A')}")
            print(f"  Tipo: {instance.get('InstanceType', 'N/A')}")
            print(f"  Región: {instance.get('Placement', {}).get('AvailabilityZone', 'N/A')}")
            
            # Información de red principal
            print(f"\n🌐 Red Principal:")
            print(f"  VPC ID: {instance.get('VpcId', 'N/A')}")
            print(f"  Subnet ID: {instance.get('SubnetId', 'N/A')}")
            print(f"  IP Privada Principal: {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"  IP Pública: {instance.get('PublicIpAddress', '(Sin asignar)')}")
            
            # Información de seguridad
            print(f"\n🔐 Security Groups:")
            sg_found = False
            for sg in instance.get('SecurityGroups', []):
                sg_found = True
                print(f"  - {sg['GroupName']}")
                print(f"    ID: {sg['GroupId']}")
            
            if not sg_found:
                print("  (Sin security groups)")
            
            # Network Interfaces - Información detallada
            print(f"\n📡 Network Interfaces (ENI):")
            if instance.get('NetworkInterfaces'):
                for eni_idx, eni in enumerate(instance['NetworkInterfaces'], 1):
                    print(f"\n  ENI #{eni_idx}: {eni['NetworkInterfaceId']}")
                    print(f"    Estado: {eni.get('Status', 'N/A')}")
                    print(f"    MAC: {eni.get('MacAddress', 'N/A')}")
                    print(f"    IP Privada Principal: {eni['PrivateIpAddress']}")
                    
                    # IPs privadas adicionales
                    private_ips = eni.get('PrivateIpAddresses', [])
                    if len(private_ips) > 1:
                        print(f"    IPs Privadas Adicionales:")
                        for ip_info in private_ips[1:]:
                            print(f"      - {ip_info['PrivateIpAddress']}")
                    
                    # Información de IP pública
                    if eni.get('Association'):
                        assoc = eni['Association']
                        print(f"    IP Pública: {assoc.get('PublicIp', 'N/A')}")
                        if assoc.get('PublicDnsName'):
                            print(f"    DNS Público: {assoc['PublicDnsName']}")
                    else:
                        print(f"    IP Pública: (Sin asignar)")
                    
                    # Security Groups en la ENI
                    if eni.get('Groups'):
                        print(f"    Security Groups:")
                        for sg in eni['Groups']:
                            print(f"      - {sg['GroupName']} ({sg['GroupId']})")
            else:
                print("  (Sin network interfaces)")
            
            # Volúmenes
            print(f"\n💾 Almacenamiento (EBS):")
            if instance.get('BlockDeviceMappings'):
                for device in instance['BlockDeviceMappings']:
                    print(f"  - {device['DeviceName']}: {device['Ebs']['VolumeId']}")
            else:
                print("  (Sin volúmenes)")
            
            # IAM Role
            iam = instance.get('IamInstanceProfile')
            if iam:
                print(f"\n👤 IAM Role:")
                print(f"  {iam.get('Arn', 'N/A')}")
            
            # Tags
            print(f"\n🏷️  Tags:")
            if instance.get('Tags'):
                for tag in instance['Tags']:
                    print(f"  {tag['Key']}: {tag['Value']}")
            else:
                print("  (Sin tags)")
            
            print("\n" + "="*70 + "\n")
        
        except ClientError as e:
            logger.error(f"Error de AWS: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def interactive_menu(self):
        """Mostrar menú interactivo"""
        while True:
            # Refrescar instancias
            if not self.refresh_instances():
                print("\n⚠️  No se pueden obtener instancias. Verifica tu configuración de AWS.")
                return
            
            # Mostrar lista
            if not self.show_instance_list():
                return
            
            # Opciones
            print("OPCIONES:")
            print("  [número] - Ver detalles de red completos")
            print("  [R] - Refrescar lista")
            print("  [Q] - Salir\n")
            
            choice = input("Selecciona una opción: ").strip().upper()
            
            if choice == 'Q':
                print("\n👋 ¡Hasta luego!\n")
                return
            
            if choice == 'R':
                print("\n🔄 Refrescando...\n")
                continue
            
            # Validar número
            try:
                idx = int(choice)
                if 1 <= idx <= len(self.instances):
                    instance_id = self.instances[idx - 1]['InstanceId']
                    self.show_networking_details(instance_id)
                    input("\nPresiona Enter para continuar...")
                else:
                    print(f"\n❌ Opción inválida. Por favor, selecciona un número entre 1 y {len(self.instances)}.\n")
            except ValueError:
                print(f"\n❌ Opción inválida: '{choice}'.\n")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("EC2 DETAILED VIEW - Visualizador de Detalles de Instancias EC2")
    print("="*70)
    
    try:
        view = EC2DetailedView()
        view.interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario.\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
