# WorkBoard - Comandos Rápidos
# Uso: make <comando>
# Para Windows PowerShell, ejecuta los comandos directamente

.PHONY: help build up down logs test clean restart shell db-shell

help: ## Muestra esta ayuda
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║      WorkBoard - Comandos Disponibles         ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make build      - Construir imagen Docker"
	@echo "  make up         - Iniciar servicios"
	@echo "  make down       - Detener servicios"
	@echo "  make logs       - Ver logs en tiempo real"
	@echo "  make test       - Ejecutar tests automáticos"
	@echo "  make restart    - Reiniciar servicios"
	@echo "  make clean      - Limpiar todo (⚠️ borra datos)"
	@echo "  make shell      - Abrir shell en contenedor"
	@echo "  make db-shell   - Abrir SQLite shell"
	@echo ""
	@echo "PowerShell equivalents:"
	@echo "  docker-compose build"
	@echo "  docker-compose up -d"
	@echo "  docker-compose down"
	@echo "  docker-compose logs -f"
	@echo "  powershell -ExecutionPolicy Bypass .\\test-workboard.ps1"

build: ## Construir imagen Docker
	docker-compose build

up: ## Iniciar servicios en segundo plano
	docker-compose up -d
	@echo "✓ Servicio iniciado en http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"

down: ## Detener servicios
	docker-compose down

logs: ## Ver logs en tiempo real
	docker-compose logs -f workboard-api

test: ## Ejecutar tests automáticos
	@echo "Ejecutando tests..."
	@powershell -ExecutionPolicy Bypass -File test-workboard.ps1

restart: down up ## Reiniciar servicios

clean: ## Limpiar todo (contenedores, volúmenes, imágenes)
	docker-compose down -v
	@echo "⚠️ Datos eliminados. Próximo 'make up' creará DB nueva."

shell: ## Abrir shell en el contenedor
	docker-compose exec workboard-api bash

db-shell: ## Abrir SQLite shell
	docker-compose exec workboard-api sqlite3 /app/data/workboard.db

dev: ## Modo desarrollo (con logs)
	docker-compose up

ps: ## Ver estado de contenedores
	docker-compose ps

health: ## Verificar salud del servicio
	@curl -s http://localhost:8000/health | python -m json.tool

docs: ## Abrir documentación en navegador
	@echo "Abriendo documentación..."
	@start http://localhost:8000/docs
