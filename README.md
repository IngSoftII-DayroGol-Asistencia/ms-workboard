# 🚀 WorkBoard API - Microservicio Estilo Trello

Microservicio de gestión de tareas tipo Trello desarrollado con FastAPI y SQLAlchemy ORM.

## 📋 Características

- ✅ **Tableros (Boards)**: Organiza proyectos en tableros independientes
- 📝 **Listas (Lists)**: Agrupa tarjetas en columnas personalizables
- 🎯 **Tarjetas (Cards)**: Gestiona tareas con prioridades, fechas y asignaciones
- 💬 **Comentarios**: Colabora en tarjetas con comentarios
- 📊 **Log de Actividades**: Seguimiento completo de cambios
- 🔄 **ORM SQLAlchemy**: Fácil migración de SQLite a PostgreSQL/CloudSQL

## 🛠️ Stack Tecnológico

- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Base de datos**: SQLite (local) → PostgreSQL/CloudSQL (producción)
- **Validación**: Pydantic 2.5.0
- **Servidor**: Uvicorn
- **Contenedorización**: Docker & Docker Compose

## 📦 Estructura del Proyecto

```
ms-workboard/
├── main.py              # API endpoints y configuración FastAPI
├── models.py            # Modelos Pydantic (Request/Response)
├── database.py          # Modelos SQLAlchemy ORM
├── storage.py           # Capa de acceso a datos
├── requirements.txt     # Dependencias Python
├── Dockerfile          # Imagen Docker
├── docker-compose.yml  # Orquestación de contenedores
├── .env.example        # Plantilla de variables de entorno
└── README.md           # Esta documentación
```

## 🚀 Guía de Inicio Rápido

### Opción 1: Con Docker (Recomendado)

1. **Clonar o navegar al directorio**:
```bash
cd ms-workboard
```

2. **Crear archivo de entorno** (opcional):
```bash
copy .env.example .env
```

3. **Iniciar el servicio con Docker Compose**:
```bash
docker-compose up --build
```

4. **Verificar que funciona**:
- API: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- Documentación alternativa: http://localhost:8000/redoc

### Opción 2: Sin Docker (Desarrollo local)

1. **Crear entorno virtual**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar el servidor**:
```bash
python main.py
# O con uvicorn directamente:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Acceder a la API**:
- http://localhost:8000/docs

## 🧪 Pruebas con la API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Respuesta esperada**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Crear un Tablero

```bash
curl -X POST "http://localhost:8000/boards" -H "Content-Type: application/json" -d "{\"name\":\"Mi Proyecto\",\"description\":\"Tablero de prueba\",\"color\":\"#3498db\",\"owner_id\":\"user123\"}"
```

### 3. Crear una Lista en el Tablero

```bash
curl -X POST "http://localhost:8000/lists?user_id=user123" -H "Content-Type: application/json" -d "{\"name\":\"Por Hacer\",\"board_id\":\"BOARD_ID_AQUI\",\"position\":0}"
```

### 4. Crear una Tarjeta en la Lista

```bash
curl -X POST "http://localhost:8000/cards?user_id=user123" -H "Content-Type: application/json" -d "{\"title\":\"Tarea importante\",\"description\":\"Detalles de la tarea\",\"priority\":\"high\",\"status\":\"todo\",\"list_id\":\"LIST_ID_AQUI\"}"
```

### 5. Obtener Tablero Completo con Listas

```bash
curl "http://localhost:8000/boards/BOARD_ID_AQUI/full"
```

Ver documentación completa en el archivo para más endpoints y ejemplos.

## 📊 Modelo de Datos

### Board (Tablero)
- id, name, description, color, owner_id, is_archived
- Relaciones: lists[], activities[]

### List (Lista/Columna)
- id, name, position, board_id, is_archived
- Relaciones: cards[]

### Card (Tarjeta/Tarea)
- id, title, description, priority, status, position, due_date, list_id, assigned_to
- Relaciones: comments[]

### Comment (Comentario)
- id, content, card_id, user_id

### ActivityLog (Registro de Actividad)
- id, board_id, user_id, activity_type, description

## 🐳 Comandos Docker Útiles

```bash
# Construir e iniciar
docker-compose up --build

# Iniciar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f workboard-api

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker-compose down -v
```

## 🔄 Migración a PostgreSQL/Cloud SQL

El código está preparado con SQLAlchemy ORM para migrar sin cambios:

1. Actualizar `DATABASE_URL` en variables de entorno
2. Reiniciar servicios
3. ¡Listo! No se requieren cambios en código

**SQLite local**:
```
DATABASE_URL=sqlite:///./data/workboard.db
```

**PostgreSQL**:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Google Cloud SQL**:
```
DATABASE_URL=postgresql+pg8000://user:pass@/dbname?unix_sock=/cloudsql/PROJECT:REGION:INSTANCE
```

## 📖 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Documentación interactiva |
| POST | `/boards` | Crear tablero |
| GET | `/boards/{id}/full` | Tablero con listas |
| POST | `/lists` | Crear lista |
| GET | `/lists/{id}/full` | Lista con tarjetas |
| POST | `/cards` | Crear tarjeta |
| PUT | `/cards/{id}` | Actualizar/mover tarjeta |
| POST | `/comments` | Agregar comentario |
| GET | `/boards/{id}/activities` | Log de actividades |

## 🐛 Troubleshooting

### El contenedor no inicia
```bash
docker-compose logs -f workboard-api
docker-compose down -v
docker-compose up --build
```

### Puerto 8000 ocupado
Editar `docker-compose.yml` y cambiar el puerto:
```yaml
ports:
  - "8001:8000"
```

## 📝 Licencia

MIT License

## 👥 Equipo

Desarrollado para IngSoftII-DayroGol-Asistencia

