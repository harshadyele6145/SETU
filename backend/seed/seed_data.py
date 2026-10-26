import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, os.path.abspath("."))

from backend.app.core.config import settings
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


def seed_database(db_session=None, generate_alerts: bool = False):
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
                "email": "ro_west_dir@aicte.gov.in",
                "full_name": "Dr. S. K. Mahajan (Regional Director West)",
                "role": UserRole.REGIONAL_DIR.value,
                "region_id": regions_map["RO_WEST"].id,
            },
            {
                "email": "bo_officer@aicte.gov.in",
                "full_name": "Shri Vikramaditya Sen (Bureau Officer)",
                "role": UserRole.BO_OFFICER.value,
                "region_id": None,
            },
            {
                "email": "bureau_officer@aicte.gov.in",
                "full_name": "Dr. Meenakshi Sundaram (Bureau Officer)",
                "role": UserRole.BUREAU_OFFICER.value,
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
                "email": "expert1@aicte-roster.ac.in",
                "full_name": "Dr. Sunita Deshmukh (Expert Panel Member)",
                "role": UserRole.COMMITTEE_MBR.value,
                "region_id": None,
            },
            {
                "email": "comp_review@aicte.gov.in",
                "full_name": "Shri Rajeshwar Rao (Compliance Reviewer)",
                "role": UserRole.COMP_REVIEW.value,
                "region_id": regions_map["RO_NORTH"].id,
            },
            {
                "email": "compliance_reviewer@aicte.gov.in",
                "full_name": "Shri Vikramaditya Rao (Compliance Reviewer)",
                "role": UserRole.COMP_REV.value,
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

        # 5b. Seed EVC Visits and Expert Panelists
        apps_by_no = {app.application_no: app for app in apps_created}
        if "AICTE-2026-0110" in apps_by_no:
            app_b = apps_by_no["AICTE-2026-0110"]
            visit_b = EVCVisit(
                application_id=app_b.id,
                status="SCHEDULED",
                proposed_date=today - timedelta(days=2),
                confirmed_date=today + timedelta(days=3),
                coordinator_id=users_map["evc_coord@aicte.gov.in"].id
            )
            db.add(visit_b)
            db.flush()

            exp_b1 = EVCExpert(
                visit_id=visit_b.id,
                expert_name="Dr. Sunita Deshmukh",
                designation="Professor, Mechanical Engg",
                organization="IIT Bombay",
                contact_email="expert1@aicte-roster.ac.in",
                status="ASSIGNED"
            )
            exp_b2 = EVCExpert(
                visit_id=visit_b.id,
                expert_name="Prof. H. S. Murthy",
                designation="Professor, Electrical Engg",
                organization="IISc Bangalore",
                contact_email="comm_member@aicte.gov.in",
                status="ASSIGNED"
            )
            exp_b3 = EVCExpert(
                visit_id=visit_b.id,
                expert_name="Dr. K. R. Raman",
                designation="Architect & Urban Planner",
                organization="SPA Delhi",
                contact_email="expert_architect@aicte-roster.ac.in",
                status="ASSIGNED"
            )
            db.add_all([exp_b1, exp_b2, exp_b3])

        if "AICTE-2026-0123" in apps_by_no:
            app_d = apps_by_no["AICTE-2026-0123"]
            visit_d = EVCVisit(
                application_id=app_d.id,
                status="SCHEDULED",
                proposed_date=today - timedelta(days=1),
                confirmed_date=today + timedelta(days=4),
                coordinator_id=users_map["evc_coord@aicte.gov.in"].id
            )
            db.add(visit_d)
            db.flush()

            exp_d1 = EVCExpert(
                visit_id=visit_d.id,
                expert_name="Dr. Sunita Deshmukh",
                designation="Professor, Mechanical Engg",
                organization="IIT Bombay",
                contact_email="expert1@aicte-roster.ac.in",
                status="ASSIGNED"
            )
            exp_d2 = EVCExpert(
                visit_id=visit_d.id,
                expert_name="Prof. H. S. Murthy",
                designation="Professor, Electrical Engg",
                organization="IISc Bangalore",
                contact_email="comm_member@aicte.gov.in",
                status="ASSIGNED"
            )
            db.add_all([exp_d1, exp_d2])

        if "AICTE-2026-0111" in apps_by_no:
            app_comp = apps_by_no["AICTE-2026-0111"]
            visit_comp = EVCVisit(
                application_id=app_comp.id,
                status="COMPLETED",
                proposed_date=today - timedelta(days=8),
                confirmed_date=today - timedelta(days=4),
                completed_date=today - timedelta(days=4),
                report_summary="Campus physical verification completed. Land and laboratory setup matches APH norm. Report uploaded.",
                coordinator_id=users_map["evc_coord@aicte.gov.in"].id
            )
            db.add(visit_comp)

        # 6. Seed 12+ Compliance Obligations across Institutions
        obligations_data = [
            ("1-100234501", "FIRE_SAFETY", "Annual Municipal Fire NOC Renewal", "Submit updated Chief Fire Officer safety certificate.", today + timedelta(days=20), "UPCOMING", "Dr. S. K. Gupta"),
            ("1-100234501", "BARRIER_FREE", "Barrier-Free Access & Ramp Construction", "Install braille-enabled lifts and ramps across Academic Block B.", today + timedelta(days=5), "DUE_SOON", "Dr. S. K. Gupta"),
            ("1-100234502", "LAB_EQUIPMENT", "AI & Robotics Lab Commissioning", "Submit purchase invoices and physical installation photos for 30 high-performance GPU workstations.", today - timedelta(days=3), "OVERDUE", "Prof. N. K. Sharma"),
            ("1-100234502", "FACULTY_CADRE", "Cadre Ratio Compliance (1:2:6)", "Appoint 2 Professors and 4 Associate Professors in Electronics & Communication.", today + timedelta(days=45), "UPCOMING", "Prof. N. K. Sharma"),
            ("1-100234503", "SOLAR_ENERGY", "Rooftop Solar Plant Installation (25kW)", "Commission green energy grid per APH mandate.", today + timedelta(days=12), "SUBMITTED", "Principal S. M. Patil"),
            ("1-100234503", "SEWAGE_TREATMENT", "Sewage Treatment Plant (STP) Clearance", "Submit State Pollution Control Board clearance certificate.", today - timedelta(days=10), "DEFICIENT", "Principal S. M. Patil"),
            ("1-100234504", "DIGITAL_LIBRARY", "E-Journal Subscription & NDLI Club Registration", "Renew IEEE and Elsevier institutional digital subscriptions.", today + timedelta(days=80), "UPCOMING", "Dean Academics"),
            ("1-100234505", "INTERNAL_COMPLAINTS", "Internal Complaints Committee (ICC) Constitution", "Constitute ICC per AICTE Regulations 2016 and display on website.", today - timedelta(days=60), "CLOSED", "Registrar"),
            ("1-100234506", "FIRE_SAFETY", "Hostel Block Fire NOC", "Submit fire safety clearance for 400-bed student residence.", today + timedelta(days=2), "DUE_SOON", "Warden / Estate Officer"),
            ("1-100234507", "CAMPUS_SECURITY", "CCTV Surveillance System Certification", "Install 360-degree high-definition coverage in examination control rooms.", today + timedelta(days=30), "UPCOMING", "Security Officer"),
            ("1-100234508", "LANGUAGE_LAB", "Advanced English Communication Lab Setup", "Commission 40-seat multimedia audio-visual language software.", today + timedelta(days=15), "UPCOMING", "HOD Humanities"),
            ("1-100234509", "STRUCTURAL_SAFETY", "Structural Stability Certificate", "Submit certified civil audit from Government Engineering College.", today - timedelta(days=1), "OVERDUE", "Estate Manager"),
            ("1-100234510", "WATER_CONSERVATION", "Rainwater Harvesting Pit Construction", "Construct 3 rainwater recharging borewells on campus.", today + timedelta(days=60), "UPCOMING", "Campus Architect"),
        ]

        for inst_aicte_id, cat, title, desc_text, due, ob_status, resp in obligations_data:
            inst = institutions_map[inst_aicte_id]
            ob = ComplianceObligation(
                institution_id=inst.id,
                category=cat,
                title=title,
                description=desc_text,
                condition_source="APH Condition Precedent",
                due_date=due,
                status=ob_status,
                responsible_person=resp
            )
            db.add(ob)

        # 7. Seed Prescribed Document Registry (Lease Deeds, Land Titles, Safety NOCs)
        documents_data = [
            ("1-100234501", "LEASE_DEED", "Registered Campus Land Lease Deed (30 Years)", today - timedelta(days=365*29 + 300), today + timedelta(days=65), 1, "EXPIRING_SOON"),
            ("1-100234502", "FIRE_NOC", "Municipal Fire Safety Clearance", today - timedelta(days=360), today + timedelta(days=5), 1, "EXPIRING_SOON"),
            ("1-100234503", "BUILDING_SAFETY", "Structural Stability Certificate (Civil Audit)", today - timedelta(days=730), today - timedelta(days=15), 1, "EXPIRED"),
            ("1-100234504", "LEASE_DEED", "Perpetual Land Ownership Title Deed", today - timedelta(days=365*10), today + timedelta(days=365*20), 1, "VALID"),
            ("1-100234505", "OCCUPANCY_CERT", "Municipal Corporation Building Occupancy Certificate", today - timedelta(days=1000), today + timedelta(days=365*15), 1, "VALID"),
            ("1-100234506", "FIRE_NOC", "Fire NOC - Academic Complex", today - timedelta(days=350), today + timedelta(days=15), 1, "EXPIRING_SOON"),
            ("1-100234507", "AICTE_AFFIDAVIT", "Anti-Ragging & Non-Capitation Fee Affidavit", today - timedelta(days=100), today + timedelta(days=265), 1, "VALID"),
            ("1-100234508", "LEASE_DEED", "Registered Land Lease Agreement", today - timedelta(days=365*29 + 350), today - timedelta(days=5), 1, "EXPIRED"),
            ("1-100234509", "BUILDING_SAFETY", "National Building Code Compliance Clearance", today - timedelta(days=400), today + timedelta(days=330), 1, "VALID"),
            ("1-100234510", "OCCUPANCY_CERT", "Provisional Completion & Occupancy Certificate", today - timedelta(days=180), today + timedelta(days=185), 1, "VALID"),
        ]

        # Ensure simulated_document_record.pdf exists in storage
        storage_dir = Path(settings.STORAGE_DIR)
        storage_dir.mkdir(parents=True, exist_ok=True)
        sim_pdf = storage_dir / "simulated_document_record.pdf"
        if not sim_pdf.exists():
            sim_pdf.write_bytes(
                b"%PDF-1.4\nBT /F1 12 Tf 72 712 Td (AICTE Official Regulatory Document Record) Tj ET\n"
                b"BT /F1 10 Tf 72 690 Td (Registered Land Lease Deed and NOC Approval 2026) Tj ET\n%%EOF"
            )

        for inst_aicte_id, doc_cat, doc_title, iss_dt, exp_dt, ver, doc_st in documents_data:
            inst = institutions_map[inst_aicte_id]
            doc = DocumentRegistry(
                institution_id=inst.id,
                document_category=doc_cat,
                title=doc_title,
                issue_date=iss_dt,
                expiry_date=exp_dt,
                current_version=ver,
                status=doc_st,
                file_path="simulated_document_record.pdf",
                file_size=1024 * 250,
                mime_type="application/pdf",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            )
            db.add(doc)

        print(f"Created {len(obligations_data)} Compliance Obligations and {len(documents_data)} Prescribed Documents.")

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

        # Trigger deadline evaluation to populate alerts and notification outbox if requested
        if generate_alerts:
            from backend.app.services.alert_service import AlertService
            eval_summary = AlertService.evaluate_and_generate_alerts(db)
            print(f"Generated {eval_summary['new_alerts_created']} Alerts ({eval_summary['notifications_enqueued']} Notifications enqueued).")

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
