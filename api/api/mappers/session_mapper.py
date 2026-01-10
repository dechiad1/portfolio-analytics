from domain.models.session import Session
from api.schemas.session import SessionResponse, CreateSessionResponse


class SessionMapper:
    """Maps between Session domain models and API schemas."""

    @staticmethod
    def to_response(session: Session) -> SessionResponse:
        """Convert a Session domain model to a SessionResponse."""
        return SessionResponse(
            id=session.id,
            created_at=session.created_at,
            last_accessed_at=session.last_accessed_at,
        )

    @staticmethod
    def to_create_response(session: Session) -> CreateSessionResponse:
        """Convert a Session domain model to a CreateSessionResponse."""
        return CreateSessionResponse(
            session_id=session.id,
            created_at=session.created_at,
        )
