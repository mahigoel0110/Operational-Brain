from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.document import DocumentModel
from app.models.interview import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewRecommendation,
)
from app.models.company_profile import CompanyProfile
from app.models.chat import ChatSession
from app.models.copilot import CopilotSession
from app.db.database import database

from app.core.security import hash_password

async def seed_oil_and_gas_data():
    # 1. Seed Users
    director = await User.find_one(User.email == "director@reliance.com")
    if not director:
        director = User(
            name="Operations Director",
            email="director@reliance.com",
            hashed_password=hash_password("Admin@123!"),
            role="Operations Director",
            department=None
        )
        await director.insert()
    
    manager = await User.find_one(User.email == "manager@reliance.com")
    if not manager:
        manager = User(
            name="Maintenance Manager",
            email="manager@reliance.com",
            hashed_password=hash_password("Manager@123!"),
            role="Department Manager",
            department="Maintenance"
        )
        await manager.insert()

    engineer = await User.find_one(User.email == "engineer@reliance.com")
    if not engineer:
        engineer = User(
            name="Mechanical Engineer",
            email="engineer@reliance.com",
            hashed_password=hash_password("Engineer@123!"),
            role="Field Engineer",
            department="Engineering"
        )
        await engineer.insert()

    # 2. Seed Organization
    org = await Organization.find_one(Organization.name == "Reliance Oil & Gas - Mumbai Offshore Platform")
    if not org:
        org = Organization(
            name="Reliance Oil & Gas - Mumbai Offshore Platform",
            industry="Oil & Gas",
            description="Mumbai Offshore Platform Operations Command",
            owner_id=str(director.id),
            members=[str(director.id), str(manager.id), str(engineer.id)]
        )
        await org.insert()
    else:
        members_updated = False
        for u in [director, manager, engineer]:
            if str(u.id) not in org.members:
                org.members.append(str(u.id))
                members_updated = True
        if members_updated:
            await org.save()

    # 3. Seed Departments (Workspaces)
    departments = [
        ("Engineering", "Engineering Drawings, P&IDs, Equipment Manuals, Datasheets, Specifications, Design Calculations, Projects"),
        ("Operations", "Operating Procedures, Shift Logs, Production Reports, Daily Reports, Startup Procedures, Shutdown Procedures"),
        ("Maintenance", "Work Orders, Maintenance Manuals, Calibration, Equipment History, Failure Records, Lubrication, Preventive Maintenance"),
        ("Inspection", "Inspection Logs, Corrosion Reports, NDT Records, Vessel Wall Thickness logs"),
        ("HSE", "Permit To Work, Incident Reports, Near Miss, Risk Assessment, Safety SOP, Emergency Procedures"),
        ("Quality", "Inspection Reports, Audit Reports, Quality Manual, CAPA, ISO, Testing Records"),
        ("Projects", "Project Charters, Gantt Charts, Milestones, Commissioning Reports, Handover Documentation"),
        ("Procurement", "Supplier Agreements, Equipment Orders, Spares Inventory, Lead-times, Vendor Audits"),
        ("Human Resources", "Competency Matrix, Shift Scheduling, Training Logs, Certifications, Emergency Contacts"),
        ("Finance", "Capital Expenditure (CAPEX), Operational Expenditure (OPEX), Maintenance Cost centers, Budgets")
    ]

    for dept_name, dept_desc in departments:
        ws = await Workspace.find_one(
            Workspace.organization_id == str(org.id),
            Workspace.name == dept_name
        )
        if not ws:
            ws = Workspace(
                organization_id=str(org.id),
                name=dept_name,
                description=dept_desc,
                workspace_type="General" if dept_name not in ["Maintenance", "HSE"] else dept_name,
                created_by=str(director.id)
            )
            await ws.insert()

async def init_db():
    """Initialize Beanie with the pre-configured database client"""
    try:
        await init_beanie(
            database=database,
            document_models=[
                User,
                Organization,
                Workspace,
                DocumentModel,
                InterviewSession,
                InterviewQuestion,
                InterviewAnswer,
                InterviewProgress,
                InterviewRecommendation,
                CompanyProfile,
                ChatSession,
                CopilotSession,
            ]
        )
        
        # Seed Oil & Gas data
        await seed_oil_and_gas_data()
    except Exception as e:
        print(f"Failed to initialize Beanie: {e}")
        raise