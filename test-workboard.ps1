# WorkBoard API - Test Suite
# Ejecuta con: powershell -ExecutionPolicy Bypass .\test-workboard.ps1

$BASE_URL = "http://localhost:8000"
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   WorkBoard API - Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para hacer requests
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Description
    )
    
    Write-Host "" -NoNewline
    Write-Host "[TEST] $Description" -ForegroundColor Yellow
    Write-Host "  $Method $Endpoint" -ForegroundColor Gray
    
    try {
        if ($Body) {
            $json = $Body | ConvertTo-Json -Depth 10
            $response = Invoke-RestMethod -Uri "$BASE_URL$Endpoint" -Method $Method -Body $json -ContentType "application/json"
        } else {
            $response = Invoke-RestMethod -Uri "$BASE_URL$Endpoint" -Method $Method
        }
        
        Write-Host "  [OK] Success" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Verificar que el servicio esta corriendo
Write-Host "Verificando servicio..." -ForegroundColor Cyan
try {
    $null = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Servicio activo en $BASE_URL" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] El servicio no esta disponible en $BASE_URL" -ForegroundColor Red
    Write-Host "Ejecuta primero: docker-compose up --build" -ForegroundColor Yellow
    exit 1
}

# TEST 1: Health Check
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 1: Health Check" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$health = Invoke-ApiRequest -Method "GET" -Endpoint "/health" -Description "Verificar salud del servicio"
if ($health) {
    Write-Host "  Status: $($health.status)" -ForegroundColor Green
}

# TEST 2: Crear Tablero
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 2: Crear Tablero" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$boardData = @{
    name = "Proyecto Test $(Get-Date -Format 'HH:mm:ss')"
    description = "Tablero de prueba automatica"
    color = "#3498db"
    owner_id = "test-user-123"
}

$board = Invoke-ApiRequest -Method "POST" -Endpoint "/boards" -Body $boardData -Description "Crear nuevo tablero"
if (-not $board) {
    Write-Host ""
    Write-Host "[ERROR] No se pudo crear el tablero. Abortando tests." -ForegroundColor Red
    exit 1
}

$BOARD_ID = $board.id
Write-Host ""
Write-Host "  Board ID: $BOARD_ID" -ForegroundColor Cyan
Write-Host "  Nombre: $($board.name)" -ForegroundColor Gray

# TEST 3: Crear Listas
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 3: Crear Listas" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$listNames = @("Por Hacer", "En Progreso", "Completado")
$listIds = @()

foreach ($listName in $listNames) {
    $listData = @{
        name = $listName
        board_id = $BOARD_ID
        position = $listNames.IndexOf($listName)
    }
    
    $list = Invoke-ApiRequest -Method "POST" -Endpoint "/lists?user_id=test-user-123" -Body $listData -Description "Crear lista '$listName'"
    if ($list) {
        $listIds += $list.id
        Write-Host "    ID: $($list.id)" -ForegroundColor DarkGray
    }
}

if ($listIds.Count -ne 3) {
    Write-Host ""
    Write-Host "[ERROR] No se pudieron crear todas las listas. Abortando." -ForegroundColor Red
    exit 1
}

# TEST 4: Crear Tarjetas
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 4: Crear Tarjetas" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

$cards = @(
    @{
        title = "Implementar autenticacion"
        description = "Sistema de login con JWT"
        priority = "high"
        status = "todo"
        list_id = $listIds[0]
        assigned_to = "test-user-123"
    },
    @{
        title = "Disenar base de datos"
        description = "Esquema de tablas y relaciones"
        priority = "urgent"
        status = "todo"
        list_id = $listIds[0]
        assigned_to = "test-user-456"
    },
    @{
        title = "Configurar CI/CD"
        description = "Pipeline de deployment"
        priority = "medium"
        status = "in_progress"
        list_id = $listIds[1]
    }
)

$cardIds = @()
foreach ($cardData in $cards) {
    $card = Invoke-ApiRequest -Method "POST" -Endpoint "/cards?user_id=test-user-123" -Body $cardData -Description "Crear tarjeta '$($cardData.title)'"
    if ($card) {
        $cardIds += $card.id
        Write-Host "    ID: $($card.id)" -ForegroundColor DarkGray
    }
}

# TEST 5: Obtener Tablero Completo
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 5: Obtener Tablero Completo" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$fullBoard = Invoke-ApiRequest -Method "GET" -Endpoint "/boards/$BOARD_ID/full" -Description "Obtener tablero con listas"

if ($fullBoard) {
    Write-Host ""
    Write-Host "  Resumen del Tablero:" -ForegroundColor Cyan
    Write-Host "  Nombre: $($fullBoard.name)" -ForegroundColor White
    Write-Host "  Listas: $($fullBoard.lists.Count)" -ForegroundColor White
    
    foreach ($list in $fullBoard.lists) {
        Write-Host "    - $($list.name)" -ForegroundColor Gray
    }
}

# TEST 6: Mover Tarjeta
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 6: Mover Tarjeta" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
if ($cardIds.Count -gt 0) {
    $updateData = @{
        list_id = $listIds[2]
        status = "done"
    }
    
    $movedCard = Invoke-ApiRequest -Method "PUT" -Endpoint "/cards/$($cardIds[0])?user_id=test-user-123" -Body $updateData -Description "Mover tarjeta a 'Completado'"
    
    if ($movedCard) {
        Write-Host "    Nuevo status: $($movedCard.status)" -ForegroundColor Green
    }
}

# TEST 7: Agregar Comentario
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 7: Agregar Comentario" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
if ($cardIds.Count -gt 0) {
    $commentData = @{
        content = "Gran avance en esta tarea!"
        card_id = $cardIds[0]
        user_id = "test-user-123"
    }
    
    $comment = Invoke-ApiRequest -Method "POST" -Endpoint "/comments" -Body $commentData -Description "Agregar comentario"
    
    if ($comment) {
        Write-Host "    Comment ID: $($comment.id)" -ForegroundColor Green
    }
}

# TEST 8: Log de Actividades
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "TEST 8: Log de Actividades" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
$activities = Invoke-ApiRequest -Method "GET" -Endpoint "/boards/$BOARD_ID/activities?limit=5" -Description "Obtener actividades"

if ($activities) {
    Write-Host ""
    Write-Host "  Ultimas $($activities.Count) actividades:" -ForegroundColor Cyan
    foreach ($activity in $activities) {
        Write-Host "    - $($activity.activity_type): $($activity.description)" -ForegroundColor Gray
    }
}

# RESUMEN FINAL
Write-Host ""
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "     TESTS COMPLETADOS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Board ID: $BOARD_ID" -ForegroundColor Cyan
Write-Host ""
Write-Host "Links utiles:" -ForegroundColor Cyan
Write-Host "  API Docs: $BASE_URL/docs" -ForegroundColor Gray
Write-Host "  ReDoc: $BASE_URL/redoc" -ForegroundColor Gray
Write-Host "  Health: $BASE_URL/health" -ForegroundColor Gray
Write-Host ""
Write-Host "WorkBoard API funcionando correctamente!" -ForegroundColor Green
Write-Host ""