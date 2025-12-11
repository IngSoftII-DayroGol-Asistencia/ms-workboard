from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


# Enums matching Pydantic models
class CardPriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CardStatusEnum(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class ActivityTypeEnum(str, enum.Enum):
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


# ============================================
# SQLAlchemy ORM Models (Database)
# ============================================

class Board(Base):
    __tablename__ = "boards"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    owner_id = Column(String, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    lists = relationship("List", back_populates="board", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="board", cascade="all, delete-orphan")


class List(Base):
    __tablename__ = "lists"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    board_id = Column(String, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    board = relationship("Board", back_populates="lists")
    cards = relationship("Card", back_populates="list", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(CardPriorityEnum), default=CardPriorityEnum.MEDIUM, nullable=False)
    status = Column(SQLEnum(CardStatusEnum), default=CardStatusEnum.TODO, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    due_date = Column(DateTime, nullable=True)
    list_id = Column(String, ForeignKey("lists.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    list = relationship("List", back_populates="cards")
    comments = relationship("Comment", back_populates="card", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    content = Column(String(1000), nullable=False)
    card_id = Column(String, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    card = relationship("Card", back_populates="comments")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    board_id = Column(String, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    activity_type = Column(SQLEnum(ActivityTypeEnum), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    board = relationship("Board", back_populates="activities")
