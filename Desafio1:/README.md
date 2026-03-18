# S3 Backup Automático

Script Python para hacer backup automático de carpetas locales a Amazon S3. Scanea carpetas, sube archivos y crea carpetas con fecha/timestamp.

## 📋 Características

- ✅ Escanea carpetas recursivamente
- ✅ Sube todos los archivos a S3
- ✅ Crea carpetas con timestamp automático
- ✅ Mantiene estructura de directorios
- ✅ Excluye patrones de archivos
- ✅ Logging detallado
- ✅ Soporte para múltiples perfiles de AWS
- ✅ Programación de backups automáticos
- ✅ API Python para integración

## 🚀 Instalación rápida

```bash
# Instalar dependencias
pip install -r requirements.txt

# O instalar manualmente
pip install boto3 schedule
```

## 📦 Crear bucket de S3

### Opción 1: Automática (recomendada)
```bash
# Verificar configuración y crear bucket si no existe
python verify_config.py
```

### Opción 2: Manual
```bash
# Crear bucket con configuración completa
python create_s3_bucket.py mi-bucket-backup
```

Para más detalles, ver [CREAR_BUCKET.md](CREAR_BUCKET.md)

## ⚙️ Configuración de AWS

### Opción 1: AWS CLI (Recomendado)
```bash
aws configure
# Ingresa tu Access Key ID, Secret Access Key, región, etc.
```

### Opción 2: Variables de entorno
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Opción 3: Archivo de credenciales (~/.aws/credentials)
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[produccion]
aws_access_key_id = PROD_ACCESS_KEY
aws_secret_access_key = PROD_SECRET_KEY
```

## 📁 Archivos incluidos

| Archivo | Descripción |
|---------|-------------|
| `s3_backup.py` | Script principal de backup a S3 |
| `create_s3_bucket.py` | **Crear y configurar buckets S3** con políticas automáticas |
| `verify_config.py` | Verificar configuración y **crear bucket automáticamente si falta** |
| `backup_scheduler.py` | Programación automática de backups |
| `test_backup.py` | Script de prueba (sin AWS real) |
| `CREAR_BUCKET.md` | Guía completa de creación de buckets |
| `EJEMPLOS_USO.md` | Ejemplos de uso detallados |
| `requirements.txt` | Dependencias Python |

## 🎯 Uso

### Flujo rápido (primero el bucket, luego el backup)
```bash
# Paso 1: Instalar
pip install -r requirements.txt

# Paso 2: Crear bucket (si no existe)
python verify_config.py

# Paso 3: Hacer backup
python s3_backup.py /ruta/carpeta --bucket mi-bucket-backup
```

### Backup simple
```bash
python s3_backup.py /ruta/carpeta --bucket mi-bucket-s3
```

### Backup con prefijo personalizado
```bash
python s3_backup.py /ruta/carpeta \
    --bucket mi-bucket-s3 \
    --prefix backups/proyecto1
```

### Backup con exclusiones
```bash
python s3_backup.py /ruta/carpeta \
    --bucket mi-bucket-s3 \
    --exclude .git __pycache__ *.tmp .env
```

### Backup con perfil de AWS
```bash
python s3_backup.py /ruta/carpeta \
    --bucket mi-bucket-s3 \
    --profile produccion
```

### Ver todas las opciones
```bash
python s3_backup.py --help
```

## 📅 Programación automática

### Uso como script programado
```bash
python backup_scheduler.py
```

Editar `backup_scheduler.py` para configurar:
- Qué carpetas hacer backup
- Cuándo ejecutar (hora, frecuencia)
- Patrones a excluir

### Con cron (Linux/Mac)
```bash
crontab -e
# Agregar:
0 2 * * * python /ruta/script/s3_backup.py /datos --bucket bucket >> /var/log/backup.log 2>&1
```

### Con systemd timer (Linux)
Ver detalles en `EJEMPLOS_USO.md`

## 🧪 Pruebas

Pruebar sin necesitar AWS real:
```bash
pip install moto  # Simula S3
python test_backup.py
```

## 📊 Estructura en S3 después del backup

```
mi-bucket-s3/
└── backups/
    └── proyecto1/
        └── 20260317_143025/           ← Timestamp automático
            ├── archivo1.txt
            ├── archivo2.py
            ├── subcarpeta/
            │   └── archivo3.json
            └── ...
```

## 🔐 Permisos necesarios en IAM

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:PutObjectAcl"],
            "Resource": "arn:aws:s3:::mi-bucket-s3/*"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::mi-bucket-s3"
        }
    ]
}
```

## 🐛 Solución de problemas

### Error: "Credenciales de AWS no encontradas"
- Ejecuta `aws configure`
- O establece variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
- O crea `~/.aws/credentials`

### Error: "NoSuchBucket"
- Verifica que el bucket existe en S3
- Verifica que el nombre del bucket es correcto
- Verifica permisos en IAM

### Error: "AccessDenied"
- Verifica permisos en la política IAM
- Asegúrate que el usuario tiene permisos s3:PutObject y s3:ListBucket

### El backup sube lentamente
- Los archivos grandes se suben de uno en uno
- Para archivos muy grandes, considera usar multipart upload
- Verifica tu conexión a internet

## 📚 Uso como biblioteca Python

```python
from s3_backup import S3Backup

# Crear instancia
backup = S3Backup("mi-bucket-s3", aws_profile="default")

# Backup simple
backup.create_backup("/ruta/datos", "backups/misdata")

# Backup con exclusiones
backup.create_backup_with_exclude(
    "/ruta/datos",
    "backups/misdata",
    exclude_patterns=[".git", "__pycache__", ".env"]
)
```

## 📝 Logging

El script genera logs en:
- **Consola**: Información en tiempo real
- **Archivo**: `backup_scheduler.log` (si usas scheduler)

Niveles de log:
- INFO: Operaciones normales
- ERROR: Errores durante backup
- WARNING: Situaciones inusuales

## 🤝 Contribuciones

Para mejorar el script, considera:
- Agregar soporte para transferencias multipart
- Compresión automática de archivos
- Sincronización bidireccional
- Notificaciones por email/Slack

## 📄 Licencia

Libre para usar y modificar.

## 💡 Tips

1. **Prueba primero**: Haz un backup de prueba a un bucket de testing
2. **Excluye lo innecesario**: .git, __pycache__, node_modules, .env hacen backups más rápidos
3. **Monitorea logs**: Configura alertas para errores de backup
4. **Lifecycle policies**: Configura políticas en S3 para archivar/eliminar backups antiguos
5. **Sincronización cruzada de regiones**: S3 puede replicar backups automáticamente

---

**Documento actualizado**: 17 de Marzo de 2026
