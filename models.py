from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================
# Pydantic Models (API Request/Response)
# ============================================

class CardPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CardStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


# Board Models
class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Board name")
    description: Optional[str] = Field(None, max_length=500, description="Board description")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Board color in hex format")


class BoardCreate(BoardBase):
    owner_id: str = Field(..., description="ID of the user who owns this board")


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_archived: Optional[bool] = None


class BoardResponse(BoardBase):
    id: str
    owner_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BoardWithLists(BoardResponse):
    lists: List['ListResponse'] = []


# List Models
class ListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="List name")
    position: int = Field(default=0, ge=0, description="Position order in board")


class ListCreate(ListBase):
    board_id: str = Field(..., description="ID of the board this list belongs to")


class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = Field(None, ge=0)
    is_archived: Optional[bool] = None


class ListResponse(ListBase):
    id: str
    board_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ListWithCards(ListResponse):
    cards: List['CardResponse'] = []


# Card Models
class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Card title")
    description: Optional[str] = Field(None, max_length=2000, description="Card description")
    priority: CardPriority = Field(default=CardPriority.MEDIUM)
    status: CardStatus = Field(default=CardStatus.TODO)
    position: int = Field(default=0, ge=0, description="Position order in list")
    due_date: Optional[datetime] = None


class CardCreate(CardBase):
    list_id: str = Field(..., description="ID of the list this card belongs to")
    assigned_to: Optional[str] = Field(None, description="User ID assigned to this card")


class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[CardPriority] = None
    status: Optional[CardStatus] = None
    position: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    list_id: Optional[str] = None  # For moving cards between lists


class CardResponse(CardBase):
    id: str
    list_id: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Comment Models
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Comment text")


class CommentCreate(CommentBase):
    card_id: str = Field(..., description="ID of the card this comment belongs to")
    user_id: str = Field(..., description="ID of the user making the comment")


class CommentResponse(CommentBase):
    id: str
    card_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Activity Log Models
class ActivityType(str, Enum):
    BOARD_CREATED = "board_created"
    BOARD_UPDATED = "board_updated"
    BOARD_ARCHIVED = "board_archived"
    LIST_CREATED = "list_created"
    LIST_UPDATED = "list_updated"
    LIST_MOVED = "list_moved"
    LIST_ARCHIVED = "list_archived"
    CARD_CREATED = "card_created"
    CARD_UPDATED = "card_updated"
    CARD_MOVED = "card_moved"
    CARD_ASSIGNED = "card_assigned"
    COMMENT_ADDED = "comment_added"


class ActivityLogResponse(BaseModel):
    id: str
    board_id: str
    user_id: str
    activity_type: ActivityType
    description: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Pagination
class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Number of items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# Update forward references
BoardWithLists.model_rebuild()
ListWithCards.model_rebuild()
