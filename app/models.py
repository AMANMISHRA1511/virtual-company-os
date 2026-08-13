from datetime import datetime
from sqlalchemy import String,Text,DateTime,Integer,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class Task(Base):
    __tablename__='tasks'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    title:Mapped[str]=mapped_column(String(200))
    description:Mapped[str]=mapped_column(Text)
    assigned_role:Mapped[str]=mapped_column(String(60),default='manager')
    assigned_name:Mapped[str]=mapped_column(String(60),default='Aarav')
    status:Mapped[str]=mapped_column(String(40),default='queued')
    result:Mapped[str]=mapped_column(Text,default='')
    requires_approval:Mapped[bool]=mapped_column(Boolean,default=False)
    approved:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AuditLog(Base):
    __tablename__='audit_logs'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    task_id:Mapped[int]=mapped_column(Integer,default=0,index=True)
    actor:Mapped[str]=mapped_column(String(80))
    action:Mapped[str]=mapped_column(String(120))
    details:Mapped[str]=mapped_column(Text,default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class FileChange(Base):
    __tablename__='file_changes'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    project:Mapped[str]=mapped_column(String(100),default='demo-company')
    path:Mapped[str]=mapped_column(String(500))
    version:Mapped[int]=mapped_column(Integer,default=1)
    actor:Mapped[str]=mapped_column(String(80))
    action:Mapped[str]=mapped_column(String(30))
    task_id:Mapped[int]=mapped_column(Integer,default=0)
    note:Mapped[str]=mapped_column(Text,default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Handoff(Base):
    __tablename__='handoffs'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    project:Mapped[str]=mapped_column(String(100),default='demo-company')
    path:Mapped[str]=mapped_column(String(500))
    from_agent:Mapped[str]=mapped_column(String(80))
    to_agent:Mapped[str]=mapped_column(String(80))
    purpose:Mapped[str]=mapped_column(Text,default='')
    status:Mapped[str]=mapped_column(String(30),default='shared')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
