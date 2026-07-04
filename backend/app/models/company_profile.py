from datetime import datetime, UTC
from beanie import Document
from pydantic import Field
from typing import List, Dict, Optional

class CompanyProfile(Document):
    workspace_id: str
    organization_id: Optional[str] = None
    
    # Core Fields from Interview
    company_name: Optional[str] = None
    industry: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    employee_count: Optional[str] = None
    erp: Optional[str] = None
    machines: List[str] = Field(default_factory=list)
    standards: List[str] = Field(default_factory=list)
    processes: List[str] = Field(default_factory=list)
    
    # Synthesized from interviews and documents
    core_business: str = Field(default="")
    
    # Department specific summaries: {"Safety": "Safety protocols involve...", "Operations": ...}
    department_summaries: Dict[str, str] = Field(default_factory=dict)
    
    # Intelligence gaps detected by the AI
    missing_policies: List[str] = Field(default_factory=list)
    missing_critical_sops: List[str] = Field(default_factory=list)
    
    # Overall AI confidence
    ai_readiness_score: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "company_profiles"
