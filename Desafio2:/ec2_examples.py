#!/usr/bin/env python3
"""
Ejemplos rápidos de uso de EC2 Monitor y Controller.
"""

from ec2_monitor import EC2Monitor
from ec2_controller import EC2Controller


# ============================================
# EJEMPLO 1: Listar todas las instancias
# ============================================

def example_list_all():
    """Listar todas las instancias."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Listar todas las instancias")
    print("="*60)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    monitor.display_instances(instances)
    monitor.display_statistics(instances)


# ============================================
# EJEMPLO 2: Filtrar por estado
# ============================================

def example_filter_running():
    """Mostrar solo instancias en ejecución."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Instancias en ejecución")
    print("="*60)
    
    monitor = EC2Monitor()
    running = monitor.get_instances(state='running')
    monitor.display_instances(running)


# ============================================
# EJEMPLO 3: Exportar a JSON
# ============================================

def example_export_json():
    """Exportar instancias a JSON."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Exportar a JSON")
    print("="*60)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    monitor.display_instances(instances, format='json')


# ============================================
# EJEMPLO 4: Exportar a CSV
# ============================================

def example_export_csv():
    """Exportar instancias a CSV."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Exportar a CSV")
    print("="*60)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    monitor.display_instances(instances, format='csv')


# ============================================
# EJEMPLO 5: Obtener estadísticas
# ============================================

def example_statistics():
    """Mostrar estadísticas."""
    print("\n" + "="*60)
    print("EJEMPLO 5: Estadísticas")
    print("="*60)
    
    monitor = EC2Monitor()
    instances = monitor.get_instances()
    monitor.display_statistics(instances)


# ============================================
# EJEMPLO 6: Iniciar una instancia
# ============================================

def example_start_instance():
    """Iniciar una instancia."""
    print("\n" + "="*60)
    print("EJEMPLO 6: Iniciar instancia")
    print("="*60)
    
    instance_id = input("ID de la instancia a iniciar: ").strip()
    
    if not instance_id:
        print("ID requerido")
        return
    
    controller = EC2Controller()
    controller.start_instances([instance_id])


# ============================================
# EJEMPLO 7: Detener una instancia
# ============================================

def example_stop_instance():
    """Detener una instancia."""
    print("\n" + "="*60)
    print("EJEMPLO 7: Detener instancia")
    print("="*60)
    
    instance_id = input("ID de la instancia a detener: ").strip()
    
    if not instance_id:
        print("ID requerido")
        return
    
    controller = EC2Controller()
    controller.stop_instances([instance_id])


# ============================================
# EJEMPLO 8: Ver estado de una instancia
# ============================================

def example_instance_status():
    """Ver estado de una instancia."""
    print("\n" + "="*60)
    print("EJEMPLO 8: Estado de instancia")
    print("="*60)
    
    instance_id = input("ID de la instancia: ").strip()
    
    if not instance_id:
        print("ID requerido")
        return
    
    controller = EC2Controller()
    status = controller.get_instance_status(instance_id)
    
    if status:
        print(f"\nEstado de {instance_id}:")
        for key, value in status.items():
            print(f"  {key}: {value}")


# ============================================
# EJEMPLO 9: Monitoreo en tiempo real
# ============================================

def example_continuous_monitoring():
    """Monitoreo en tiempo real."""
    print("\n" + "="*60)
    print("EJEMPLO 9: Monitoreo en tiempo real (Ctrl+C para salir)")
    print("="*60)
    
    monitor = EC2Monitor()
    monitor.monitor_continuous(interval=15)


# ============================================
# EJEMPLO 10: Script personalizado
# ============================================

def example_custom_script():
    """Script personalizado."""
    print("\n" + "="*60)
    print("EJEMPLO 10: Script personalizado")
    print("="*60)
    
    monitor = EC2Monitor()
    
    # Obtener todas las instancias
    all_instances = monitor.get_instances()
    
    # Filtrar por tipo
    t2_instances = [i for i in all_instances if 't2' in i['InstanceType']]
    
    print(f"\nInstancias t2 ({len(t2_instances)} total):")
    for instance in t2_instances:
        print(f"  - {instance['InstanceId']}: {instance['State']} ({instance['InstanceType']})")


# ============================================
# MENÚ PRINCIPAL
# ============================================

def main():
    """Menú principal."""
    examples = {
        '1': ('Listar todas las instancias', example_list_all),
        '2': ('Filtrar instancias en ejecución', example_filter_running),
        '3': ('Exportar a JSON', example_export_json),
        '4': ('Exportar a CSV', example_export_csv),
        '5': ('Estadísticas', example_statistics),
        '6': ('Iniciar instancia', example_start_instance),
        '7': ('Detener instancia', example_stop_instance),
        '8': ('Ver estado', example_instance_status),
        '9': ('Monitoreo en tiempo real', example_continuous_monitoring),
        '10': ('Script personalizado', example_custom_script),
    }
    
    while True:
        print("\n" + "="*60)
        print("EJEMPLOS DE USO EC2")
        print("="*60)
        
        for key, (description, _) in examples.items():
            print(f"{key}. {description}")
        print("0. Salir")
        
        choice = input("\nSelecciona una opción: ").strip()
        
        if choice == '0':
            print("Hasta luego!")
            break
        
        if choice in examples:
            _, example_func = examples[choice]
            try:
                example_func()
            except KeyboardInterrupt:
                print("\nCancelado")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Opción inválida")


if __name__ == "__main__":
    main()
