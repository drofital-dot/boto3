# Desafío 2 - EC2 Monitor y Control

## 🎯 Objetivo completado

Crear un script que liste y monitoree instancias EC2 mostrando:
- ✅ Instance ID
- ✅ Estado
- ✅ Tipo de instancia
- ✅ IP pública

## 📁 Archivos creados

| Archivo | Descripción |
|---------|------------|
| `ec2_monitor.py` | **Script principal** - Lista y monitorea EC2 |
| `ec2_controller.py` | **Control** - Inicia, detiene, reinicia instancias |
| `ec2_examples.py` | **Ejemplos interactivos** - 10 ejemplos de uso |
| `test_ec2.py` | **Pruebas** - Sin necesidad de AWS real |
| `EC2_MONITOR.md` | **Documentación completa** - Guía de uso |

## 🚀 Uso rápido

### Ver todas las instancias
```bash
python ec2_monitor.py
```

Salida:
```
============================================================
INSTANCIAS EC2
============================================================
ID               | Estado     | Tipo         | IP Pública      | IP Privada      | Nombre
i-0abc123def456  | running    | t2.micro     | 52.10.20.30     | 10.0.1.100      | webserver
i-1def234abc567  | stopped    | t2.small     | N/A             | 10.0.2.50       | database
============================================================

==================================================
ESTADÍSTICAS
==================================================
Total de instancias: 2
  En ejecución: 1
  Detenidas: 1
  Con IP pública: 1
```

### Ver solo instancias en ejecución
```bash
python ec2_monitor.py --running-only
```

### Monitoreo en tiempo real
```bash
python ec2_monitor.py --monitor
```

### Exportar a CSV
```bash
python ec2_monitor.py --format csv > instancias.csv
```

### Exportar a JSON
```bash
python ec2_monitor.py --format json
```

## 🎮 Control de instancias

### Iniciar instancia
```bash
python ec2_controller.py start i-1234567890abcdef0
```

### Detener instancia
```bash
python ec2_controller.py stop i-1234567890abcdef0
```

### Reiniciar instancia
```bash
python ec2_controller.py reboot i-1234567890abcdef0
```

### Ver estado
```bash
python ec2_controller.py status i-1234567890abcdef0
```

## 📚 Ejemplos interactivos
```bash
python ec2_examples.py
```

Menú con 10 ejemplos:
1. Listar todas las instancias
2. Filtrar por estado
3. Exportar a JSON
4. Exportar a CSV
5. Estadísticas
6. Iniciar instancia
7. Detener instancia
8. Ver estado
9. Monitoreo en tiempo real
10. Script personalizado

## 🧪 Pruebas (sin AWS real)
```bash
python test_ec2.py
```

## ✨ Características

### Monitor
- ✅ Listar instancias con toda la información
- ✅ Mostrar: ID, Estado, Tipo, IPs (pública/privada), Nombre
- ✅ Filtrar por estado
- ✅ Mostrar en tabla, JSON o CSV
- ✅ Estadísticas (total, por estado, por tipo)
- ✅ Monitoreo continuo en tiempo real
- ✅ Colores en terminal

### Controller
- ✅ Iniciar instancias
- ✅ Detener instancias
- ✅ Reiniciar instancias
- ✅ Terminar instancias
- ✅ Ver estado
- ✅ Esperar a que alcance un estado

## 📊 Información mostrada

Para cada instancia:
- **Instance ID**: i-0abc123def456
- **Estado**: running, stopped, terminated, pending...
- **Tipo de instancia**: t2.micro, t2.small, t3.medium, etc.
- **IP Pública**: 52.10.20.30 (para instancias en ejecución)
- **IP Privada**: 10.0.1.100
- **Nombre**: Del tag "Name"
- **Timestamp**: Cuándo se lanzó

## 🔍 Casos de uso

### 1. Monitoreo diario
```bash
# Actualiza cada 15 segundos
python ec2_monitor.py --monitor --interval 15
```

### 2. Inventario automático
```bash
# Exportar a CSV para análisis
python ec2_monitor.py --format csv > inventario_$(date +%Y%m%d).csv
```

### 3. Instancias en ejecución
```bash
# Ver solo las que están corriendo
python ec2_monitor.py --running-only
```

### 4. Reiniciar una instancia
```bash
# Ver estado actual
python ec2_controller.py status i-xxxxxx

# Reiniciar
python ec2_controller.py reboot i-xxxxxx

# Esperar a que esté running
python ec2_controller.py status i-xxxxxx --wait running
```

### 5. Ahorrar costos
```bash
# Ver detallas
python ec2_monitor.py --state running

# Detener todos los que no se usen
python ec2_controller.py stop i-1111111 i-2222222 i-3333333
```

## 🔐 Permisos necesarios

```json
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
```

## 📝 Opciones de línea de comandos

### Monitor
```
--profile PROFILE              Perfil de AWS
--region REGION                Región AWS
--state {running,stopped}      Filtrar por estado
--format {table,json,csv}      Formato de salida
--monitor                      Monitoreo continuo
--interval SECONDS             Actualización (default: 30)
--stats                        Solo estadísticas
--running-only                 Solo en ejecución
```

### Controller
```
start <IDs>                    Iniciar
stop <IDs> [--force]           Detener
reboot <IDs>                   Reiniciar
terminate <IDs>                Terminar
status <ID> [--wait STATE]     Estado
```

## 💡 Tips

1. **Guardar inventario**: `python ec2_monitor.py --format csv > backup.csv`
2. **Monitorear 24/7**: `nohup python ec2_monitor.py --monitor > monitor.log &`
3. **Alertas**: Combinar con scripts shell para enviar emails
4. **Dashboard web**: Exportar JSON e integrar con herramientas de visualización
5. **Automatización**: Ejecutar con cron o systemd timers

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| No aparecen instancias | Verificar región con `--region` o `aws configure` |
| "Unauthorized operation" | Falta permisos IAM ec2:* |
| Instancia ID no existe | Verificar con `python ec2_monitor.py` primero |
| Monitoreo lento | Aumentar `--interval` o usar filtros |

## 📚 Próximas características (opcionales)

- [ ] Alertas por email cuando cambia estado
- [ ] Gráficos de histórico de estados
- [ ] Integración con CloudWatch
- [ ] Tagging automático
- [ ] Reserva de instancias
- [ ] Dashboards web

---

**Estado**: ✅ Desafío 2 completado
**Última actualización**: 18 de Marzo de 2026
