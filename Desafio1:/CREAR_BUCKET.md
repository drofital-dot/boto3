# Crear y Configurar Buckets S3

## Scripts disponibles

### 1. `create_s3_bucket.py` - Crear bucket con configuración
Script completo para crear un bucket de S3 con políticas automáticas.

### 2. `verify_config.py` - Verificar y crear si es necesario
Script de verificación que crea el bucket automáticamente si no existe.

---

## Opción 1: Crear manualmente con `create_s3_bucket.py`

### Uso básico
```bash
python create_s3_bucket.py mi-bucket-backup
```

Esto:
✓ Crea el bucket
✓ Asigna política para backup
✓ Habilita versionado
✓ Configura ciclo de vida (archiva después de 90 días a Glacier)
✓ Bloquea acceso público

### Opciones adicionales

```bash
# Especificar región
python create_s3_bucket.py mi-bucket --region eu-west-1

# Usar perfil de AWS
python create_s3_bucket.py mi-bucket --profile produccion

# Cambiar tipo de política
python create_s3_bucket.py mi-bucket --policy full

# Ver todas las opciones
python create_s3_bucket.py --help
```

### Tipos de política

- **`backup`** (default) - Permite: PutObject, GetObject, ListBucket ✓
- **`public`** - Permite lectura pública (no recomendado)
- **`full`** - Acceso completo (no recomendado en producción)

### Desactivar características

```bash
# Sin versionado
python create_s3_bucket.py mi-bucket --no-versioning

# Sin ciclo de vida
python create_s3_bucket.py mi-bucket --no-lifecycle

# Permitir acceso público
python create_s3_bucket.py mi-bucket --allow-public
```

### Ejemplo completo
```bash
python create_s3_bucket.py mi-bucket-produccion \
    --region us-east-1 \
    --profile produccion \
    --policy backup
```

---

## Opción 2: Crear automáticamente con `verify_config.py`

### Primero ejecuta verificación
```bash
python verify_config.py
```

### Proceso
1. Verifica credenciales de AWS
2. Pregunta por el bucket
3. **Si el bucket no existe**, te pregunta si quieres crearlo
4. Si respondes "s" o "si", lo crea e configura automáticamente

### Ejemplo
```
$ python verify_config.py

✓ Credenciales de AWS encontradas
  Región: us-east-1

¿Nombre del bucket S3 a verificar? (o Enter para saltar): mi-bucket-backup

⚠ El bucket no existe: mi-bucket-backup

¿Deseas crear el bucket 'mi-bucket-backup'? (s/n): s

Configuración del bucket:
Región AWS (default: us-east-1): us-east-1
Creando bucket: mi-bucket-backup en región us-east-1...
✓ Bucket creado: mi-bucket-backup
✓ Política de acceso configurada
✓ Acceso público bloqueado

✓ Acceso exitoso a bucket: mi-bucket-backup

¿Carpeta local a verificar? (o Enter para saltar): /datos
✓ Carpeta accesible: /datos
  Archivos: 150
  Subcarpetas: 25

============================================================
RESUMEN DE VERIFICACIÓN
============================================================
✓ Credenciales AWS
✓ Acceso a S3
✓ Carpeta local

============================================================

✓ ¡Todo está configurado correctamente!
```

---

## Lo que se configura automáticamente

### 1. Política de Acceso (IAM)
Permite:
- `s3:PutObject` - Subir archivos (backup)
- `s3:GetObject` - Descargar archivos
- `s3:ListBucket` - Listar contenido

Deniega:
- Acceso público

### 2. Versionado
- Guarda versiones anteriores de archivos
- Permite recuperar archivos eliminados accidentalmente
- Utiliza almacenamiento adicional

### 3. Ciclo de Vida
- Archiva objetos a Glacier después de 90 días
- Reduce costos de almacenamiento
- Los archivos siguen siendo accesibles

### 4. Bloqueo de Acceso Público
- Impide acceso anónimo
- Protege datos sensibles

---

## Verificar configuración del bucket

Después de crear el bucket, verifica que todo está correcto:

```bash
# Ver política del bucket
aws s3api get-bucket-policy --bucket mi-bucket-backup --output text | python -m json.tool

# Ver versionado
aws s3api get-bucket-versioning --bucket mi-bucket-backup

# Ver ciclo de vida
aws s3api get-bucket-lifecycle-configuration --bucket mi-bucket-backup

# Ver bloqueo de acceso público
aws s3api get-public-access-block --bucket mi-bucket-backup
```

---

## Uso con scripts de backup

Una vez creado el bucket:

```bash
# Requiere que el bucket exista (normalmente falla si no existe)
python s3_backup.py /datos --bucket mi-bucket-backup

# Requiere que el bucket exista o lo crea
python verify_config.py  # Crea el bucket si es necesario
python s3_backup.py /datos --bucket mi-bucket-backup
```

---

## Ejemplos de flujo completo

### Flujo 1: Rápido (recomendado)
```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Verificar y crear (interactivo)
python verify_config.py

# 3. Hacer backup
python s3_backup.py /datos --bucket mi-bucket-backup
```

### Flujo 2: Automático (sin preguntas)
```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Crear bucket
python create_s3_bucket.py mi-bucket-backup

# 3. Hacer backup
python s3_backup.py /datos --bucket mi-bucket-backup
```

### Flujo 3: Scripts programados
```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Crear bucket con políticas aseguradas
python create_s3_bucket.py mi-bucket-backup \
    --policy backup \
    --no-public-access

# 3. Configurar backup automático
python backup_scheduler.py
```

---

## Costología

### Estimación de costos (S3 Standard)
- **Almacenamiento**: $0.023 / GB/mes
- **Ciclo de vida (Glacier)**: $0.004 / GB/mes (después de 90 días)

**Ejemplo**: 100GB de datos
- Primeros 90 días: $2.30
- Después de 90 días: $0.40/mes (en Glacier)

### Recomendaciones para ahorrar
1. Habilitar ciclo de vida (ya lo hace el script) ✓
2. Usar patrones de exclusión en backup
3. Revisar objetos obsoletos regularmente

---

## Solución de problemas

### Error: "BucketAlreadyExists"
Alguien más ya usa ese nombre. Los nombres de buckets son únicos globalmente.

**Solución**: Elige otro nombre con sufijo único
```bash
python create_s3_bucket.py mi-bucket-backup-$(date +%s)
```

### Error: "AccessDenied al crear bucket"
Tu usuario no tiene permiso s3:CreateBucket

**Solución**: Verifica tu política IAM
```json
{
    "Effect": "Allow",
    "Action": "s3:CreateBucket",
    "Resource": "*"
}
```

### Error: "Credenciales no encontradas"
AWS no puede encontrar tus credenciales

**Solución**:
```bash
aws configure  # O establece variables de entorno
```

---

## Seguridad - Recomendaciones

✓ **Usar política "backup"** (en lugar de "full")
✓ **Bloquear acceso público** (habilitado por defecto)
✓ **Habilitar versionado** (habilitado por defecto)
✓ **Usar perfiles de AWS** específicos por proyecto
✓ **Auditar acceso** regularmente

```bash
# Ver logs de acceso
aws s3api get-bucket-logging --bucket mi-bucket-backup
```

---

## Próximos pasos

Una vez que el bucket está creado y configurado:

1. ✓ Hacer backup manual: `python s3_backup.py ...`
2. ✓ Programar backups: `python backup_scheduler.py`
3. ✓ Verificar contenido: `aws s3 ls s3://mi-bucket-backup/`
4. ✓ Configurar alertas de monitoreo
5. ✓ Pruebas de restauración

---

**Última actualización**: 18 de Marzo de 2026
