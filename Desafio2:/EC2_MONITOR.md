# EC2 Monitor y Control

Scripts para listar, monitorear y controlar instancias EC2 en AWS.

## 📋 Características

### EC2 Monitor (`ec2_monitor.py`)
- ✅ Listar todas las instancias EC2
- ✅ Mostrar: Instance ID, estado, tipo, IPs (pública/privada)
- ✅ Filtrar por estado (running, stopped, terminated, etc.)
- ✅ Mostrar en múltiples formatos (tabla, JSON, CSV)
- ✅ Estadísticas de instancias
- ✅ Monitoreo continuo en tiempo real
- ✅ Colores en la terminal para mejor visualización

### EC2 Controller (`ec2_controller.py`)
- ✅ Iniciar instancias
- ✅ Detener instancias
- ✅ Reiniciar instancias
- ✅ Terminar instancias
- ✅ Verificar estado
- ✅ Esperar a que alcance un estado específico

---

## 🚀 Uso rápido

### Listar todas las instancias
```bash
python ec2_monitor.py
```

### Ver solo instancias en ejecución
```bash
python ec2_monitor.py --running-only
```

### Mostrar en formato JSON
```bash
python ec2_monitor.py --format json
```

### Mostrar en formato CSV
```bash
python ec2_monitor.py --format csv
```

### Monitoreo en tiempo real (actualiza cada 30s)
```bash
python ec2_monitor.py --monitor
```

### Monitoreo personalizado (actualiza cada 10s)
```bash
python ec2_monitor.py --monitor --interval 10
```

### Solo estadísticas
```bash
python ec2_monitor.py --stats
```

### Filtrar por estado específico
```bash
python ec2_monitor.py --state running
python ec2_monitor.py --state stopped
python ec2_monitor.py --state terminated
```

---

## 🎮 Control de instancias

### Ver ayuda
```bash
python ec2_controller.py --help
```

### Iniciar instancia
```bash
python ec2_controller.py start i-1234567890abcdef0
```

### Iniciar múltiples instancias
```bash
python ec2_controller.py start i-1111111111111111 i-2222222222222222
```

### Detener instancia (espera gracefully)
```bash
python ec2_controller.py stop i-1234567890abcdef0
```

### Detener forzadamente
```bash
python ec2_controller.py stop i-1234567890abcdef0 --force
```

### Reiniciar instancia
```bash
python ec2_controller.py reboot i-1234567890abcdef0
```

### Terminar instancia (PELIGROSO)
```bash
python ec2_controller.py terminate i-1234567890abcdef0
```

### Ver estado de una instancia
```bash
python ec2_controller.py status i-1234567890abcdef0
```

### Ver estado y esperar a que esté "running"
```bash
python ec2_controller.py status i-1234567890abcdef0 --wait running
```

---

## 📊 Ejemplos de salida

### Formato tabla (default)
```
============================================================
INSTANCIAS EC2
============================================================
ID               | Estado     | Tipo         | IP Pública      | IP Privada      | Nombre
i-0abc123def456  | running    | t2.micro     | 52.10.20.30     | 10.0.1.100      | webserver-1
i-1def234abc567  | stopped    | t2.small     | N/A             | 10.0.2.50       | database-1
i-2abc345def678  | running    | t3.medium    | 54.20.10.40     | 10.0.3.200      | api-server-1
============================================================
```

### Estadísticas
```
==================================================
ESTADÍSTICAS
==================================================
Total de instancias: 3
  En ejecución: 2
  Detenidas: 1
  Terminadas: 0
  Con IP pública: 2

Por tipo de instancia:
  t2.micro: 1
  t2.small: 1
  t3.medium: 1
==================================================
```

### Monitoreo continuo
```
🔄 Actualización: 2026-03-18 14:30:45

============================================================
INSTANCIAS EC2
============================================================
ID               | Estado     | Tipo         | IP Pública      | IP Privada      | Nombre
i-0abc123def456  | running    | t2.micro     | 52.10.20.30     | 10.0.1.100      | webserver-1
...

Próxima actualización en 30s... (Ctrl+C para salir)
```

---

## 🔍 Casos de uso

### Caso 1: Monitorear instancias
```bash
# Monitoreo en tiempo real
python ec2_monitor.py --monitor --interval 15
```

### Caso 2: Exportar inventario
```bash
# Exportar a CSV
python ec2_monitor.py --format csv > inventario.csv
```

### Caso 3: Iniciar todas las instancias paradas
```bash
# Ver cuáles están paradas
python ec2_monitor.py --state stopped

# Iniciar una (reemplazar con los IDs reales)
python ec2_controller.py start i-1111111111111111 i-2222222222222222
```

### Caso 4: Reiniciar una instancia
```bash
# Ver estado actual
python ec2_controller.py status i-1234567890abcdef0

# Reiniciar
python ec2_controller.py reboot i-1234567890abcdef0

# Esperar a que esté running de nuevo
python ec2_controller.py status i-1234567890abcdef0 --wait running
```

### Caso 5: Dashboard personalizado (bash)
```bash
#!/bin/bash
while true; do
    clear
    python ec2_monitor.py --format table
    sleep 30
done
```

---

## 🔧 Uso en Python

### Monitor
```python
from ec2_monitor import EC2Monitor

# Crear monitor
monitor = EC2Monitor(region='us-east-1')

# Obtener instancias en ejecución
running = monitor.get_instances(state='running')

# Mostrar en tabla
monitor.display_instances(running)

# Obtener estadísticas
stats = monitor.get_statistics(running)
print(f"Total en ejecución: {stats['running']}")
```

### Controller
```python
from ec2_controller import EC2Controller

# Crear controlador
controller = EC2Controller(region='us-east-1')

# Iniciar instancia
controller.start_instances(['i-1234567890abcdef0'])

# Obtener estado
status = controller.get_instance_status('i-1234567890abcdef0')
print(f"Estado actual: {status['State']}")

# Esperar a que esté running
controller.wait_for_state('i-1234567890abcdef0', 'running')
```

---

## 🔐 Permisos necesarios en IAM

El usuario de AWS necesita estos permisos:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:RebootInstances",
                "ec2:TerminateInstances"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## 🧪 Pruebas

### Ejecutar pruebas (usando moto - sin AWS real)
```bash
python test_ec2.py
```

Esto probará:
- Crear instancias de prueba
- Listar instancias
- Mostrar en diferentes formatos
- Controlar instancias (start, stop, reboot)

---

## 📝 Opciones de línea de comandos

### EC2 Monitor
```
--profile PROFILE          Perfil de AWS a usar
--region REGION           Región AWS (default: usa la de aws configure)
--state {running,stopped} Filtrar por estado
--format {table,json,csv} Formato de salida
--monitor                 Modo de monitoreo continuo
--interval SECONDS        Segundos entre actualizaciones
--stats                   Mostrar solo estadísticas
--running-only           Mostrar solo instancias en ejecución
```

### EC2 Controller
```
start <IDs>              Iniciar instancias
stop <IDs>               Detener instancias
  --force               Fuerza la detención
reboot <IDs>             Reiniciar instancias
terminate <IDs>          Terminar instancias
status <ID>              Ver estado
  --wait STATE          Esperar a estado específico
```

---

## ⚠️ Advertencias

- **Terminar es irreversible**: No se puede deshacer. Asegúrate antes de terminar.
- **Costos**: Las instancias en ejecución generan costos. Detén las que no uses.
- **Información sensible**: Las IPs públicas pueden exponer servicios. Revisa security groups.

---

## 🆘 Solución de problemas

### Error: "Unauthorized operation"
Las credenciales no tienen permisos suficientes.
- Solución: Agregar permisos ec2:Describe* a la política IAM

### Error: "Instance ID not found"
El ID de la instancia no existe.
- Solución: Verificar con `python ec2_monitor.py`

### No aparecen instancias
Pueden estar en otra región.
- Solución: Especificar `--region` o cambiar en `aws configure`

### Monitoreo lento
Demasiadas instancias o conexión lenta.
- Solución: Aumentar `--interval` o usar filtros (`--running-only`)

---

## 📚 Recursos

- [AWS EC2 API Reference](https://docs.aws.amazon.com/ec2/index.html)
- [Boto3 EC2 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)

---

**Última actualización**: 18 de Marzo de 2026
