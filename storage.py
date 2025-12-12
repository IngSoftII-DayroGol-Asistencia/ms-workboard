import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import List, Optional, Generator
from datetime import datetime

from database import Base, Board, List as DBList, Card, Comment, ActivityLog
from models import (
    BoardCreate, BoardUpdate, BoardResponse, BoardWithLists,
    ListCreate, ListUpdate, ListResponse, ListWithCards,
    CardCreate, CardUpdate, CardResponse,
    CommentCreate, CommentResponse,
    ActivityType, ActivityLogResponse
)


class WorkBoardStorage:
    """
    Storage layer using SQLAlchemy ORM.
    Uses SQLite for local development, easily migrates to PostgreSQL/CloudSQL
    """
    
    def __init__(self, database_url: str = "sqlite:///./workboard.db"):
        """
        Initialize storage with database connection
        
        Args:
            database_url: SQLAlchemy database URL
                          Local: sqlite:///./workboard.db
                          PostgreSQL: postgresql://user:pass@host:port/dbname
                          Cloud SQL: postgresql+pg8000://user:pass@/dbname?unix_sock=/cloudsql/project:region:instance
        """
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
            echo=False  # Set to True for SQL query logging
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ============================================
    # Board Operations
    # ============================================
    
    def create_board(self, board_data: BoardCreate) -> BoardResponse:
        """Create a new board"""
        with self.get_session() as session:
            db_board = Board(
                name=board_data.name,
                description=board_data.description,
                color=board_data.color,
                owner_id=board_data.owner_id
            )
            session.add(db_board)
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=db_board.id,
                user_id=board_data.owner_id,
                activity_type=ActivityType.BOARD_CREATED,
                description=f"Created board '{board_data.name}'"
            )
            
            session.refresh(db_board)
            return BoardResponse.model_validate(db_board)
    
    def get_board(self, board_id: str) -> Optional[BoardResponse]:
        """Get a board by ID"""
        with self.get_session() as session:
            board = session.query(Board).filter(Board.id == board_id).first()
            return BoardResponse.model_validate(board) if board else None
    
    def get_board_with_lists(self, board_id: str) -> Optional[BoardWithLists]:
        """Get a board with all its lists"""
        with self.get_session() as session:
            board = session.query(Board).filter(Board.id == board_id).first()
            if not board:
                return None
            
            # Load lists ordered by position
            lists = session.query(DBList).filter(
                DBList.board_id == board_id,
                DBList.is_archived == False
            ).order_by(DBList.position).all()
            
            board_dict = BoardResponse.model_validate(board).model_dump()
            board_dict['lists'] = [ListResponse.model_validate(lst) for lst in lists]
            
            return BoardWithLists(**board_dict)
    
    def get_boards_by_owner(self, owner_id: str, include_archived: bool = False) -> List[BoardResponse]:
        """Get all boards owned by a user"""
        with self.get_session() as session:
            query = session.query(Board).filter(Board.owner_id == owner_id)
            if not include_archived:
                query = query.filter(Board.is_archived == False)
            boards = query.order_by(Board.updated_at.desc()).all()
            return [BoardResponse.model_validate(board) for board in boards]
    
    def update_board(self, board_id: str, board_update: BoardUpdate, user_id: str) -> Optional[BoardResponse]:
        """Update a board"""
        with self.get_session() as session:
            board = session.query(Board).filter(Board.id == board_id).first()
            if not board:
                return None
            
            update_data = board_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(board, key, value)
            
            board.updated_at = datetime.utcnow()
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=board_id,
                user_id=user_id,
                activity_type=ActivityType.BOARD_UPDATED,
                description=f"Updated board '{board.name}'"
            )
            
            session.refresh(board)
            return BoardResponse.model_validate(board)
    
    def delete_board(self, board_id: str) -> bool:
        """Delete a board (cascade deletes lists and cards)"""
        with self.get_session() as session:
            board = session.query(Board).filter(Board.id == board_id).first()
            if not board:
                return False
            session.delete(board)
            return True
    
    # ============================================
    # List Operations
    # ============================================
    
    def create_list(self, list_data: ListCreate, user_id: str) -> ListResponse:
        """Create a new list in a board"""
        with self.get_session() as session:
            # Get max position for this board
            max_pos = session.query(DBList).filter(
                DBList.board_id == list_data.board_id
            ).count()
            
            db_list = DBList(
                name=list_data.name,
                position=list_data.position if list_data.position else max_pos,
                board_id=list_data.board_id
            )
            session.add(db_list)
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=list_data.board_id,
                user_id=user_id,
                activity_type=ActivityType.LIST_CREATED,
                description=f"Created list '{list_data.name}'"
            )
            
            session.refresh(db_list)
            return ListResponse.model_validate(db_list)
    
    def get_list(self, list_id: str) -> Optional[ListResponse]:
        """Get a list by ID"""
        with self.get_session() as session:
            lst = session.query(DBList).filter(DBList.id == list_id).first()
            return ListResponse.model_validate(lst) if lst else None
    
    def get_list_with_cards(self, list_id: str) -> Optional[ListWithCards]:
        """Get a list with all its cards"""
        with self.get_session() as session:
            lst = session.query(DBList).filter(DBList.id == list_id).first()
            if not lst:
                return None
            
            # Load cards ordered by position
            cards = session.query(Card).filter(
                Card.list_id == list_id
            ).order_by(Card.position).all()
            
            list_dict = ListResponse.model_validate(lst).model_dump()
            list_dict['cards'] = [CardResponse.model_validate(card) for card in cards]
            
            return ListWithCards(**list_dict)
    
    def get_lists_by_board(self, board_id: str, include_archived: bool = False) -> List[ListResponse]:
        """Get all lists in a board"""
        with self.get_session() as session:
            query = session.query(DBList).filter(DBList.board_id == board_id)
            if not include_archived:
                query = query.filter(DBList.is_archived == False)
            lists = query.order_by(DBList.position).all()
            return [ListResponse.model_validate(lst) for lst in lists]
    
    def update_list(self, list_id: str, list_update: ListUpdate, user_id: str) -> Optional[ListResponse]:
        """Update a list"""
        with self.get_session() as session:
            lst = session.query(DBList).filter(DBList.id == list_id).first()
            if not lst:
                return None
            
            update_data = list_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(lst, key, value)
            
            lst.updated_at = datetime.utcnow()
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=lst.board_id,
                user_id=user_id,
                activity_type=ActivityType.LIST_UPDATED,
                description=f"Updated list '{lst.name}'"
            )
            
            session.refresh(lst)
            return ListResponse.model_validate(lst)
    
    def delete_list(self, list_id: str) -> bool:
        """Delete a list (cascade deletes cards)"""
        with self.get_session() as session:
            lst = session.query(DBList).filter(DBList.id == list_id).first()
            if not lst:
                return False
            session.delete(lst)
            return True
    
    # ============================================
    # Card Operations
    # ============================================
    
    def create_card(self, card_data: CardCreate, user_id: str) -> CardResponse:
        """Create a new card in a list"""
        with self.get_session() as session:
            # Get the list to find board_id
            lst = session.query(DBList).filter(DBList.id == card_data.list_id).first()
            if not lst:
                raise ValueError(f"List {card_data.list_id} not found")
            
            # Get max position for this list
            max_pos = session.query(Card).filter(
                Card.list_id == card_data.list_id
            ).count()
            
            db_card = Card(
                title=card_data.title,
                description=card_data.description,
                priority=card_data.priority,
                status=card_data.status,
                position=card_data.position if card_data.position else max_pos,
                due_date=card_data.due_date,
                list_id=card_data.list_id,
                assigned_to=card_data.assigned_to
            )
            session.add(db_card)
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=lst.board_id,
                user_id=user_id,
                activity_type=ActivityType.CARD_CREATED,
                description=f"Created card '{card_data.title}'"
            )
            
            session.refresh(db_card)
            return CardResponse.model_validate(db_card)
    
    def get_card(self, card_id: str) -> Optional[CardResponse]:
        """Get a card by ID"""
        with self.get_session() as session:
            card = session.query(Card).filter(Card.id == card_id).first()
            return CardResponse.model_validate(card) if card else None
    
    def get_cards_by_list(self, list_id: str) -> List[CardResponse]:
        """Get all cards in a list"""
        with self.get_session() as session:
            cards = session.query(Card).filter(
                Card.list_id == list_id
            ).order_by(Card.position).all()
            return [CardResponse.model_validate(card) for card in cards]
    
    def get_cards_by_user(self, user_id: str) -> List[CardResponse]:
        """Get all cards assigned to a user"""
        with self.get_session() as session:
            cards = session.query(Card).filter(
                Card.assigned_to == user_id
            ).order_by(Card.due_date, Card.created_at).all()
            return [CardResponse.model_validate(card) for card in cards]
    
    def update_card(self, card_id: str, card_update: CardUpdate, user_id: str) -> Optional[CardResponse]:
        """Update a card"""
        with self.get_session() as session:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return None
            
            # Get board_id through list
            lst = session.query(DBList).filter(DBList.id == card.list_id).first()
            
            update_data = card_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(card, key, value)
            
            card.updated_at = datetime.utcnow()
            session.flush()
            
            # Log activity
            activity_type = ActivityType.CARD_UPDATED
            if 'list_id' in update_data:
                activity_type = ActivityType.CARD_MOVED
            elif 'assigned_to' in update_data:
                activity_type = ActivityType.CARD_ASSIGNED
            
            self._log_activity(
                session,
                board_id=lst.board_id,
                user_id=user_id,
                activity_type=activity_type,
                description=f"Updated card '{card.title}'"
            )
            
            session.refresh(card)
            return CardResponse.model_validate(card)
    
    def delete_card(self, card_id: str) -> bool:
        """Delete a card"""
        with self.get_session() as session:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return False
            session.delete(card)
            return True
    
    # ============================================
    # Comment Operations
    # ============================================
    
    def create_comment(self, comment_data: CommentCreate) -> CommentResponse:
        """Add a comment to a card"""
        with self.get_session() as session:
            # Get card to find board_id
            card = session.query(Card).filter(Card.id == comment_data.card_id).first()
            if not card:
                raise ValueError(f"Card {comment_data.card_id} not found")
            
            lst = session.query(DBList).filter(DBList.id == card.list_id).first()
            
            db_comment = Comment(
                content=comment_data.content,
                card_id=comment_data.card_id,
                user_id=comment_data.user_id
            )
            session.add(db_comment)
            session.flush()
            
            # Log activity
            self._log_activity(
                session,
                board_id=lst.board_id,
                user_id=comment_data.user_id,
                activity_type=ActivityType.COMMENT_ADDED,
                description=f"Added comment to card '{card.title}'"
            )
            
            session.refresh(db_comment)
            return CommentResponse.model_validate(db_comment)
    
    def get_comments_by_card(self, card_id: str) -> List[CommentResponse]:
        """Get all comments for a card"""
        with self.get_session() as session:
            comments = session.query(Comment).filter(
                Comment.card_id == card_id
            ).order_by(Comment.created_at.desc()).all()
            return [CommentResponse.model_validate(comment) for comment in comments]
    
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment"""
        with self.get_session() as session:
            comment = session.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                return False
            session.delete(comment)
            return True
    
    # ============================================
    # Activity Log Operations
    # ============================================
    
    def get_board_activities(self, board_id: str, limit: int = 50, offset: int = 0) -> List[ActivityLogResponse]:
        """Get activity log for a board"""
        with self.get_session() as session:
            activities = session.query(ActivityLog).filter(
                ActivityLog.board_id == board_id
            ).order_by(ActivityLog.created_at.desc()).limit(limit).offset(offset).all()
            return [ActivityLogResponse.model_validate(activity) for activity in activities]
    
    def _log_activity(self, session: Session, board_id: str, user_id: str, 
                     activity_type: ActivityType, description: str):
        """Internal method to log activities"""
        activity = ActivityLog(
            board_id=board_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description
        )
        session.add(activity)


# Global storage instance - reads DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/workboard.db")
storage = WorkBoardStorage(DATABASE_URL)
