"""Project service for managing projects and document assignments."""

import logging
import uuid
from math import ceil

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import traced
from app.models.document import Document
from app.models.project import Project
from app.models.project_document import ProjectDocument
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


@traced()
async def create_project(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    """
    Create a new project.

    Args:
        db: Database session
        user_id: User ID
        data: Project creation data

    Returns:
        Created Project instance
    """
    project = Project(
        user_id=user_id,
        name=data.name,
        description=data.description,
    )
    db.add(project)
    await db.flush()

    logger.info(f"Created project {project.id} for user {user_id}")
    return project


@traced()
async def get_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Project | None:
    """
    Get a project by ID (with ownership check).

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check

    Returns:
        Project if found and owned by user, None otherwise
    """
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@traced()
async def get_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Project], int]:
    """
    Get paginated projects for a user.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (projects list, total count)
    """
    # Count total
    count_stmt = select(func.count(Project.id)).where(Project.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Get paginated projects
    offset = (page - 1) * per_page
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    return projects, total


@traced()
async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ProjectUpdate,
) -> Project | None:
    """
    Update a project.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check
        data: Project update data

    Returns:
        Updated Project if found and owned by user, None otherwise
    """
    project = await get_project(db, project_id, user_id)
    if not project:
        return None

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    await db.flush()
    logger.info(f"Updated project {project_id}")
    return project


@traced()
async def delete_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Delete a project.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check

    Returns:
        True if deleted, False if not found
    """
    project = await get_project(db, project_id, user_id)
    if not project:
        return False

    await db.delete(project)
    await db.flush()

    logger.info(f"Deleted project {project_id}")
    return True


@traced()
async def assign_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    document_ids: list[uuid.UUID],
) -> int:
    """
    Assign documents to a project.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check
        document_ids: List of document IDs to assign

    Returns:
        Number of documents added
    """
    # Verify project ownership
    project = await get_project(db, project_id, user_id)
    if not project:
        raise ValueError("Project not found or access denied")

    # Get existing assignments
    existing_stmt = select(ProjectDocument.document_id).where(
        ProjectDocument.project_id == project_id,
        ProjectDocument.document_id.in_(document_ids),
    )
    result = await db.execute(existing_stmt)
    existing_ids = set(result.scalars().all())

    # Verify document ownership
    doc_stmt = select(Document.id).where(
        Document.id.in_(document_ids),
        Document.user_id == user_id,
    )
    result = await db.execute(doc_stmt)
    valid_doc_ids = set(result.scalars().all())

    # Create new assignments for valid documents not already assigned
    count = 0
    for doc_id in document_ids:
        if doc_id in valid_doc_ids and doc_id not in existing_ids:
            project_doc = ProjectDocument(
                project_id=project_id,
                document_id=doc_id,
            )
            db.add(project_doc)
            count += 1

    await db.flush()
    logger.info(f"Assigned {count} documents to project {project_id}")
    return count


@traced()
async def remove_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    document_ids: list[uuid.UUID],
) -> int:
    """
    Remove documents from a project.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check
        document_ids: List of document IDs to remove

    Returns:
        Number of documents removed
    """
    # Verify project ownership
    project = await get_project(db, project_id, user_id)
    if not project:
        raise ValueError("Project not found or access denied")

    # Delete assignments
    stmt = delete(ProjectDocument).where(
        ProjectDocument.project_id == project_id,
        ProjectDocument.document_id.in_(document_ids),
    )
    result = await db.execute(stmt)
    count = result.rowcount

    await db.flush()
    logger.info(f"Removed {count} documents from project {project_id}")
    return count


@traced()
async def get_project_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Document]:
    """
    Get all documents assigned to a project.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check

    Returns:
        List of documents
    """
    # Verify project ownership
    project = await get_project(db, project_id, user_id)
    if not project:
        raise ValueError("Project not found or access denied")

    # Get documents via join
    stmt = (
        select(Document)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .where(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.added_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@traced()
async def get_project_with_counts(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[Project | None, int, int]:
    """
    Get a project with document and conversation counts.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID for ownership check

    Returns:
        Tuple of (project, document_count, conversation_count)
    """
    project = await get_project(db, project_id, user_id)
    if not project:
        return None, 0, 0

    # Count documents
    doc_count_stmt = select(func.count(ProjectDocument.id)).where(
        ProjectDocument.project_id == project_id
    )
    doc_count = (await db.execute(doc_count_stmt)).scalar() or 0

    # Count conversations
    from app.models.conversation import Conversation

    conv_count_stmt = select(func.count(Conversation.id)).where(
        Conversation.project_id == project_id
    )
    conv_count = (await db.execute(conv_count_stmt)).scalar() or 0

    return project, doc_count, conv_count


def calculate_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages."""
    return ceil(total / per_page) if per_page > 0 else 0
