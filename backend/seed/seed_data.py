import sys
import os
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, os.path.abspath("."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash, UserRole
from backend.app.models.region import Region
from backend.app.models.institution import Institution
from backend.app.models.user import User
from backend.app.models.workflow import WorkflowDefinition, WorkflowStage
from backend.app.models.application import Application, ApplicationHistory
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.compliance import ComplianceObligation, ComplianceEvidence
from backend.app.models.document import DocumentRegistry
from backend.app.models.alert import Alert
from backend.app.models.notification import NotificationOutbox
from backend.app.services.audit_service import audit_service


def seed_database(db_session=None):
    print("Beginning SETU Synthetic Database Seeding...")
    close_db_at_end = False
    if db_session is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db_at_end = True
    else:
        db = db_session

    try:
        # Check if already seeded
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Database already contains {existing_users} users. Skipping seed.")
            return

        demo_password_hash = get_password_hash("DemoPass@2026")
        now = datetime.now(timezone.utc)
        today = date.today()

        # 1. Seed Regions
        regions_data = [
            {"code": "RO_NORTH", "name": "Northern Regional Office", "states_covered": "Uttar Pradesh, Uttarakhand"},
            {"code": "RO_WEST", "name": "Western Regional Office", "states_covered": "Maharashtra, Goa"},
            {"code": "RO_SOUTH", "name": "Southern Regional Office", "states_covered": "Tamil Nadu, Puducherry"},
            {"code": "RO_EAST", "name": "Eastern Regional Office", "states_covered": "West Bengal, Odisha, Bihar"},
            {"code": "RO_CENTRAL", "name": "Central Regional Office", "states_covered": "Madhya Pradesh, Chhattisgarh"},
        ]
        regions_map = {}
        for r_data in regions_data:
            reg = Region(**r_data)
            db.add(reg)
            db.flush()
            regions_map[r_data["code"]] = reg

        print(f"Created {len(regions_map)} Regions.")

        # 2. Seed 10 Fictional Institutions
        institutions_data = [
            {"aicte_id": "1-100234501", "name": "National Institute of Science & Technology (Fictional)", "region_code": "RO_NORTH", "district": "Kanpur", "state": "Uttar Pradesh", "contact_email": "registrar@nist-fictional.ac.in"},
            {"aicte_id": "1-100234502", "name": "Apex Engineering College (Fictional)", "region_code": "RO_NORTH", "district": "Dehradun", "state": "Uttarakhand", "contact_email": "info@apex-engg-fictional.edu.in"},
            {"aicte_id": "1-100234503", "name": "Western Polytechnic Institute (Fictional)", "region_code": "RO_WEST", "district": "Pune", "state": "Maharashtra", "contact_email": "principal@western-poly-fictional.org"},
            {"aicte_id": "1-100234504", "name": "Sahyadri Technology Academy (Fictional)", "region_code": "RO_WEST", "district": "Nagpur", "state": "Maharashtra", "contact_email": "admin@sahyadri-fictional.edu"},
            {"aicte_id": "1-100234505", "name": "Southern Advanced Tech Institute (Fictional)", "region_code": "RO_SOUTH", "district": "Chennai", "state": "Tamil Nadu", "contact_email": "dean@southern-tech-fictional.ac.in"},
            {"aicte_id": "1-100234506", "name": "Coimbatore Institute of Engineering (Fictional)", "region_code": "RO_SOUTH", "district": "Coimbatore", "state": "Tamil Nadu", "contact_email": "contact@cie-fictional.edu"},
            {"aicte_id": "1-100234507", "name": "Kalinga School of Management (Fictional)", "region_code": "RO_EAST", "district": "Bhubaneswar", "state": "Odisha", "contact_email": "director@kalinga-mgmt-fictional.ac.in"},
            {"aicte_id": "1-100234508", "name": "Bengal Rural Polytechnic (Fictional)", "region_code": "RO_EAST", "district": "Kolkata", "state": "West Bengal", "contact_email": "principal@bengal-poly-fictional.org"},
            {"aicte_id": "1-100234509", "name": "Malwa Institute of Applied Technology (Fictional)", "region_code": "RO_CENTRAL", "district": "Indore", "state": "Madhya Pradesh", "contact_email": "info@malwa-tech-fictional.edu"},
            {"aicte_id": "1-100234510", "name": "Central Tribal Technical Institute (Fictional)", "region_code": "RO_CENTRAL", "district": "Raipur", "state": "Chhattisgarh", "contact_email": "admin@ctti-fictional.ac.in"},
        ]
        institutions_map = {}
        for inst_data in institutions_data:
            reg = regions_map[inst_data.pop("region_code")]
            inst = Institution(region_id=reg.id, **inst_data)
            db.add(inst)
            db.flush()
            institutions_map[inst.aicte_id] = inst

        print(f"Created {len(institutions_map)} Fictional Institutions.")

        # 3. Seed Users across all 8 Roles
        users_data = [
            {
                "email": "inst_admin@fictional-nist.edu.in",
                "full_name": "Dr. R. K. Verma (Inst Admin 1)",
                "role": UserRole.INST_ADMIN.value,
                "institution_id": institutions_map["1-100234501"].id,
                "region_id": regions_map["RO_NORTH"].id,
            },
            {
                "email": "inst_admin2@fictional-poly.org",
                "full_name": "Prof. S. M. Patil (Inst Admin 2)",
                "role": UserRole.INST_ADMIN.value,
                "institution_id": institutions_map["1-100234503"].id,
                "region_id": regions_map["RO_WEST"].id,
            },
            {
                "email": "ro_north@aicte.gov.in",
                "full_name": "Dr. Arun Mehra (Regional Officer North)",
                "role": UserRole.RO_OFFICER.value,
                "region_id": regions_map["RO_NORTH"].id,
            },
            {
                "email": "ro_west@aicte.gov.in",
                "full_name": "Smt. Sunita Deshmukh (Regional Officer West)",
                "role": UserRole.RO_OFFICER.value,
                "region_id": regions_map["RO_WEST"].id,
            },
            {
                "email": "bo_officer@aicte.gov.in",
                "full_name": "Shri Vikramaditya Sen (Bureau Officer)",
                "role": UserRole.BO_OFFICER.value,
                "region_id": None,
            },
            {
                "email": "evc_coord@aicte.gov.in",
                "full_name": "Dr. Preeti Saxena (EVC Coordinator)",
                "role": UserRole.EVC_COORD.value,
                "region_id": regions_map["RO_NORTH"].id,
            },
            {
                "email": "comm_member@aicte.gov.in",
                "full_name": "Prof. H. S. Murthy (Committee Member)",
                "role": UserRole.COMM_MEMBER.value,
                "region_id": None,
            },
            {
                "email": "comp_review@aicte.gov.in",
                "full_name": "Shri Rajeshwar Rao (Compliance Reviewer)",
                "role": UserRole.COMP_REVIEW.value,
                "region_id": regions_map["RO_NORTH"].id,
            },
            {
                "email": "comp_auth@aicte.gov.in",
                "full_name": "Member Secretary / Competent Authority (AICTE)",
                "role": UserRole.COMP_AUTH.value,
                "region_id": None,
            },
            {
                "email": "sys_admin@aicte.gov.in",
                "full_name": "Administrator (SETU Tech Ops)",
                "role": UserRole.SYS_ADMIN.value,
                "region_id": None,
            },
        ]
        users_map = {}
        for u_data in users_data:
            user = User(
                email=u_data["email"],
                hashed_password=demo_password_hash,
                full_name=u_data["full_name"],
                role=u_data["role"],
                institution_id=u_data.get("institution_id"),
                region_id=u_data.get("region_id"),
                is_active=True
            )
            db.add(user)
            db.flush()
            users_map[user.email] = user

        print(f"Created {len(users_map)} Demo Users across 8 RBAC Roles.")

        # 4. Seed Workflow Definitions & Stages (Routes A, B, C, D)
        workflows_data = [
            {
                "code": "ROUTE_A",
                "name": "Route A: Only Scrutiny",
                "description": "Standard extension without expansion. Submission -> Scrutiny -> Regional Review -> Competent Decision.",
                "stages": [
                    ("DRAFT", "Draft Application", 1, 0, False),
                    ("SUBMITTED", "Submitted / Regional Intake", 2, 2, False),
                    ("UNDER_SCRUTINY", "Scrutiny in Progress", 3, 7, False),
                    ("SCRUTINY_DEFICIENT", "Clarification Requested", 4, 10, False),
                    ("SCRUTINY_RECOMMENDED", "Scrutiny Cleared / Review", 5, 3, False),
                    ("DECISION_PENDING", "Decision Pending (Competent Auth)", 6, 5, False),
                    ("APPROVED", "Approved", 7, 0, True),
                    ("REJECTED", "Rejected", 8, 0, True),
                ]
            },
            {
                "code": "ROUTE_B",
                "name": "Route B: Scrutiny + EVC",
                "description": "New programmes or significant intake increase. Scrutiny -> EVC Inspection -> Regional Review -> Decision.",
                "stages": [
                    ("DRAFT", "Draft Application", 1, 0, False),
                    ("SUBMITTED", "Submitted / Regional Intake", 2, 2, False),
                    ("UNDER_SCRUTINY", "Scrutiny in Progress", 3, 7, False),
                    ("SCRUTINY_DEFICIENT", "Clarification Requested", 4, 10, False),
                    ("EVC_QUEUE", "Awaiting EVC Scheduling", 5, 7, False),
                    ("EVC_SCHEDULED", "EVC Inspection Scheduled", 6, 14, False),
                    ("EVC_COMPLETED", "Visit Conducted / Report Awaited", 7, 3, False),
                    ("EVC_REPORT_SUBMITTED", "Report Under Review", 8, 3, False),
                    ("DECISION_PENDING", "Decision Pending (Competent Auth)", 9, 5, False),
                    ("APPROVED", "Approved", 10, 0, True),
                    ("REJECTED", "Rejected", 10, 0, True),
                ]
            },
            {
                "code": "ROUTE_C",
                "name": "Route C: EVC + SAC/SHC",
                "description": "Hearings & Appeals for discrepancies. EVC Deficiencies -> SHC Hearing -> SAC Appeal -> Decision.",
                "stages": [
                    ("DRAFT", "Draft Application", 1, 0, False),
                    ("SUBMITTED", "Submitted", 2, 2, False),
                    ("EVC_QUEUE", "Awaiting EVC Scheduling", 3, 7, False),
                    ("EVC_COMPLETED", "EVC Visit Done", 4, 3, False),
                    ("SHC_QUEUE", "Standing Hearing Committee", 5, 10, False),
                    ("SAC_APPEAL", "Standing Appellate Committee", 6, 14, False),
                    ("DECISION_PENDING", "Decision Pending (Competent Auth)", 7, 5, False),
                    ("APPROVED", "Approved", 8, 0, True),
                    ("REJECTED", "Rejected", 8, 0, True),
                ]
            },
            {
                "code": "ROUTE_D",
                "name": "Route D: Only EVC",
                "description": "Mandated physical verification or surprise infrastructure audits.",
                "stages": [
                    ("DRAFT", "Draft Application", 1, 0, False),
                    ("SUBMITTED", "Submitted", 2, 2, False),
                    ("EVC_QUEUE", "Awaiting EVC Scheduling", 3, 7, False),
                    ("EVC_SCHEDULED", "EVC Inspection Scheduled", 4, 14, False),
                    ("EVC_COMPLETED", "Visit Conducted / Report Awaited", 5, 3, False),
                    ("DECISION_PENDING", "Decision Pending (Competent Auth)", 6, 5, False),
                    ("APPROVED", "Approved", 7, 0, True),
                    ("REJECTED", "Rejected", 7, 0, True),
                ]
            }
        ]

        stages_lookup = {}
        for w_data in workflows_data:
            wf = WorkflowDefinition(
                code=w_data["code"],
                name=w_data["name"],
                description=w_data["description"]
            )
            db.add(wf)
            db.flush()

            for skey, sname, seq, sla, term in w_data["stages"]:
                stg = WorkflowStage(
                    workflow_id=wf.id,
                    stage_key=skey,
                    name=sname,
                    sequence_order=seq,
                    sla_days=sla,
                    is_terminal=term
                )
                db.add(stg)
                db.flush()
                stages_lookup[(w_data["code"], skey)] = stg

        print(f"Created 4 Workflow Routes and {len(stages_lookup)} Workflow Stages.")

        # 5. Seed 25+ Diverse Synthetic Applications across Routes A, B, C, D
        sample_applications = [
            # ROUTE A (Only Scrutiny)
            ("1-100234501", "ROUTE_A", "UNDER_SCRUTINY", 4, "ro_north@aicte.gov.in", 0, "Extension of Approval (EoA)"),
            ("1-100234502", "ROUTE_A", "SCRUTINY_DEFICIENT", 12, "ro_north@aicte.gov.in", 1, "Increase in Intake - Computer Science"),
            ("1-100234503", "ROUTE_A", "SUBMITTED", 1, None, 0, "Extension of Approval (EoA)"),
            ("1-100234504", "ROUTE_A", "SCRUTINY_RECOMMENDED", 6, "ro_west@aicte.gov.in", 0, "Introduction of New Course (AI & DS)"),
            ("1-100234505", "ROUTE_A", "DECISION_PENDING", 16, "ro_north@aicte.gov.in", 0, "Extension of Approval (EoA)"),
            ("1-100234506", "ROUTE_A", "APPROVED", 25, "ro_north@aicte.gov.in", 0, "Extension of Approval (EoA)"),
            ("1-100234507", "ROUTE_A", "REJECTED", 28, "ro_north@aicte.gov.in", 2, "Closure of Course - Mechanical Engg"),
            ("1-100234508", "ROUTE_A", "UNDER_SCRUTINY", 9, "ro_north@aicte.gov.in", 0, "Change of Site / Location"),
            
            # ROUTE B (Scrutiny + EVC)
            ("1-100234501", "ROUTE_B", "EVC_QUEUE", 8, "evc_coord@aicte.gov.in", 0, "Setting up New Technical Institution"),
            ("1-100234502", "ROUTE_B", "EVC_SCHEDULED", 5, "evc_coord@aicte.gov.in", 0, "Introduction of Supernumerary Seats"),
            ("1-100234503", "ROUTE_B", "EVC_COMPLETED", 4, "evc_coord@aicte.gov.in", 0, "New Programme - Integrated MCA"),
            ("1-100234504", "ROUTE_B", "EVC_REPORT_SUBMITTED", 6, "ro_west@aicte.gov.in", 0, "Setting up New Technical Campus"),
            ("1-100234505", "ROUTE_B", "DECISION_PENDING", 18, "bo_officer@aicte.gov.in", 0, "Restoration of Intake"),
            ("1-100234506", "ROUTE_B", "UNDER_SCRUTINY", 3, None, 0, "Conversion of Women's Inst to Co-ed"),
            ("1-100234507", "ROUTE_B", "EVC_QUEUE", 11, "evc_coord@aicte.gov.in", 0, "Setting up New Polytechnic"),
            ("1-100234508", "ROUTE_B", "APPROVED", 30, "bo_officer@aicte.gov.in", 0, "New Degree in Engineering"),

            # ROUTE C (EVC + SAC/SHC)
            ("1-100234509", "ROUTE_C", "SHC_QUEUE", 15, "comm_member@aicte.gov.in", 1, "Appeal against EVC Deficiency Notice"),
            ("1-100234510", "ROUTE_C", "SAC_APPEAL", 22, "comm_member@aicte.gov.in", 2, "Standing Appellate Appeal on Land Norms"),
            ("1-100234501", "ROUTE_C", "DECISION_PENDING", 26, "bo_officer@aicte.gov.in", 1, "Hearing Outcome on Faculty Cadre Ratio"),
            ("1-100234502", "ROUTE_C", "REJECTED", 35, "bo_officer@aicte.gov.in", 2, "Non-compliance of Barrier-Free Access"),
            ("1-100234503", "ROUTE_C", "SHC_QUEUE", 7, "comm_member@aicte.gov.in", 0, "Discrepancy in Built-up Area"),

            # ROUTE D (Only EVC)
            ("1-100234504", "ROUTE_D", "EVC_QUEUE", 14, None, 0, "Surprise Physical Verification"),
            ("1-100234505", "ROUTE_D", "EVC_SCHEDULED", 3, "evc_coord@aicte.gov.in", 0, "Infrastructure Audit"),
            ("1-100234506", "ROUTE_D", "EVC_COMPLETED", 2, "evc_coord@aicte.gov.in", 0, "Verification of Fire NOC Clearances"),
            ("1-100234507", "ROUTE_D", "DECISION_PENDING", 9, "bo_officer@aicte.gov.in", 0, "Post-Inspection Governance Audit"),
            ("1-100234508", "ROUTE_D", "APPROVED", 19, "bo_officer@aicte.gov.in", 0, "Complaint Verification Cleared"),
        ]

        apps_created = []
        for a_idx, (inst_aicte_id, route_code, stage_key, days_ago, officer_email, ret_cnt, app_type) in enumerate(sample_applications, start=101):
            inst = institutions_map[inst_aicte_id]
            stg = stages_lookup.get((route_code, stage_key))
            officer = users_map.get(officer_email) if officer_email else None
            
            sub_date = now - timedelta(days=days_ago + 3)
            stage_date = now - timedelta(days=days_ago)
            sla_days = stg.sla_days if stg else 7
            deadline = stage_date + timedelta(days=sla_days) if sla_days > 0 else None

            app = Application(
                application_no=f"AICTE-2026-{a_idx:04d}",
                institution_id=inst.id,
                region_id=inst.region_id,
                academic_year="2026-2027",
                application_type=app_type,
                route=route_code,
                current_stage_id=stg.id if stg else None,
                status=stage_key,
                assigned_officer_id=officer.id if officer else None,
                submitted_at=sub_date,
                stage_entered_at=stage_date,
                current_sla_deadline=deadline,
                is_paused=False,
                return_count=ret_cnt
            )
            db.add(app)
            db.flush()
            apps_created.append(app)

            # Add initial history event
            h = ApplicationHistory(
                application_id=app.id,
                to_stage_id=stg.id if stg else None,
                action="INITIAL_SEED_STAGE",
                actor_id=officer.id if officer else None,
                comments=f"Application entered {stage_key} stage via synthetic seed."
            )
            db.add(h)

        print(f"Created {len(apps_created)} Synthetic Applications across Routes A, B, C, D.")

        # Record Genesis Audit Event
        audit_service.record_event(
            db=db,
            actor_role="SYSTEM",
            action="INITIAL_SEED_DATABASE",
            entity_type="SYSTEM",
            entity_id="00000000-0000-0000-0000-000000000001",
            new_state="SEEDED",
            details={"version": "1.0.0", "timestamp": now.isoformat()}
        )

        db.commit()
        print("SETU Database Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        if close_db_at_end:
            db.close()


if __name__ == "__main__":
    seed_database()
