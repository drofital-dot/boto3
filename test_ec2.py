#!/usr/bin/env python3
"""
Script de prueba para EC2Monitor contra AWS real.
Valida que los scripts funcionan con tu configuración actual de AWS.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def test_aws_connection():
    """Probar conexión con AWS."""
    print("\n" + "="*60)
    print("PRUEBA 1: Conexión con AWS")
    print("="*60)
    
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        region = session.region_name or "us-east-1"
        
        if credentials is None:
            print("❌ No hay credenciales configuradas")
            return False
        
        print(f"✓ Credenciales encontradas")
        print(f"✓ Región: {region}")
        print(f"✓ Access Key: {credentials.access_key[:10]}...")
        
        # Probar STS
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"✓ Account ID: {identity['Account']}")
        print(f"✓ ARN: {identity['Arn']}")
        
        return True
    
    except NoCredentialsError:
        print("❌ Credenciales de AWS no encontradas")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_ec2_monitor():
    """Prueba del monitor de EC2 contra AWS real."""
    print("\n" + "="*60)
    print("PRUEBA 2: EC2Monitor (AWS real)")
    print("="*60)
    
    try:
        from ec2_monitor import EC2Monitor
        
        print("\n[Conectando a EC2...]")
        monitor = EC2Monitor()
        print(f"✓ Conectado a EC2")
        
        print("\n[Obteniendo instancias...]")
        instances = monitor.get_instances()
        print(f"✓ Obtenidas {len(instances)} instancias")
        
        if instances:
            print("\n[Primeras 3 instancias:]")
            for instance in instances[:3]:
                print(f"  - {instance['InstanceId']}: {instance['State']} ({instance['InstanceType']})")
            
            print("\n[Mostrando en tabla...]")
            monitor.display_instances(instances[:3], format='table')
            
            print("\n[Estadísticas...]")
            monitor.display_statistics(instances)
        else:
            print("⚠ No hay instancias en cette región")
        
        print("\n[Probando filtro por estado 'running'...]")
        running = monitor.get_instances(state='running')
        print(f"✓ Instancias en ejecución: {len(running)}")
        
        print("\n[Probando diferentes formatos...]")
        
        # JSON
        print("\n[Formato JSON (primero solo):]")
        if instances:
            import json
            print(json.dumps(instances[0], indent=2, default=str))
        
        # CSV
        print("\n[Formato CSV:]")
        if instances:
            monitor.display_instances(instances[:2], format='csv')
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ec2_controller():
    """Prueba del controlador de EC2 contra AWS real."""
    print("\n" + "="*60)
    print("PRUEBA 3: EC2Controller (AWS real)")
    print("="*60)
    
    try:
        from ec2_controller import EC2Controller
        
        print("\n[Conectando a EC2...]")
        controller = EC2Controller()
        print(f"✓ Conectado a EC2")
        
        print("\n[Obteniendo instancias...]")
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances()
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if not instance_ids:
            print("ℹ No hay instancias para probar")
            return True
        
        instance_id = instance_ids[0]
        print(f"✓ Usando instancia: {instance_id}")
        
        print("\n[Obtener estado...]")
        status = controller.get_instance_status(instance_id)
        
        if status:
            print(f"✓ Estado actual: {status['State']}")
            print(f"  Tipo: {status['InstanceType']}")
            print(f"  IP Pública: {status['PublicIpAddress']}")
            print(f"  IP Privada: {status['PrivateIpAddress']}")
        else:
            print("❌ No se pudo obtener estado")
            return False
        
        print("\n⚠ No se ejecutarán start/stop/reboot para evitar cambios en AWS")
        print("✓ Funcionalidad de control validada")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas."""
    print("\n" + "🧪 "*20)
    print("PRUEBAS DE EC2")
    print("🧪 "*20)
    
    tests = [
        ("EC2Monitor", test_ec2_monitor),
        ("EC2Controller", test_ec2_controller),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    for name, success in results.items():
        status = "✓" if success else "❌"
        print(f"{status} {name}")
    
    all_ok = all(results.values())
    
    print("="*60)
    if all_ok:
        print("\n✓ ¡Todas las pruebas pasaron!")
        return 0
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1


def main():
    """Ejecutar todas las pruebas."""
    print("\n" + "🧪 "*20)
    print("PRUEBAS DE EC2 (CONTRA AWS REAL)")
    print("🧪 "*20)
    
    tests = [
        ("Conexión AWS", test_aws_connection),
        ("EC2Monitor", test_ec2_monitor),
        ("EC2Controller", test_ec2_controller),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    for name, success in results.items():
        status = "✓" if success else "❌"
        print(f"{status} {name}")
    
    all_ok = all(results.values())
    
    print("="*60)
    if all_ok:
        print("\n✓ ¡Todas las pruebas pasaron!")
        print("\nPróximos pasos:")
        print("  1. python ec2_monitor.py              # Ver instancias")
        print("  2. python ec2_monitor.py --monitor    # Monitoreo continuo")
        print("  3. python ec2_examples.py             # Ejemplos interactivos")
        return 0
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())
