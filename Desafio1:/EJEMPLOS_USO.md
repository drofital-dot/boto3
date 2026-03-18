# Ejemplos de Uso - S3 Backup Script

## Instalación de dependencias

```bash
pip install boto3
```

## Configuración de AWS

Antes de usar el script, necesitas configurar tus credenciales de AWS:

### Opción 1: Usar el CLI de AWS
```bash
aws configure
```

### Opción 2: Variables de entorno
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

---

## Ejemplos de uso

### 1. Backup simple de una carpeta

```bash
python s3_backup.py /ruta/a/carpeta --bucket mi-bucket-s3
```

Esto creará una carpeta como `backup/20260317_143025/` en S3 con todos los archivos.

### 2. Backup con prefijo personalizado

```bash
python s3_backup.py /ruta/a/carpeta \
    --bucket mi-bucket-s3 \
    --prefix backups/proyecto1
```

Resultado: `backups/proyecto1/20260317_143025/archivos...`

### 3. Backup excluyendo patrones

```bash
python s3_backup.py /ruta/a/carpeta \
    --bucket mi-bucket-s3 \
    --exclude .git __pycache__ *.tmp node_modules .env
```

Esto excluirá cualquier archivo que contenga estos patrones en su ruta.

### 4. Backup con perfil de AWS específico

```bash
python s3_backup.py /ruta/a/carpeta \
    --bucket mi-bucket-s3 \
    --profile mi-perfil-aws
```

### 5. Backup completo con todas las opciones

```bash
python s3_backup.py /ruta/a/carpeta \
    --bucket mi-bucket-s3 \
    --prefix backups/mi-proyecto \
    --exclude .git __pycache__ *.tmp .env node_modules \
    --profile produccion
```

---

## Uso en Python

También puedes usar el script directamente en tu código Python:

```python
from s3_backup import S3Backup

# Crear instancia
backup = S3Backup("mi-bucket-s3")

# Backup simple
backup.create_backup("/ruta/a/carpeta", "backups/proyecto1")

# Backup con exclusiones
backup.create_backup_with_exclude(
    "/ruta/a/carpeta",
    "backups/proyecto1",
    exclude_patterns=[".git", "__pycache__", "*.tmp"]
)
```

---

## Estructura de carpetas en S3

Después del backup, la estructura en S3 será:

```
mi-bucket-s3/
└── backups/
    └── proyecto1/
        └── 20260317_143025/           ← Carpeta con timestamp
            ├── archivo1.txt
            ├── archivo2.py
            ├── subcarpeta/
            │   └── archivo3.json
            └── ...
```

---

## Automatizar backups con cron (Linux/Mac)

Para hacer backups automáticos cada día a las 2 AM:

```bash
# Editar crontab
crontab -e

# Agregar esta línea:
0 2 * * * python /ruta/del/script/s3_backup.py /datos/importante --bucket mi-bucket-s3 --prefix backups/diarios >> /var/log/backup.log 2>&1
```

---

## Automatizar con systemd timer (Linux)

Crear archivo `/etc/systemd/system/s3-backup.service`:

```ini
[Unit]
Description=S3 Backup Service
After=network-online.target

[Service]
Type=oneshot
User=tu_usuario
WorkingDirectory=/ubicacion/del/script
ExecStart=/usr/bin/python3 /ubicacion/del/script/s3_backup.py /datos/importante --bucket mi-bucket-s3
StandardOutput=journal
StandardError=journal

Environment="AWS_PROFILE=default"
```

Crear archivo `/etc/systemd/system/s3-backup.timer`:

```ini
[Unit]
Description=S3 Backup Timer
Requires=s3-backup.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable s3-backup.timer
sudo systemctl start s3-backup.timer
```

---

## Verificar carpetas en S3

```bash
# Listar carpetas de backup
aws s3 ls s3://mi-bucket-s3/backups/ --recursive

# Ver contenido de un backup específico
aws s3 ls s3://mi-bucket-s3/backups/proyecto1/20260317_143025/ --recursive
```

---

## Permisos necesarios en AWS IAM

El usuario de AWS necesita estos permisos en el bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::mi-bucket-s3/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::mi-bucket-s3"
        }
    ]
}
```
