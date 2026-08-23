from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gstin = Column(String(15), unique=True, nullable=False)
    agency_name = Column(String(255), nullable=False)
    bank_account_hash = Column(String(255), nullable=False)
    contact_phone = Column(String(20))
    risk_rating = Column(Float, default=0.00)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mp_id = Column(String(50), nullable=False)  # Important for the MP Dashboard view
    project_title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String(100), nullable=False)
    estimated_cost = Column(Float, nullable=False)
    sanctioned_amount = Column(Float, nullable=False)
    state_nodal_agency = Column(String(255), nullable=False) # For State Dashboard view
    district_authority = Column(String(255), nullable=False) # For District Dashboard view
    
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id"))
    
    start_date = Column(Date, nullable=False)
    expected_end_date = Column(Date, nullable=False)
    current_progress_pct = Column(Integer, default=0)
    status = Column(String(50), default='SANCTIONED')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agency = relationship("Agency")
    transactions = relationship("Transaction", back_populates="project")
    blockchain_records = relationship("BlockchainLedger", back_populates="project")
    compliance_alerts = relationship("ComplianceAlertModel", back_populates="project")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    reference_id = Column(String(255), unique=True, nullable=False)
    pfms_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    project = relationship("Project", back_populates="transactions")

class ComplianceAlertModel(Base):
    """
    NOTE: We adapted this from the original 'ml_risk_alerts' to match our 
    new pivot (storing actual human-readable alerts rather than opaque math scores).
    """
    __tablename__ = "compliance_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    alert_type = Column(String(100), nullable=False) # e.g., FINANCIAL_DEVIATION
    message = Column(String, nullable=False)
    severity = Column(String(20), nullable=False) # CRITICAL, HIGH, MEDIUM
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    project = relationship("Project", back_populates="compliance_alerts")

class BlockchainLedger(Base):
    __tablename__ = "blockchain_ledger"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    local_data_hash = Column(String(256), nullable=False)
    onchain_tx_hash = Column(String(256), nullable=False)
    block_number = Column(Integer, nullable=False)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    project = relationship("Project", back_populates="blockchain_records")
