from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.schemas.attention import BottleneckSummary
from backend.app.services.bottleneck_service import BottleneckService


router = APIRouter(prefix="/api/bottlenecks", tags=["Bottleneck & Exception Cockpit"])


@router.get("/exceptions", response_model=BottleneckSummary)
def get_bottleneck_cockpit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns exception cockpit isolating stalled items into
    'Waiting on Institution' vs 'Waiting on AICTE Internal'.
    """
    return BottleneckService.get_bottleneck_exceptions(db=db, user=current_user)


@router.get("/dependencies")
def get_compliance_dependency_graph(
    institution_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compliance Dependency View:
    Returns full navigational dependency hierarchy connecting
    Institution -> Applications -> Compliance Obligations -> Prescribed Documents.
    """
    if current_user.role == "INST_ADMIN":
        institution_id = current_user.institution_id

    query = db.query(Institution)
    if institution_id:
        query = query.filter(Institution.id == institution_id)
    elif current_user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"] and current_user.region_id:
        query = query.filter(Institution.region_id == current_user.region_id)

    institutions = query.limit(10).all()

    nodes = []
    links = []

    for inst in institutions:
        inst_node_id = f"inst_{inst.id}"
        nodes.append({
            "id": inst_node_id,
            "label": inst.name,
            "type": "INSTITUTION",
            "status": "ACTIVE"
        })

        # Apps
        for app in inst.applications:
            app_node_id = f"app_{app.id}"
            nodes.append({
                "id": app_node_id,
                "label": f"{app.application_no} ({app.route})",
                "type": "APPLICATION",
                "status": app.status
            })
            links.append({"source": inst_node_id, "target": app_node_id, "relationship": "OWNS_APPLICATION"})

            # Obligations
            for ob in app.compliance_obligations:
                ob_node_id = f"ob_{ob.id}"
                nodes.append({
                    "id": ob_node_id,
                    "label": f"{ob.category}: {ob.title[:25]}",
                    "type": "COMPLIANCE_OBLIGATION",
                    "status": ob.status
                })
                links.append({"source": app_node_id, "target": ob_node_id, "relationship": "CONDITIONAL_ON"})

        # Documents
        docs = db.query(DocumentRegistry).filter(DocumentRegistry.institution_id == inst.id).all()
        for doc in docs:
            doc_node_id = f"doc_{doc.id}"
            nodes.append({
                "id": doc_node_id,
                "label": f"{doc.document_category} v{doc.current_version}",
                "type": "PRESCRIBED_DOCUMENT",
                "status": doc.status
            })
            links.append({"source": inst_node_id, "target": doc_node_id, "relationship": "HOLDS_DOCUMENT"})

    return {
        "nodes": nodes,
        "links": links
    }
