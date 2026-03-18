# Desafio 3: Inventario de Recursos AWS y Sistema de Alertas con CloudWatch

Este desafío implementa dos herramientas principales:

1. **Escáner de Inventario de Recursos AWS** (`inventory_scanner.py`)
2. **Sistema de Alertas con CloudWatch** (`cloudwatch_metrics.py`)

## 🚀 Inicio Rápido

### Prerrequisitos

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciales AWS:**
   ```bash
   aws configure
   # O crear un perfil nombrado
   aws configure --profile myprofile
   ```

### Uso Básico

#### 1. Escanear Recursos AWS
```bash
# Escaneo completo con salida en tabla
python inventory_scanner.py

# Usar un perfil específico y región
python inventory_scanner.py --profile myprofile --region us-east-1

# Salida en JSON
python inventory_scanner.py --format json --output inventory.json

# Salida en CSV
python inventory_scanner.py --format csv --output inventory.csv
```

#### 2. Publicar Métricas en CloudWatch
```bash
# Publicar métricas desde un inventario existente
python cloudwatch_metrics.py --inventory-file inventory.json --send-metrics

# Crear alarmas basadas en métricas
python cloudwatch_metrics.py --create-alarms

# Listar métricas personalizadas
python cloudwatch_metrics.py --list-metrics
```

## 📋 Servicios Soportados

El escáner de inventario cubre los siguientes servicios AWS:

- **EC2**: Instancias, tipos, estados, IPs, VPCs
- **S3**: Buckets, regiones, conteo de objetos
- **RDS**: Instancias de base de datos, motores, estados
- **Lambda**: Funciones, runtimes, memoria, timeouts
- **VPC**: VPCs, subnets, security groups
- **EBS**: Volúmenes, tamaños, estados, attachments

## 📊 Métricas de CloudWatch

El sistema crea métricas personalizadas en el namespace `AWS/Resources`:

### Métricas Generales
- `TotalResources`: Conteo total de recursos
- `{Service}Count`: Conteo por servicio (EC2Count, S3Count, etc.)

### Métricas Específicas por Servicio
- **EC2**: `EC2RunningInstances`, `EC2StoppedInstances`
- **RDS**: `RDSAvailableInstances`, `RDSStoppedInstances`
- **Lambda**: `LambdaActiveFunctions`, `LambdaTotalMemoryMB`
- **EBS**: `EBSVolumesInUse`, `EBSVolumesAvailable`, `EBSTotalSizeGB`

### Alarmas Automáticas
Se crean alarmas predefinidas para:
- Alto conteo de instancias EC2 (>10)
- Alto conteo de instancias RDS (>5)
- Alto uso de memoria Lambda (>1024MB)

## 🛠️ Opciones de Línea de Comandos

### inventory_scanner.py

```
--profile PROFILE    Perfil de AWS a usar
--region REGION      Región de AWS (por defecto: us-east-1)
--services SERVICES  Servicios específicos a escanear
--format FORMAT      Formato de salida: table, json, csv
--output FILE        Archivo de salida
--all                Escanear todos los servicios
```

### cloudwatch_metrics.py

```
--profile PROFILE       Perfil de AWS a usar
--region REGION         Región de AWS (por defecto: us-east-1)
--namespace NAMESPACE   Namespace para métricas (por defecto: AWS/Resources)
--inventory-file FILE   Archivo JSON del inventario
--send-metrics          Enviar métricas a CloudWatch
--create-alarms         Crear alarmas de CloudWatch
--list-metrics          Listar métricas personalizadas
```

## 📝 Ejemplos de Uso

### 1. Flujo Completo: Escaneo → Métricas → Alarmas

```bash
# 1. Escanear recursos y guardar en JSON
python inventory_scanner.py --format json --output inventory.json

# 2. Publicar métricas en CloudWatch
python cloudwatch_metrics.py --inventory-file inventory.json --send-metrics

# 3. Crear alarmas
python cloudwatch_metrics.py --create-alarms

# 4. Ver métricas publicadas
python cloudwatch_metrics.py --list-metrics
```

### 2. Monitoreo Periódico con Cron

```bash
# Añadir a crontab para escaneo diario
0 2 * * * cd /path/to/desafio3 && python inventory_scanner.py --format json --output inventory_$(date +\%Y\%m\%d).json

# Publicar métricas cada hora
0 * * * * cd /path/to/desafio3 && python cloudwatch_metrics.py --inventory-file inventory_latest.json --send-metrics
```

### 3. Integración con Otros Scripts

```python
from inventory_scanner import AWSResourceScanner
from cloudwatch_metrics import CloudWatchMetricsPublisher

# Escanear recursos
scanner = AWSResourceScanner(profile_name='prod', region='us-east-1')
inventory = scanner.scan_all_resources()

# Publicar métricas
publisher = CloudWatchMetricsPublisher(profile_name='prod', region='us-east-1')
publisher.publish_inventory_metrics(inventory)
```

## 🔧 Configuración y Solución de Problemas

### Credenciales AWS

El script soporta múltiples métodos de autenticación:

1. **Variables de entorno:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

2. **Archivo de credenciales:**
   ```bash
   aws configure --profile myprofile
   ```

3. **Perfiles nombrados:**
   ```bash
   python inventory_scanner.py --profile myprofile
   ```

### Permisos IAM Requeridos

Para el escáner de inventario:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:ListObjectsV2",
                "rds:DescribeDBInstances",
                "lambda:ListFunctions",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

Para métricas de CloudWatch:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

### Manejo de Errores

- **Credenciales inválidas:** Verifica configuración con `aws configure`
- **Permisos insuficientes:** Revisa políticas IAM
- **Región incorrecta:** Algunos servicios son globales (S3), otros regionales
- **Límites de API:** El script incluye manejo de rate limiting básico

## 📊 Formatos de Salida

### Tabla (por defecto)
```
================================================================================
INVENTARIO DE RECURSOS AWS
================================================================================
Cuenta: 123456789012
Región: us-east-1
Fecha: 2024-01-15T10:30:00

📋 EC2
----------------------------------------
  1. i-1234567890abcdef0 - running (t3.micro)
  2. i-0987654321fedcba0 - stopped (t3.small)

📋 S3
----------------------------------------
  1. my-bucket - us-east-1 (15 objetos)
```

### JSON
```json
{
  "metadata": {
    "account_id": "123456789012",
    "region": "us-east-1",
    "scan_timestamp": "2024-01-15T10:30:00",
    "scanner_version": "1.0.0"
  },
  "resources": {
    "ec2": [...],
    "s3": [...],
    "rds": [...],
    "lambda": [...],
    "vpc": {...},
    "ebs": [...]
  },
  "summary": {
    "total_resources": 25,
    "services_scanned": 6,
    "service_counts": {
      "ec2": 5,
      "s3": 3,
      "rds": 2,
      "lambda": 8,
      "vpc": 4,
      "ebs": 3
    }
  }
}
```

## 🔍 Verificación

Para verificar que todo funciona correctamente:

1. **Probar el escáner:**
   ```bash
   python inventory_scanner.py --help
   python inventory_scanner.py --format table
   ```

2. **Verificar métricas en CloudWatch:**
   - Ve a la consola de CloudWatch
   - Navega a "Metrics" → "Custom namespaces" → "AWS/Resources"
   - Deberías ver las métricas publicadas

3. **Verificar alarmas:**
   - Ve a "Alarms" en CloudWatch
   - Busca alarmas con nombres como "HighEC2InstanceCount"

## 🚀 Próximos Pasos

Posibles mejoras:
- Soporte para más servicios AWS (ECS, EKS, API Gateway, etc.)
- Filtros avanzados por tags, estados, etc.
- Dashboard personalizado en CloudWatch
- Notificaciones por email/SNS cuando se activen alarmas
- Historial de cambios en recursos
- Exportación a bases de datos o sistemas de monitoreo externos