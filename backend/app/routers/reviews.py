from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.human_review import (
    HumanReviewResponse,
    HumanReviewAuditLogResponse,
    HumanReviewResolvePayload,
)
from app.services import human_review_service

router = APIRouter(tags=["reviews"])

@router.get(
    "/api/reviews",
    response_model=List[HumanReviewResponse],
    summary="List all human reviews with optional status filter",
)
def list_reviews(
    status: Optional[str] = Query(None, description="Filter by status: pending, in_review, approved, rejected, resolved"),
    db: Session = Depends(get_db),
):
    return human_review_service.list_human_reviews(db, status_filter=status)

@router.get(
    "/api/reviews/{id}",
    response_model=HumanReviewResponse,
    summary="Get human review by ID",
)
def get_review(
    id: int,
    db: Session = Depends(get_db),
):
    review = human_review_service.get_human_review(db, review_id=id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Human review with id {id} not found."
        )
    return review

@router.get(
    "/api/tasks/{task_id}/review",
    response_model=HumanReviewResponse,
    summary="Get human review for task ID",
)
def get_review_by_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    review = human_review_service.get_human_review_by_task(db, task_id=task_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No human review found for task {task_id}."
        )
    return review

@router.post(
    "/api/reviews/{id}/start",
    response_model=HumanReviewResponse,
    summary="Transition review from pending to in_review",
)
def start_review(
    id: int,
    db: Session = Depends(get_db),
):
    return human_review_service.start_human_review(db, review_id=id)

@router.post(
    "/api/reviews/{id}/resolve",
    response_model=HumanReviewResponse,
    summary="Resolve human review as APPROVE or REJECT",
)
def resolve_review(
    id: int,
    payload: HumanReviewResolvePayload,
    db: Session = Depends(get_db),
):
    return human_review_service.resolve_human_review(
        db,
        review_id=id,
        decision=payload.decision,
        reviewer_note=payload.reviewer_note,
    )

@router.get(
    "/api/reviews/{id}/audit",
    response_model=List[HumanReviewAuditLogResponse],
    summary="Get human review audit logs",
)
def get_review_audit_logs(
    id: int,
    db: Session = Depends(get_db),
):
    # Check if review exists
    review = human_review_service.get_human_review(db, review_id=id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Human review with id {id} not found."
        )
    return human_review_service.get_human_review_audit_logs(db, review_id=id)
