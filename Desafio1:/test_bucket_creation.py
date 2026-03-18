#!/usr/bin/env python3
"""
Script para probar la creación de buckets S3 con moto (simulador).
Prueba los scripts sin necesitar AWS real.
"""

import sys
import json
from pathlib import Path

# Instalar moto si es necesario
try:
    from moto import mock_aws  # Nueva versión de moto usa mock_aws
    import boto3
except ImportError:
    try:
        from moto import mock_s3  # Versión antigua
        mock_aws = mock_s3
        import boto3
    except ImportError:
        print("Instalando moto para pruebas...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "moto"], check=True)
        try:
            from moto import mock_aws
        except ImportError:
            from moto import mock_s3
            mock_aws = mock_s3
        import boto3


def test_create_bucket():
    """Prueba de creación de bucket."""
    print("\n" + "="*60)
    print("PRUEBA: Crear bucket con moto")
    print("="*60)
    
    with mock_aws():
        from create_s3_bucket import S3BucketSetup
        
        setup = S3BucketSetup(region="us-east-1")
        
        # Prueba 1: Crear bucket
        print("\n[Prueba 1] Crear bucket...")
        assert setup.create_bucket("test-bucket-1"), "Falló crear bucket"
        print("✓ Bucket creado")
        
        # Prueba 2: Verificar que existe
        print("\n[Prueba 2] Verificar que existe...")
        assert setup.bucket_exists("test-bucket-1"), "Bucket no existe"
        print("✓ Bucket verificado")
        
        # Prueba 3: Agregar política
        print("\n[Prueba 3] Agregar política de backup...")
        assert setup.add_bucket_policy("test-bucket-1", "backup"), "Falló agregar política"
        print("✓ Política asignada")
        
        # Prueba 4: Bloquear acceso público
        print("\n[Prueba 4] Bloquear acceso público...")
        assert setup.block_public_access("test-bucket-1"), "Falló bloquear acceso público"
        print("✓ Acceso público bloqueado")
        
        # Prueba 5: Configuración completa
        print("\n[Prueba 5] Configuración completa...")
        assert setup.setup_complete(
            "test-bucket-2",
            enable_versioning=True,
            enable_lifecycle=False,  # No probar lifecycle en moto
            block_public=True,
            policy_type="backup"
        ), "Falló configuración completa"
        print("✓ Configuración completa exitosa")
        
        # Verificar contenido
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        
        print(f"\n✓ Buckets creados: {bucket_names}")
        
        return True


def test_verify_and_create():
    """Prueba de verificar y crear bucket."""
    print("\n" + "="*60)
    print("PRUEBA: Verify config (crear bucket automáticamente)")
    print("="*60)
    
    with mock_aws():
        from unittest.mock import patch
        import verify_config
        
        # Crear cliente S3 en el contexto mock
        boto3.client('s3')
        
        # Prueba: bucket_exists
        print("\n[Prueba 1] Verificar si bucket existe (no existe)...")
        exists = verify_config.bucket_exists("no-existe")
        assert not exists, "Debería retornar False"
        print("✓ Retorna False correctamente")
        
        # Prueba: crear bucket interactivo
        print("\n[Prueba 2] Crear bucket interactivamente...")
        s3_client = boto3.client('s3')
        
        # Simular create_bucket_interactive
        success = verify_config.create_bucket_interactive(s3_client, "test-bucket-nuevo")
        assert success, "Falló crear bucket"
        print("✓ Bucket creado")
        
        # Verificar que existe
        exists = verify_config.bucket_exists("test-bucket-nuevo")
        assert exists, "Bucket debería existir"
        print("✓ Bucket verificado")
        
        return True


def test_integration():
    """Prueba de integración completa."""
    print("\n" + "="*60)
    print("PRUEBA: Integración completa")
    print("="*60)
    
    with mock_aws():
        from create_s3_bucket import S3BucketSetup
        import boto3
        
        print("\n[Prueba] Crear bucket con setup_complete...")
        
        setup = S3BucketSetup(region="us-east-1")
        success = setup.setup_complete(
            "backup-final",
            enable_versioning=True,
            enable_lifecycle=False,
            block_public=True,
            policy_type="backup"
        )
        
        assert success, "Falló setup_complete"
        print("✓ Setup completo exitoso")
        
        # Verificar política
        print("\n[Verificación] Verificar política asignada...")
        s3 = boto3.client('s3')
        try:
            policy = s3.get_bucket_policy(Bucket="backup-final")
            policy_dict = json.loads(policy['Policy'])
            print(f"✓ Política: {policy_dict['Statement'][0]['Action']}")
        except Exception as e:
            print(f"⚠ No se pudo verificar política: {e}")
        
        return True


def main():
    """Ejecutar todas las pruebas."""
    print("\n" + "🧪 "*20)
    print("PRUEBAS DE BUCKET S3")
    print("🧪 "*20)
    
    tests = [
        ("Crear bucket", test_create_bucket),
        ("Verificar y crear", test_verify_and_create),
        ("Integración", test_integration),
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


if __name__ == "__main__":
    sys.exit(main())
