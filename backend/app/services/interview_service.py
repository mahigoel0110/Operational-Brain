"""
AI Interview Engine — Rule-Based, Zero External Dependencies.

Architecture:
  workspace.industry (from CompanyProfile)
      ↓
  INDUSTRY_QUESTION_BANK[industry][department]
      ↓
  Department queue: General → Dept1 → Dept2 → ...
      ↓ per answer
  FollowUpEngine.extract_triggers(answer) → follow-up question
      ↓
  If no follow-up → next department question
      ↓ on complete
  RecommendationEngine.generate() → InterviewRecommendation[]
  CompanyProfileEnricher.enrich() → CompanyProfile updated
"""

import logging
import re
from datetime import datetime, UTC
from typing import Optional, List, Dict, Tuple, Any

from app.models.interview import (
    InterviewSession, InterviewQuestion, InterviewAnswer,
    InterviewProgress, InterviewRecommendation
)
from app.models.company_profile import CompanyProfile

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRY QUESTION BANK
# Structure: {industry: {department: [(question_text, category)]}}
# "General" questions always appear first regardless of industry.
# ─────────────────────────────────────────────────────────────────────────────

UNIVERSAL_GENERAL_QUESTIONS: List[Tuple[str, str]] = [
    ("What does your company do? Please describe your main business.", "business"),
    ("Which locations or cities do you operate in?", "locations"),
    ("How many employees does your company have?", "employee_count"),
    ("What ERP system do you use, if any? (e.g., SAP, Oracle, Tally)", "erp"),
    ("What CRM system do you use, if any? (e.g., Salesforce, Zoho)", "crm"),
    ("Who are your primary customers or clients?", "customers"),
]

INDUSTRY_QUESTION_BANK: Dict[str, Dict[str, List[Tuple[str, str]]]] = {

    "Manufacturing": {
        "Production": [
            ("What products do you manufacture?", "products"),
            ("What are the main production stages or steps in your manufacturing process?", "processes"),
            ("What machines or equipment are used in production?", "machines"),
            ("Do you have documented Standard Operating Procedures (SOPs) for production?", "sops"),
            ("What is your current production capacity (units/day or tons/month)?", "capacity"),
            ("How do you track work-in-progress (WIP)?", "tracking"),
        ],
        "Quality": [
            ("Which quality or ISO standards do you follow? (e.g., ISO 9001, IATF 16949)", "standards"),
            ("What is your inspection process — incoming, in-process, and final?", "processes"),
            ("What are your main Quality KPIs? (e.g., defect rate, rejection rate)", "kpis"),
            ("What quality testing equipment do you use?", "equipment"),
        ],
        "Maintenance": [
            ("How is preventive maintenance scheduled for your machines?", "processes"),
            ("What is the breakdown response workflow when a machine fails?", "processes"),
            ("Are machine manuals and technical drawings readily accessible?", "documents"),
            ("Do you use a CMMS (Computerized Maintenance Management System)?", "systems"),
        ],
        "Safety": [
            ("What safety protocols and PPE requirements are in place on the production floor?", "protocols"),
            ("How are safety incidents reported and investigated?", "processes"),
            ("Do you conduct regular safety audits or toolbox talks?", "audits"),
            ("What hazardous materials, if any, are present on site?", "hazards"),
        ],
        "HR": [
            ("What is the onboarding process for new hires?", "processes"),
            ("How are employee records and payroll managed?", "systems"),
            ("What shift patterns do your production workers follow?", "shifts"),
        ],
        "Finance": [
            ("What accounting software do you use? (e.g., SAP, Tally, QuickBooks)", "systems"),
            ("What is the budget approval process for capital expenditure?", "processes"),
            ("How are purchase orders and vendor payments handled?", "processes"),
        ],
        "Procurement": [
            ("Who are your key raw material suppliers?", "suppliers"),
            ("What is your procurement lead time for critical materials?", "lead_times"),
            ("How do you manage inventory and reorder levels?", "inventory"),
        ],
    },

    "Healthcare": {
        "Clinical": [
            ("What clinical services or specialties does your facility offer?", "services"),
            ("What is the typical patient journey from admission to discharge?", "processes"),
            ("How many beds or consultation rooms does your facility have?", "capacity"),
            ("What medical equipment do you operate? (e.g., MRI, CT, ventilators)", "equipment"),
        ],
        "Pharmacy": [
            ("How is medication dispensing managed and tracked?", "processes"),
            ("What pharmacy management software do you use?", "systems"),
            ("How do you handle controlled substances and narcotics?", "compliance"),
        ],
        "Diagnostics": [
            ("What diagnostic tests or lab services do you offer?", "services"),
            ("How are patient samples collected, labeled, and tracked?", "processes"),
            ("What accreditations do your labs hold? (e.g., NABL, CAP)", "accreditations"),
        ],
        "Administration": [
            ("What Hospital Information System (HIS) do you use?", "systems"),
            ("How are appointments and scheduling managed?", "processes"),
            ("How is patient billing and insurance claims handled?", "billing"),
        ],
        "Compliance": [
            ("What regulatory bodies govern your facility? (e.g., NABH, JCI, CQC)", "regulators"),
            ("How often do you conduct internal compliance audits?", "audits"),
            ("How is patient data privacy and security managed?", "data_privacy"),
        ],
        "Biomedical": [
            ("How is medical equipment serviced and calibrated?", "maintenance"),
            ("Do you maintain equipment maintenance logs and calibration certificates?", "documents"),
        ],
    },

    "Finance": {
        "Risk & Compliance": [
            ("What risk management frameworks do you follow? (e.g., Basel, RBI guidelines)", "frameworks"),
            ("How is KYC and AML compliance managed?", "compliance"),
            ("How frequently are risk assessments conducted?", "frequency"),
        ],
        "Credit": [
            ("What types of loans or credit products do you offer?", "products"),
            ("What is the credit appraisal and approval process?", "processes"),
            ("How is loan delinquency and recovery managed?", "recovery"),
        ],
        "Operations": [
            ("What core banking or financial platform do you use?", "systems"),
            ("How are transactions processed and reconciled?", "processes"),
            ("What is the escalation process for operational failures?", "escalation"),
        ],
        "Audit": [
            ("How often are internal audits conducted?", "frequency"),
            ("What audit management tools do you use?", "systems"),
            ("How are audit findings tracked and resolved?", "processes"),
        ],
        "Treasury": [
            ("How is liquidity management and cash flow forecasting done?", "processes"),
            ("What treasury management system do you use?", "systems"),
        ],
    },

    "Education": {
        "Academic": [
            ("What courses, programs, or grades does your institution offer?", "programs"),
            ("How is the curriculum planned and reviewed?", "processes"),
            ("What is the student-to-teacher ratio?", "ratios"),
            ("How is student assessment and grading managed?", "assessment"),
        ],
        "Student Services": [
            ("How do students register for courses and manage their records?", "processes"),
            ("What student support services do you offer? (e.g., counseling, placement)", "services"),
            ("How is student attendance tracked?", "tracking"),
        ],
        "Administration": [
            ("What School/College Management System (SMS/CMS) do you use?", "systems"),
            ("How is the academic calendar and timetable planned?", "scheduling"),
            ("How is faculty recruitment and performance managed?", "hr"),
        ],
        "Finance": [
            ("How is fee collection and financial aid managed?", "billing"),
            ("What accounting system does the institution use?", "systems"),
        ],
        "IT": [
            ("What learning management system (LMS) do you use? (e.g., Moodle, Canvas)", "systems"),
            ("How is the campus IT infrastructure managed?", "infrastructure"),
        ],
    },

    "Technology": {
        "Engineering": [
            ("What is your primary technology stack or programming languages used?", "stack"),
            ("How is the software development lifecycle (SDLC) managed?", "processes"),
            ("How often do you release new features or product versions?", "releases"),
            ("What version control and CI/CD tools do you use?", "tools"),
        ],
        "Product": [
            ("What is the process for gathering and prioritizing product requirements?", "processes"),
            ("What product management tools do you use? (e.g., Jira, Linear, Notion)", "tools"),
            ("How is user feedback collected and incorporated?", "feedback"),
        ],
        "QA": [
            ("What is your testing strategy? (manual, automated, or both)", "strategy"),
            ("What test automation frameworks do you use?", "tools"),
            ("What is your bug tracking and resolution process?", "processes"),
        ],
        "Security": [
            ("What security frameworks or standards do you follow? (e.g., ISO 27001, SOC2)", "standards"),
            ("How is access control and identity management handled?", "iam"),
            ("How are security incidents detected and responded to?", "incident_response"),
        ],
        "DevOps": [
            ("What cloud infrastructure do you use? (e.g., AWS, GCP, Azure, on-prem)", "infrastructure"),
            ("How is infrastructure provisioning and configuration managed?", "iac"),
            ("What monitoring and alerting tools are in use?", "monitoring"),
        ],
        "Customer Success": [
            ("How is customer onboarding managed?", "processes"),
            ("What support ticket management system do you use?", "systems"),
            ("What are your SLA targets for customer support?", "sla"),
        ],
    },

    "Logistics": {
        "Fleet": [
            ("How many vehicles do you operate, and what types?", "fleet"),
            ("How is vehicle maintenance and GPS tracking managed?", "maintenance"),
            ("How are drivers recruited, trained, and managed?", "drivers"),
        ],
        "Warehouse": [
            ("What Warehouse Management System (WMS) do you use?", "systems"),
            ("How is inbound and outbound goods movement tracked?", "processes"),
            ("What is your inventory accuracy and cycle count process?", "inventory"),
        ],
        "Operations": [
            ("How are delivery routes planned and optimized?", "routing"),
            ("What is the process for handling delivery exceptions or failures?", "exceptions"),
            ("How are customer delivery confirmations captured?", "pod"),
        ],
        "Safety": [
            ("What driver safety training programs are in place?", "training"),
            ("How are vehicle accidents and incidents reported?", "incidents"),
        ],
    },

    "Energy": {
        "Operations": [
            ("What type of energy do you produce or distribute? (e.g., oil, gas, solar, coal)", "type"),
            ("What is your current production or generation capacity?", "capacity"),
            ("How are operational processes monitored and controlled? (SCADA, DCS?)", "control_systems"),
        ],
        "Maintenance": [
            ("How is equipment maintenance scheduled for critical assets?", "maintenance"),
            ("What is the process for managing planned shutdowns or turnarounds?", "shutdowns"),
            ("Do you use a CMMS for maintenance tracking?", "systems"),
        ],
        "Safety & HSE": [
            ("What HSE management system or standards do you follow? (e.g., ISO 14001, OHSAS 18001)", "standards"),
            ("How are environmental incidents reported and managed?", "incidents"),
            ("What is the permit-to-work process for hazardous tasks?", "permits"),
        ],
        "Engineering": [
            ("What engineering design and drawing management tools do you use?", "tools"),
            ("How is asset lifecycle management handled?", "asset_management"),
        ],
    },

    "Retail": {
        "Merchandising": [
            ("What product categories or SKUs do you carry?", "products"),
            ("How is product sourcing and vendor management handled?", "sourcing"),
            ("What is your planogram and shelf management process?", "planogram"),
        ],
        "Supply Chain": [
            ("How is inventory replenishment triggered? (manual, automatic, demand-driven)", "replenishment"),
            ("How many distribution centers or warehouses do you operate?", "infrastructure"),
            ("What supply chain management software do you use?", "systems"),
        ],
        "Store Operations": [
            ("How many stores or outlets do you operate?", "footprint"),
            ("What Point-of-Sale (POS) system do you use?", "pos"),
            ("How is store staff scheduling and attendance managed?", "hr"),
        ],
        "Customer Experience": [
            ("What loyalty or rewards program do you run?", "loyalty"),
            ("How are customer complaints and returns handled?", "processes"),
        ],
    },
}

# Default questions for unrecognized industries
DEFAULT_QUESTIONS: Dict[str, List[Tuple[str, str]]] = {
    "Operations": [
        ("What are the main operational processes in your organization?", "processes"),
        ("What software systems do you use for operations?", "systems"),
        ("How many people are in your operations team?", "team_size"),
    ],
    "Administration": [
        ("How is document and records management handled?", "documents"),
        ("What communication tools does your team use?", "tools"),
    ],
    "Finance": [
        ("What accounting and finance software do you use?", "systems"),
        ("What is the budget approval process?", "processes"),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# FOLLOW-UP TRIGGER RULES
# keyword → (follow-up question, category)
# ─────────────────────────────────────────────────────────────────────────────
FOLLOWUP_RULES: List[Tuple[List[str], str, str]] = [
    # Production machines
    (["rolling mill", "mill"], "Do you have Standard Operating Procedures (SOPs) specifically for the Rolling Mill?", "sops"),
    (["press", "hydraulic press", "cnc"], "Do you have maintenance records and SOPs for this equipment?", "sops"),
    (["furnace", "kiln", "oven"], "What are the temperature control procedures and safety protocols for this equipment?", "safety"),
    (["conveyor", "belt", "conveyor belt"], "How is conveyor maintenance and belt inspection scheduled?", "maintenance"),
    (["robot", "robotic", "automation"], "Are the robotic systems fully documented with integration manuals?", "documents"),

    # ERP / Systems
    (["sap"], "Which SAP modules are currently active? (e.g., PP, MM, QM, PM, FI)", "modules"),
    (["oracle"], "Which Oracle modules or Cloud services are you using?", "modules"),
    (["tally"], "Are you using Tally ERP 9 or TallyPrime? Which version?", "version"),
    (["salesforce"], "Which Salesforce clouds are you using? (Sales, Service, Marketing?)", "modules"),
    (["zoho"], "Which Zoho apps are you using? (CRM, Books, People, Inventory?)", "modules"),
    (["dynamics", "d365"], "Which Dynamics 365 modules are deployed?", "modules"),
    (["jira"], "How are backlogs and sprints managed in Jira? Do you use Scrum or Kanban?", "methodology"),

    # Standards & Certifications
    (["iso 9001", "9001"], "When was your last ISO 9001 audit, and what was the outcome?", "audit"),
    (["iso 14001", "14001"], "What environmental targets are tied to your ISO 14001 certification?", "targets"),
    (["iso 27001", "27001"], "Which information assets are in scope for your ISO 27001 certification?", "scope"),
    (["nabh", "jci", "joint commission"], "What was your last accreditation score, and what improvement areas were identified?", "improvement"),
    (["nabl"], "What test categories are covered under your NABL accreditation?", "scope"),

    # Employees / People
    (["50", "100", "200", "300", "500", "1000", "employees", "staff", "workers"], "How many of these employees are on the production or operations floor?", "headcount"),
    (["contractor", "contract workers", "vendors on site"], "How are contractor safety inductions and access managed?", "safety"),

    # Finance / Accounting
    (["quickbooks"], "Which version of QuickBooks are you using? (Online or Desktop?)", "version"),
    (["excel", "spreadsheet"], "Are there plans to move to a dedicated accounting or ERP system?", "roadmap"),
    (["purchase order", "po"], "What is the approval workflow for purchase orders above a certain value?", "approval"),

    # Locations
    (["multiple", "locations", "plants", "branches", "offices"], "Are these locations managed under a single ERP instance or separately?", "systems"),

    # Healthcare-specific
    (["patient"], "How many patient visits or admissions do you handle per day on average?", "volume"),
    (["icu", "intensive care"], "What is your ICU bed capacity and ventilator count?", "capacity"),
    (["his", "hospital information"], "Which Hospital Information System (HIS) vendor are you using?", "vendor"),
    (["emr", "ehr", "electronic medical"], "Is the EMR system integrated with billing and pharmacy?", "integration"),

    # Education-specific
    (["student", "students"], "What is the current total enrollment?", "enrollment"),
    (["online", "e-learning", "virtual"], "What platform hosts your online or virtual learning?", "platform"),
    (["lms", "moodle", "canvas", "blackboard"], "How are course materials and assessments delivered through the LMS?", "delivery"),

    # Logistics
    (["fleet", "trucks", "vehicles", "transport"], "How is vehicle tracking and telematics managed?", "tracking"),
    (["warehouse", "wms"], "What is the warehouse area in square feet and how many SKUs do you manage?", "scale"),

    # Technology
    (["aws", "azure", "gcp", "cloud"], "What is your monthly cloud infrastructure spend approximately?", "cost"),
    (["kubernetes", "docker", "containers"], "What is your container orchestration strategy and deployment pipeline?", "devops"),
    (["microservices", "micro-services"], "How many microservices are in production and how are they monitored?", "scale"),

    # General business
    (["export", "international", "global"], "Which countries or regions do you export to?", "markets"),
    (["b2b", "enterprise clients", "corporate"], "What is your typical sales cycle length?", "sales_cycle"),
    (["certification", "certified"], "How do you maintain and renew these certifications?", "renewal"),
]

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT RECOMMENDATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
DOCUMENT_RECOMMENDATIONS: Dict[str, List[Dict[str, str]]] = {
    "General": [
        {"document_name": "Company Overview / Business Profile", "priority": "high", "reason": "Foundational document for all AI learning"},
        {"document_name": "Organizational Chart", "priority": "high", "reason": "Maps roles and reporting structure"},
        {"document_name": "Vision, Mission & Values Statement", "priority": "medium", "reason": "Sets strategic context for AI decisions"},
    ],
    "Production": [
        {"document_name": "Standard Operating Procedures (SOPs)", "priority": "high", "reason": "AI needs SOPs to answer operational queries accurately"},
        {"document_name": "Machine / Equipment Manuals", "priority": "high", "reason": "Required for maintenance and troubleshooting queries"},
        {"document_name": "Production Process Flow Chart", "priority": "high", "reason": "Defines end-to-end production flow"},
        {"document_name": "Work Instructions", "priority": "medium", "reason": "Step-by-step guides for specific tasks"},
        {"document_name": "Capacity Planning Report", "priority": "medium", "reason": "Helps AI understand production constraints"},
    ],
    "Maintenance": [
        {"document_name": "Preventive Maintenance Schedule", "priority": "high", "reason": "Core document for maintenance planning queries"},
        {"document_name": "Machine Maintenance Logs", "priority": "high", "reason": "Historical data for failure pattern analysis"},
        {"document_name": "Calibration Records & Certificates", "priority": "high", "reason": "Required for quality and compliance queries"},
        {"document_name": "Spare Parts Catalog", "priority": "medium", "reason": "Essential for procurement and inventory queries"},
        {"document_name": "Breakdown Response Procedure", "priority": "medium", "reason": "Defines escalation paths during failures"},
    ],
    "Quality": [
        {"document_name": "Quality Manual", "priority": "high", "reason": "Foundation document for all quality queries"},
        {"document_name": "ISO / Certification Documents", "priority": "high", "reason": "Required for compliance and audit queries"},
        {"document_name": "Inspection Checklists", "priority": "high", "reason": "Needed for in-process and final inspection queries"},
        {"document_name": "Customer Complaint Handling Procedure", "priority": "medium", "reason": "Defines CAPA and resolution workflows"},
        {"document_name": "Test Method Documents", "priority": "medium", "reason": "Specifies how quality tests are conducted"},
    ],
    "Safety": [
        {"document_name": "Safety Manual / HSE Policy", "priority": "high", "reason": "Primary reference for all safety queries"},
        {"document_name": "Emergency Response Plan", "priority": "high", "reason": "Critical for incident management queries"},
        {"document_name": "Incident Report Form", "priority": "high", "reason": "Standardizes incident recording"},
        {"document_name": "Hazard Identification & Risk Assessment (HIRA)", "priority": "high", "reason": "Maps workplace hazards for AI awareness"},
        {"document_name": "PPE Requirements List", "priority": "medium", "reason": "Defines protective equipment standards per area"},
        {"document_name": "Safety Audit Checklist", "priority": "medium", "reason": "Enables AI to assist in safety audit preparation"},
    ],
    "HR": [
        {"document_name": "Employee Handbook", "priority": "high", "reason": "Covers HR policies and employee rights"},
        {"document_name": "Leave & Attendance Policy", "priority": "high", "reason": "Required for HR query responses"},
        {"document_name": "Onboarding Checklist", "priority": "medium", "reason": "Standardizes new hire onboarding process"},
        {"document_name": "Job Descriptions (JDs)", "priority": "medium", "reason": "Defines roles for competency queries"},
        {"document_name": "Performance Appraisal Form", "priority": "medium", "reason": "Enables AI to assist in performance management"},
    ],
    "Finance": [
        {"document_name": "Purchase Policy", "priority": "high", "reason": "Defines approval thresholds and vendor rules"},
        {"document_name": "Invoice Templates", "priority": "medium", "reason": "Standardizes billing outputs"},
        {"document_name": "Budget Template", "priority": "medium", "reason": "Needed for financial planning queries"},
        {"document_name": "Chart of Accounts", "priority": "medium", "reason": "Maps financial categories for accounting queries"},
        {"document_name": "Expense Claim Policy", "priority": "low", "reason": "Handles employee reimbursement queries"},
    ],
    "IT": [
        {"document_name": "IT Infrastructure Map / Network Diagram", "priority": "high", "reason": "Required for IT support and architecture queries"},
        {"document_name": "Data Backup & Recovery Policy", "priority": "high", "reason": "Critical for business continuity queries"},
        {"document_name": "User Access & Password Policy", "priority": "high", "reason": "Defines access control standards"},
        {"document_name": "Software License Inventory", "priority": "medium", "reason": "Tracks licensed tools for compliance queries"},
        {"document_name": "IT Incident Management Procedure", "priority": "medium", "reason": "Defines escalation for IT issues"},
    ],
    "Procurement": [
        {"document_name": "Vendor / Supplier List", "priority": "high", "reason": "Core reference for procurement queries"},
        {"document_name": "Purchase Order Template", "priority": "medium", "reason": "Standardizes procurement documents"},
        {"document_name": "Vendor Evaluation Criteria", "priority": "medium", "reason": "Enables AI to assist in vendor selection"},
    ],
    "Clinical": [
        {"document_name": "Clinical Protocols & Guidelines", "priority": "high", "reason": "Essential for clinical decision support queries"},
        {"document_name": "Patient Admission & Discharge Procedure", "priority": "high", "reason": "Defines patient flow"},
        {"document_name": "Infection Control Policy", "priority": "high", "reason": "Critical for healthcare safety queries"},
    ],
    "Compliance": [
        {"document_name": "Regulatory Compliance Checklist", "priority": "high", "reason": "Maps regulatory requirements"},
        {"document_name": "Audit Trail Logs", "priority": "high", "reason": "Required for compliance and audit queries"},
        {"document_name": "Data Privacy Policy (GDPR / HIPAA)", "priority": "high", "reason": "Covers data protection requirements"},
    ],
    "Academic": [
        {"document_name": "Curriculum & Syllabus Documents", "priority": "high", "reason": "Core academic reference"},
        {"document_name": "Examination Policy", "priority": "high", "reason": "Defines assessment standards"},
        {"document_name": "Faculty Handbook", "priority": "medium", "reason": "Covers faculty policies and procedures"},
    ],
    "Engineering": [
        {"document_name": "Technical Design Documents / Architecture Diagrams", "priority": "high", "reason": "Maps system architecture"},
        {"document_name": "API Documentation", "priority": "high", "reason": "Required for integration queries"},
        {"document_name": "Coding Standards / Style Guide", "priority": "medium", "reason": "Defines development standards"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# MISSING INFO TOPICS BY INDUSTRY
# ─────────────────────────────────────────────────────────────────────────────
MISSING_INFO_BY_INDUSTRY: Dict[str, List[str]] = {
    "Manufacturing": ["Machine specifications", "Production KPIs", "Quality rejection rates", "Maintenance MTTR/MTBF", "Safety incident history"],
    "Healthcare": ["Patient volume statistics", "Bed occupancy rates", "Clinical outcome metrics", "Medical equipment list", "Accreditation certificates"],
    "Finance": ["Portfolio size", "Regulatory filing history", "Risk exposure metrics", "Loan book size", "Audit findings"],
    "Education": ["Enrollment data", "Exam pass rates", "Faculty credentials", "Campus infrastructure map", "Accreditation status"],
    "Technology": ["System architecture diagrams", "API documentation", "Security posture", "Incident history", "SLA performance"],
    "Logistics": ["Fleet utilization rates", "Delivery SLA performance", "Warehouse throughput", "Driver safety record", "Fuel consumption data"],
    "Energy": ["Production/generation capacity", "Equipment reliability data", "Environmental compliance records", "HSE incident history", "Asset register"],
    "Retail": ["SKU count and catalog", "Inventory turnover rate", "Store-level sales data", "Customer satisfaction scores", "Shrinkage / loss data"],
}


# ─────────────────────────────────────────────────────────────────────────────
# DEPARTMENT QUEUE BY INDUSTRY
# ─────────────────────────────────────────────────────────────────────────────
DEPARTMENT_QUEUE_BY_INDUSTRY: Dict[str, List[str]] = {
    "Manufacturing": ["Production", "Quality", "Maintenance", "Safety", "HR", "Finance", "Procurement"],
    "Healthcare": ["Clinical", "Pharmacy", "Diagnostics", "Administration", "Compliance", "Biomedical"],
    "Finance": ["Risk & Compliance", "Credit", "Operations", "Audit", "Treasury"],
    "Education": ["Academic", "Student Services", "Administration", "Finance", "IT"],
    "Technology": ["Engineering", "Product", "QA", "Security", "DevOps", "Customer Success"],
    "Logistics": ["Fleet", "Warehouse", "Operations", "Safety"],
    "Energy": ["Operations", "Maintenance", "Safety & HSE", "Engineering"],
    "Retail": ["Merchandising", "Supply Chain", "Store Operations", "Customer Experience"],
    "default": ["Operations", "Administration", "Finance"],
}


# ─────────────────────────────────────────────────────────────────────────────
# AI TRANSITION PHRASES
# ─────────────────────────────────────────────────────────────────────────────
DEPT_TRANSITIONS: Dict[str, str] = {
    "Production": "Great. Now let me understand your **production operations**.",
    "Quality": "Thanks! Let's talk about **quality management**.",
    "Maintenance": "Got it. Moving on to **maintenance and equipment reliability**.",
    "Safety": "Now, let's cover **safety and compliance**.",
    "HR": "Let me ask a few questions about **human resources**.",
    "Finance": "Understood. Let's look at **finance and accounting**.",
    "Procurement": "A few quick questions about **procurement and supply chain**.",
    "Clinical": "Now let's discuss your **clinical operations**.",
    "Pharmacy": "Let me ask about your **pharmacy operations**.",
    "Diagnostics": "Let's cover **diagnostics and laboratory services**.",
    "Administration": "Now, some **administrative** questions.",
    "Compliance": "Important area — let's discuss **compliance and regulatory requirements**.",
    "Biomedical": "Let me ask about **biomedical engineering and equipment**.",
    "Risk & Compliance": "Let's cover **risk management and compliance**.",
    "Credit": "Now, questions about your **credit operations**.",
    "Operations": "Let me understand your **core operations**.",
    "Audit": "A few questions about **audit processes**.",
    "Treasury": "Let's touch on **treasury management**.",
    "Academic": "Let's move to **academic programs and curriculum**.",
    "Student Services": "Questions about **student support services** next.",
    "IT": "Let me ask about your **IT infrastructure**.",
    "Engineering": "Now, let's discuss your **engineering and development**.",
    "Product": "Questions about **product management** next.",
    "QA": "Let me ask about **quality assurance and testing**.",
    "Security": "Now let's cover **security practices**.",
    "DevOps": "Questions about **infrastructure and DevOps**.",
    "Customer Success": "Finally, let's discuss **customer success**.",
    "Fleet": "Let me ask about your **fleet operations**.",
    "Warehouse": "Questions about **warehouse management** next.",
    "Safety & HSE": "Now, let's cover **health, safety, and environment**.",
    "Merchandising": "Let me understand your **merchandising strategy**.",
    "Supply Chain": "Questions about your **supply chain** now.",
    "Store Operations": "Let me ask about **store operations**.",
    "Customer Experience": "Finally, questions about **customer experience**.",
}

COMPLETION_MESSAGES = [
    "Excellent work! I now have a comprehensive understanding of your organization. Let me compile your Company Profile.",
    "That's everything I needed! I've captured the key details about your organization. Generating your profile now.",
    "Perfect — I have a solid picture of your company now. Building your Company Profile and document recommendations.",
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _extract_followup(answer_text: str) -> Optional[Tuple[str, str]]:
    """
    Given a user answer, check if it triggers any follow-up question.
    Returns (follow_up_question, category) or None.
    """
    normalized = _normalize(answer_text)
    for keywords, followup_q, category in FOLLOWUP_RULES:
        for kw in keywords:
            if " " in kw:
                if kw in normalized:
                    return (followup_q, category)
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", normalized):
                    return (followup_q, category)
    return None


def _get_department_queue(industry: str) -> List[str]:
    return DEPARTMENT_QUEUE_BY_INDUSTRY.get(industry, DEPARTMENT_QUEUE_BY_INDUSTRY["default"])


def _get_dept_questions(industry: str, department: str) -> List[Tuple[str, str]]:
    bank = INDUSTRY_QUESTION_BANK.get(industry, {})
    questions = bank.get(department, [])
    if not questions:
        # Fall back to default
        questions = DEFAULT_QUESTIONS.get(department, [])
    return questions


def _calculate_knowledge_score(answers: List[InterviewAnswer], total_questions: int) -> int:
    """Compute a 0–100 knowledge score based on coverage and answer quality."""
    if total_questions == 0:
        return 0
    base = int((len(answers) / max(total_questions, 1)) * 70)
    # Bonus for detailed answers
    detailed = sum(1 for a in answers if len(a.answer.strip()) > 40)
    bonus = int((detailed / max(len(answers), 1)) * 30)
    return min(base + bonus, 100)


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION STATE STORE
# Lightweight in-process store to track generated (ephemeral) questions per session.
# Keyed by session_id → {"questions": [...], "index": N, "followup_pending": {...}}
# ─────────────────────────────────────────────────────────────────────────────
_SESSION_STATE: Dict[str, Dict] = {}


def _get_or_init_session_state(session: InterviewSession) -> Dict:
    sid = str(session.id)
    if sid not in _SESSION_STATE:
        industry = session.detected_industry or "default"
        dept_queue = session.department_queue or _get_department_queue(industry)

        # Build flat question list
        questions = []
        # Always start with general questions
        for q_text, category in UNIVERSAL_GENERAL_QUESTIONS:
            questions.append({"q": q_text, "category": category, "dept": "General", "id": None})

        # Then department questions
        for dept in dept_queue:
            dept_qs = _get_dept_questions(industry, dept)
            if dept_qs:
                for q_text, category in dept_qs:
                    questions.append({"q": q_text, "category": category, "dept": dept, "id": None})

        _SESSION_STATE[sid] = {
            "questions": questions,
            "index": 0,
            "followup_pending": None,   # {"q": ..., "category": ..., "dept": ...}
            "dept_queue": dept_queue,
        }
    return _SESSION_STATE[sid]


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE CLASSES
# ─────────────────────────────────────────────────────────────────────────────

class InterviewService:

    @staticmethod
    async def start_interview(workspace_id: str, user_id: str) -> InterviewSession:
        """Start or resume an interview session for a workspace."""
        # Check for existing in_progress session
        existing = await InterviewSession.find_one(
            {"workspace_id": workspace_id, "status": "in_progress"}
        )
        if existing:
            # Re-initialize state in case server restarted
            _get_or_init_session_state(existing)
            return existing

        # Detect industry from CompanyProfile
        profile = await CompanyProfile.find_one({"workspace_id": workspace_id})
        detected_industry = profile.industry if profile and profile.industry else "default"

        dept_queue = _get_department_queue(detected_industry)
        all_depts = ["General"] + dept_queue

        session = InterviewSession(
            workspace_id=workspace_id,
            created_by=user_id,
            status="in_progress",
            current_department="General",
            progress={d: 0 for d in all_depts},
            completion_percentage=0,
            detected_industry=detected_industry,
            department_queue=dept_queue,
        )
        await session.insert()

        # Initialize progress tracker
        progress = InterviewProgress(
            session_id=str(session.id),
            workspace_id=workspace_id,
            knowledge_score=0,
            department_confidence={d: 0 for d in all_depts},
            missing_info=MISSING_INFO_BY_INDUSTRY.get(detected_industry, []),
            questions_asked=0,
            questions_answered=0,
        )
        await progress.insert()

        # Initialize in-process state
        _get_or_init_session_state(session)
        return session

    @staticmethod
    async def get_first_question(session: InterviewSession) -> Dict[str, Any]:
        """Return the opening AI message + first question."""
        industry = session.detected_industry or "General"
        state = _get_or_init_session_state(session)

        opening = (
            f"Hello! I'm your OperationalBrain AI assistant. I'm going to ask you a series of questions "
            f"to build a comprehensive understanding of your organization.\n\n"
            f"I've detected that you're in the **{industry}** industry. I'll tailor my questions accordingly. "
            f"Let's start with some general questions.\n\n"
            f"**{state['questions'][0]['q']}**"
        )

        state["index"] = 1
        await InterviewProgress.find_one({"session_id": str(session.id)}).update(
            {"$inc": {"questions_asked": 1}}
        )
        return {
            "ai_message": opening,
            "question_text": state["questions"][0]["q"],
            "department": "General",
            "category": state["questions"][0]["category"],
            "question_index": 0,
            "is_followup": False,
            "session_complete": False,
        }

    @staticmethod
    async def process_answer(
        session: InterviewSession,
        question_text: str,
        department: str,
        category: str,
        answer_text: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Process the user's answer and return the next AI message.
        Handles follow-up logic and department transitions.
        """
        sid = str(session.id)
        state = _SESSION_STATE.get(sid)
        if not state:
            state = _get_or_init_session_state(session)

        # Persist the answer
        answer_obj = InterviewAnswer(
            session_id=sid,
            question_text=question_text,
            question_id=f"{department}_{category}_{state['index']}",
            answer=answer_text,
            answered_by=user_id,
            department=department,
        )
        await answer_obj.insert()

        # Update progress tracker
        prog = await InterviewProgress.find_one({"session_id": sid})
        if prog:
            prog.questions_answered += 1
            prog.questions_asked = state["index"] + 1

        # Check for follow-up
        followup = _extract_followup(answer_text)
        prev_followup = state.get("followup_pending")

        if followup and not prev_followup:
            # Queue a follow-up question
            state["followup_pending"] = {
                "q": followup[0],
                "category": followup[1],
                "dept": department,
            }
            if prog:
                prog.questions_asked += 1
                await prog.save()
            return {
                "ai_message": followup[0],
                "question_text": followup[0],
                "department": department,
                "category": followup[1],
                "is_followup": True,
                "session_complete": False,
            }

        # Clear pending follow-up
        state["followup_pending"] = None

        # Move to next question
        idx = state["index"]
        questions = state["questions"]

        if idx >= len(questions):
            # All questions answered
            if prog:
                all_answers = await InterviewAnswer.find({"session_id": sid}).to_list()
                prog.knowledge_score = _calculate_knowledge_score(all_answers, len(questions))
                await prog.save()
            return {
                "ai_message": COMPLETION_MESSAGES[0],
                "question_text": None,
                "department": None,
                "category": None,
                "is_followup": False,
                "session_complete": True,
            }

        next_q = questions[idx]
        state["index"] += 1

        # Check if we crossed into a new department
        prev_dept = department
        next_dept = next_q["dept"]
        transition_msg = ""
        if next_dept != prev_dept:
            transition_msg = DEPT_TRANSITIONS.get(next_dept, f"Now let's discuss **{next_dept}**.") + "\n\n"

        # Update current department on session
        if next_dept != session.current_department:
            session.current_department = next_dept
            await session.save()

        ai_message = f"{transition_msg}**{next_q['q']}**"

        if prog:
            await prog.save()

        return {
            "ai_message": ai_message,
            "question_text": next_q["q"],
            "department": next_dept,
            "category": next_q["category"],
            "is_followup": False,
            "session_complete": False,
        }

    @staticmethod
    async def complete_interview(session_id: str) -> InterviewSession:
        session = await InterviewSession.get(session_id)
        if not session:
            raise ValueError("Session not found")

        session.status = "completed"
        session.completed_at = datetime.now(UTC)
        session.completion_percentage = 100
        await session.save()

        # Generate company profile
        await CompanyProfileEnricher.enrich(session_id)

        # Generate document recommendations
        await RecommendationEngine.generate(session_id)

        return session

    @staticmethod
    async def get_progress(session_id: str) -> Dict[str, Any]:
        session = await InterviewSession.get(session_id)
        if not session:
            return {}

        prog = await InterviewProgress.find_one({"session_id": session_id})
        state = _SESSION_STATE.get(session_id)
        total_q = len(state["questions"]) if state else 1
        answered = prog.questions_answered if prog else 0
        overall = int((answered / max(total_q, 1)) * 100)

        # Compute per-department progress
        dept_progress: Dict[str, int] = {}
        answers = await InterviewAnswer.find({"session_id": session_id}).to_list()
        answered_depts: Dict[str, int] = {}
        for a in answers:
            answered_depts[a.department] = answered_depts.get(a.department, 0) + 1

        all_depts = ["General"] + (session.department_queue or [])
        if state:
            dept_total: Dict[str, int] = {}
            for q in state["questions"]:
                dept_total[q["dept"]] = dept_total.get(q["dept"], 0) + 1
            for dept in all_depts:
                total = dept_total.get(dept, 1)
                done = answered_depts.get(dept, 0)
                dept_progress[dept] = min(int((done / total) * 100), 100)

        # Knowledge score
        knowledge_score = _calculate_knowledge_score(answers, total_q)
        if prog:
            prog.knowledge_score = knowledge_score
            prog.questions_answered = answered
            await prog.save()

        session.progress = dept_progress
        session.completion_percentage = overall
        await session.save()

        return {
            "progress": dept_progress,
            "completion_percentage": overall,
            "current_department": session.current_department,
            "knowledge_score": knowledge_score,
            "department_confidence": prog.department_confidence if prog else {},
            "missing_info": prog.missing_info if prog else [],
            "questions_asked": prog.questions_asked if prog else 0,
            "questions_answered": answered,
        }


class CompanyProfileEnricher:
    """Enriches CompanyProfile with interview answers after completion."""

    @staticmethod
    async def enrich(session_id: str):
        session = await InterviewSession.get(session_id)
        if not session:
            return

        answers = await InterviewAnswer.find({"session_id": session_id}).to_list()
        profile = await CompanyProfile.find_one({"workspace_id": session.workspace_id})

        if not profile:
            profile = CompanyProfile(workspace_id=session.workspace_id)

        machines: List[str] = []
        processes: List[str] = []
        standards: List[str] = []
        locations: List[str] = []
        products: List[str] = []
        dept_summaries: Dict[str, str] = {}

        for ans in answers:
            a = ans.answer.strip()
            cat = ans.category if hasattr(ans, "category") else ""
            dept = ans.department

            q_lower = ans.question_text.lower() if ans.question_text else ""
            a_lower = a.lower()

            if "employee" in q_lower or "staff" in q_lower or "worker" in q_lower:
                profile.employee_count = a
            elif "erp" in q_lower:
                profile.erp = a
            elif "location" in q_lower or "cities" in q_lower or "plant" in q_lower:
                locations.append(a)
            elif "machine" in q_lower or "equipment" in q_lower:
                machines.append(a)
            elif "standard" in q_lower or "iso" in q_lower or "certif" in q_lower:
                standards.append(a)
            elif "product" in q_lower or "manufactur" in q_lower or "produc" in a_lower:
                products.append(a)
            elif "process" in q_lower or "workflow" in q_lower or "procedure" in q_lower:
                processes.append(f"{dept}: {a}")

            # Build per-department summaries
            if dept and dept != "General":
                existing_summary = dept_summaries.get(dept, "")
                addition = f"Q: {ans.question_text}\nA: {a}\n"
                dept_summaries[dept] = existing_summary + addition

        if machines:
            profile.machines = list(set(profile.machines + machines))
        if standards:
            profile.standards = list(set(profile.standards + standards))
        if processes:
            profile.processes = list(set(profile.processes + processes))
        if products:
            profile.products = list(set(profile.products + products))
        if locations:
            profile.departments = profile.departments or []
        if dept_summaries:
            profile.department_summaries = {**profile.department_summaries, **dept_summaries}

        # Update industry from session
        if session.detected_industry:
            profile.industry = session.detected_industry

        # Compute readiness score
        prog = await InterviewProgress.find_one({"session_id": session_id})
        if prog:
            profile.ai_readiness_score = prog.knowledge_score

        # Departments covered
        answered_depts = list(set(a.department for a in answers))
        profile.departments = list(set((profile.departments or []) + answered_depts))

        await profile.save()
        logger.info(f"CompanyProfile enriched for workspace {session.workspace_id}")


class RecommendationEngine:
    """Generates document recommendations after interview."""

    @staticmethod
    async def generate(session_id: str):
        session = await InterviewSession.get(session_id)
        if not session:
            return

        # Clear existing recommendations for session
        existing = await InterviewRecommendation.find({"session_id": session_id}).to_list()
        for r in existing:
            await r.delete()

        # Get departments covered in the interview
        answers = await InterviewAnswer.find({"session_id": session_id}).to_list()
        covered_depts = list(set(a.department for a in answers))

        # Always include General
        if "General" not in covered_depts:
            covered_depts.insert(0, "General")

        for dept in covered_depts:
            dept_docs = DOCUMENT_RECOMMENDATIONS.get(dept, [])
            for doc_info in dept_docs:
                rec = InterviewRecommendation(
                    session_id=session_id,
                    workspace_id=session.workspace_id,
                    department=dept,
                    document_name=doc_info["document_name"],
                    priority=doc_info["priority"],
                    reason=doc_info["reason"],
                )
                await rec.insert()

        logger.info(f"Generated document recommendations for session {session_id}")

    @staticmethod
    async def get_recommendations(session_id: str) -> List[InterviewRecommendation]:
        return await InterviewRecommendation.find({"session_id": session_id}).to_list()


# ─────────────────────────────────────────────────────────────────────────────
# Legacy compatibility (old API routes still call these)
# ─────────────────────────────────────────────────────────────────────────────

class QuestionService:
    @staticmethod
    async def seed_questions():
        pass  # No-op — we use dynamic in-memory questions now

    @staticmethod
    async def get_next_question(session_id: str):
        return None  # Legacy endpoint — replaced by /chat


class ProgressService:
    @staticmethod
    async def calculate_progress(session_id: str) -> dict:
        return await InterviewService.get_progress(session_id)


class AnswerService:
    @staticmethod
    async def submit_answer(session_id: str, question_id: str, answer_text: str, user_id: str) -> InterviewAnswer:
        answer = InterviewAnswer(
            session_id=session_id,
            question_id=question_id,
            question_text="",
            answer=answer_text,
            answered_by=user_id,
            department="General",
        )
        await answer.insert()
        return answer
