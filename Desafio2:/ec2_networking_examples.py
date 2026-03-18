#!/usr/bin/env python3
"""
EC2 Networking Examples - Ejemplos de cómo acceder a información de red detallada
Demuestra las diferentes formas de obtener información de conectividad de instancias
"""

import sys
from ec2_monitor import EC2Monitor
from ec2_detailed_view import EC2DetailedView
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_network_info():
    """Ejemplo 1: Información básica de red de todas las instancias"""
    print("\n" + "="*70)
    print("EJEMPLO 1: Información Básica de Red")
    print("="*70)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    
    if not instances:
        print("\n❌ No hay instancias EC2 disponibles.\n")
        return
    
    print(f"\nSe encontraron {len(instances)} instancia(s):\n")
    
    for instance in instances:
        print(f"  🔹 {instance['InstanceId']}")
        print(f"     IP Privada: {instance['PrivateIpAddress']}")
        print(f"     IP Pública: {instance['PublicIpAddress']}")
        print(f"     VPC: {instance['VpcId']}")
        print()


def example_2_filtering_by_state():
    """Ejemplo 2: Filtrar instancias por estado"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Filtrar por Estado")
    print("="*70)
    
    monitor = EC2Monitor()
    
    # Obtener solo instancias en ejecución
    running = monitor.get_instances(filters={'instance-state-name': 'running'})
    
    print(f"\nInstancias en ejecución: {len(running)}")
    for instance in running:
        print(f"  🟢 {instance['InstanceId']}")
        print(f"     IP: {instance['PublicIpAddress']} (privada: {instance['PrivateIpAddress']})")


def example_3_vpc_subnet_info():
    """Ejemplo 3: Información de VPC y Subnet"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Información de VPC y Subnet")
    print("="*70)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    
    if not instances:
        print("\n❌ No hay instancias EC2 disponibles.\n")
        return
    
    print("\n")
    for instance in instances:
        print(f"  📍 {instance['InstanceId']}")
        print(f"     VPC: {instance['VpcId']}")
        print(f"     Subnet: {instance['SubnetId']}")
        print(f"     AZ: {instance['Placement']['AvailabilityZone']}")
        print()


def example_4_detailed_view_interactive():
    """Ejemplo 4: Visualizador interactivo detallado"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Visualizador Interactivo Detallado")
    print("="*70)
    print("""
Este ejemplo inicia un menú interactivo donde puedes:
  1. Ver lista de todas tus instancias EC2
  2. Seleccionar una instancia
  3. Ver TODOS sus detalles de red:
     - Network Interfaces (ENI)
     - IPs privadas y públicas
     - Security Groups
     - Volúmenes
     - Tags
     - Y más...

Iniciando menú interactivo...
""")
    
    view = EC2DetailedView()
    view.interactive_menu()


def example_5_raw_networking_details():
    """Ejemplo 5: Detalles de red sin filtros (datos crudos)"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Detalles de Red Completos (Datos Crudos)")
    print("="*70)
    
    monitor = EC2Monitor()
    
    # Demostración de acceso directo a datos crudos
    try:
        response = monitor.ec2_client.describe_instances()
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                
                print(f"\n  📍 {instance_id}")
                
                # Network Interfaces
                for eni in instance.get('NetworkInterfaces', []):
                    print(f"     🔗 ENI: {eni['NetworkInterfaceId']}")
                    print(f"        MAC: {eni.get('MacAddress', 'N/A')}")
                    
                    # IP privada
                    print(f"        IP Privada: {eni['PrivateIpAddress']}")
                    
                    # IPs privadas adicionales
                    private_ips = [ip['PrivateIpAddress'] for ip in eni.get('PrivateIpAddresses', []) if ip['PrivateIpAddress'] != eni['PrivateIpAddress']]
                    if private_ips:
                        print(f"        IPs Privadas Adicionales: {', '.join(private_ips)}")
                    
                    # IP pública
                    if eni.get('Association'):
                        print(f"        IP Pública: {eni['Association'].get('PublicIp', 'N/A')}")
                    else:
                        print(f"        IP Pública: (Sin asignar)")
    
    except Exception as e:
        logger.error(f"Error: {e}")


def show_menu():
    """Mostrar menú de ejemplos"""
    print("\n" + "="*70)
    print("EC2 NETWORKING EXAMPLES - Ejemplos de Información de Red")
    print("="*70)
    print("""
Selecciona un ejemplo para ejecutar:

1. Información básica de red de todas las instancias
2. Filtrar instancias por estado
3. Ver información de VPC y Subnet
4. Visualizador interactivo con detalles completos
5. Detalles de red sin filtros (datos crudos)
6. Salir
""")


def main():
    """Función principal"""
    
    while True:
        show_menu()
        
        choice = input("Selecciona un ejemplo (1-6): ").strip()
        
        if choice == '1':
            example_1_basic_network_info()
        elif choice == '2':
            example_2_filtering_by_state()
        elif choice == '3':
            example_3_vpc_subnet_info()
        elif choice == '4':
            example_4_detailed_view_interactive()
        elif choice == '5':
            example_5_raw_networking_details()
        elif choice == '6':
            print("\n👋 ¡Hasta luego!\n")
            sys.exit(0)
        else:
            print("\n❌ Opción inválida. Por favor, selecciona un número entre 1 y 6.\n")
        
        input("\nPresiona Enter para continuar...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario.\n")
        sys.exit(0)
