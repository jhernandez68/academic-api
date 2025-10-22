#!/bin/bash

# Script de utilidades para Docker Compose
# Uso: ./docker-utils.sh [comando]

set -e

COMPOSE="docker-compose"

case "$1" in
  start)
    echo "🚀 Iniciando servicios..."
    $COMPOSE up -d
    echo "✅ Servicios iniciados"
    ;;

  stop)
    echo "🛑 Deteniendo servicios..."
    $COMPOSE down
    echo "✅ Servicios detenidos"
    ;;

  restart)
    echo "🔄 Reiniciando servicios..."
    $COMPOSE restart
    echo "✅ Servicios reiniciados"
    ;;

  logs)
    echo "📋 Mostrando logs..."
    $COMPOSE logs -f ${2:-web}
    ;;

  migrate)
    echo "🔄 Ejecutando migraciones..."
    $COMPOSE exec web python manage.py migrate
    echo "✅ Migraciones completadas"
    ;;

  test)
    echo "🧪 Ejecutando tests..."
    $COMPOSE exec web pytest ${2:-tests_flujos.py} -v
    ;;

  shell)
    echo "🐍 Entrando a Django shell..."
    $COMPOSE exec web python manage.py shell
    ;;

  clean)
    echo "🗑️  Limpiando todo (incluyendo datos)..."
    read -p "¿Estás seguro? Esto eliminará todos los datos. (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
      $COMPOSE down -v
      echo "✅ Limpieza completada"
    else
      echo "❌ Operación cancelada"
    fi
    ;;

  status)
    echo "📊 Estado de servicios:"
    $COMPOSE ps
    ;;

  build)
    echo "🏗️  Construyendo imagen..."
    $COMPOSE build
    echo "✅ Imagen construida"
    ;;

  *)
    echo "Academic API - Docker Utilities"
    echo ""
    echo "Uso: ./docker-utils.sh [comando] [opciones]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start       - Inicia todos los servicios"
    echo "  stop        - Detiene todos los servicios"
    echo "  restart     - Reinicia todos los servicios"
    echo "  logs [srv]  - Muestra logs (web, postgres, redis, celery_worker, celery_beat)"
    echo "  migrate     - Ejecuta migraciones de base de datos"
    echo "  test [path] - Ejecuta tests (por defecto tests_flujos.py)"
    echo "  shell       - Abre Django shell"
    echo "  status      - Muestra estado de servicios"
    echo "  build       - Construye la imagen Docker"
    echo "  clean       - Elimina todo (incluyendo datos)"
    echo ""
    echo "Ejemplos:"
    echo "  ./docker-utils.sh start"
    echo "  ./docker-utils.sh logs web"
    echo "  ./docker-utils.sh test tests_critical_endpoints.py"
    echo "  ./docker-utils.sh migrate"
    ;;
esac
