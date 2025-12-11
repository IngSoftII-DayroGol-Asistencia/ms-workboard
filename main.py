from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn

from models import (
    BoardCreate, BoardUpdate, BoardResponse, BoardWithLists,
    ListCreate, ListUpdate, ListResponse, ListWithCards,
    CardCreate, CardUpdate, CardResponse,
    CommentCreate, CommentResponse,
    ActivityLogResponse,
    PaginationParams
)
from storage import storage


app = FastAPI(
    title="WorkBoard API",
    description="A Trello-like task management service with boards, lists, and cards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["http://localhost:5173", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Health Check
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "service": "WorkBoard API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected"
    }


# ============================================
# Board Endpoints
# ============================================

@app.post("/boards", response_model=BoardResponse, status_code=201, tags=["Boards"])
async def create_board(board: BoardCreate):
    """Create a new board"""
    try:
        return storage.create_board(board)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/boards/{board_id}", response_model=BoardResponse, tags=["Boards"])
async def get_board(board_id: str = Path(..., description="Board ID")):
    """Get a board by ID"""
    board = storage.get_board(board_id)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
    return board


@app.get("/boards/{board_id}/full", response_model=BoardWithLists, tags=["Boards"])
async def get_board_with_lists(board_id: str = Path(..., description="Board ID")):
    """Get a board with all its lists"""
    board = storage.get_board_with_lists(board_id)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
    return board


@app.get("/boards", response_model=List[BoardResponse], tags=["Boards"])
async def get_boards_by_owner(
    owner_id: str = Query(..., description="Owner user ID"),
    include_archived: bool = Query(False, description="Include archived boards")
):
    """Get all boards owned by a user"""
    return storage.get_boards_by_owner(owner_id, include_archived)


@app.patch("/boards/{board_id}", response_model=BoardResponse, tags=["Boards"])
async def update_board(
    board_id: str = Path(..., description="Board ID"),
    board_update: BoardUpdate = Body(...),
    user_id: str = Query(..., description="User ID making the update")
):
    """Update a board"""
    board = storage.update_board(board_id, board_update, user_id)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
    return board


@app.delete("/boards/{board_id}", status_code=204, tags=["Boards"])
async def delete_board(board_id: str = Path(..., description="Board ID")):
    """Delete a board"""
    if not storage.delete_board(board_id):
        raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
    return None


# ============================================
# List Endpoints
# ============================================

@app.post("/lists", response_model=ListResponse, status_code=201, tags=["Lists"])
async def create_list(
    list_data: ListCreate,
    user_id: str = Query(..., description="User ID creating the list")
):
    """Create a new list in a board"""
    try:
        return storage.create_list(list_data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lists/{list_id}", response_model=ListResponse, tags=["Lists"])
async def get_list(list_id: str = Path(..., description="List ID")):
    """Get a list by ID"""
    lst = storage.get_list(list_id)
    if not lst:
        raise HTTPException(status_code=404, detail=f"List {list_id} not found")
    return lst


@app.get("/lists/{list_id}/full", response_model=ListWithCards, tags=["Lists"])
async def get_list_with_cards(list_id: str = Path(..., description="List ID")):
    """Get a list with all its cards"""
    lst = storage.get_list_with_cards(list_id)
    if not lst:
        raise HTTPException(status_code=404, detail=f"List {list_id} not found")
    return lst


@app.get("/boards/{board_id}/lists", response_model=List[ListResponse], tags=["Lists"])
async def get_lists_by_board(
    board_id: str = Path(..., description="Board ID"),
    include_archived: bool = Query(False, description="Include archived lists")
):
    """Get all lists in a board"""
    return storage.get_lists_by_board(board_id, include_archived)


@app.patch("/lists/{list_id}", response_model=ListResponse, tags=["Lists"])
async def update_list(
    list_id: str = Path(..., description="List ID"),
    list_update: ListUpdate = Body(...),
    user_id: str = Query(..., description="User ID making the update")
):
    """Update a list"""
    lst = storage.update_list(list_id, list_update, user_id)
    if not lst:
        raise HTTPException(status_code=404, detail=f"List {list_id} not found")
    return lst


@app.delete("/lists/{list_id}", status_code=204, tags=["Lists"])
async def delete_list(list_id: str = Path(..., description="List ID")):
    """Delete a list"""
    if not storage.delete_list(list_id):
        raise HTTPException(status_code=404, detail=f"List {list_id} not found")
    return None


# ============================================
# Card Endpoints
# ============================================

@app.post("/cards", response_model=CardResponse, status_code=201, tags=["Cards"])
async def create_card(
    card_data: CardCreate,
    user_id: str = Query(..., description="User ID creating the card")
):
    """Create a new card in a list"""
    try:
        return storage.create_card(card_data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{card_id}", response_model=CardResponse, tags=["Cards"])
async def get_card(card_id: str = Path(..., description="Card ID")):
    """Get a card by ID"""
    card = storage.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
    return card


@app.get("/lists/{list_id}/cards", response_model=List[CardResponse], tags=["Cards"])
async def get_cards_by_list(list_id: str = Path(..., description="List ID")):
    """Get all cards in a list"""
    return storage.get_cards_by_list(list_id)


@app.get("/cards", response_model=List[CardResponse], tags=["Cards"])
async def get_cards_by_user(
    user_id: str = Query(..., description="User ID assigned to cards")
):
    """Get all cards assigned to a user"""
    return storage.get_cards_by_user(user_id)


@app.patch("/cards/{card_id}", response_model=CardResponse, tags=["Cards"])
async def update_card(
    card_id: str = Path(..., description="Card ID"),
    card_update: CardUpdate = Body(...),
    user_id: str = Query(..., description="User ID making the update")
):
    """Update a card (including moving between lists)"""
    card = storage.update_card(card_id, card_update, user_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
    return card


@app.delete("/cards/{card_id}", status_code=204, tags=["Cards"])
async def delete_card(card_id: str = Path(..., description="Card ID")):
    """Delete a card"""
    if not storage.delete_card(card_id):
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found")
    return None


# ============================================
# Comment Endpoints
# ============================================

@app.post("/comments", response_model=CommentResponse, status_code=201, tags=["Comments"])
async def create_comment(comment_data: CommentCreate):
    """Add a comment to a card"""
    try:
        return storage.create_comment(comment_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{card_id}/comments", response_model=List[CommentResponse], tags=["Comments"])
async def get_comments_by_card(card_id: str = Path(..., description="Card ID")):
    """Get all comments for a card"""
    return storage.get_comments_by_card(card_id)


@app.delete("/comments/{comment_id}", status_code=204, tags=["Comments"])
async def delete_comment(comment_id: str = Path(..., description="Comment ID")):
    """Delete a comment"""
    if not storage.delete_comment(comment_id):
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
    return None


# ============================================
# Activity Log Endpoints
# ============================================

@app.get("/boards/{board_id}/activities", response_model=List[ActivityLogResponse], tags=["Activities"])
async def get_board_activities(
    board_id: str = Path(..., description="Board ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Number of activities to skip")
):
    """Get activity log for a board"""
    return storage.get_board_activities(board_id, limit, offset)


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )
