from datetime import date, datetime, time
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class HCP(Base):
    __tablename__='hcps'
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(120), unique=True, index=True)
    specialty: Mapped[str|None]=mapped_column(String(120))
    institution: Mapped[str|None]=mapped_column(String(180))
    interactions: Mapped[list['Interaction']]=relationship(back_populates='hcp', cascade='all, delete-orphan')

class Interaction(Base):
    __tablename__='interactions'
    id: Mapped[int]=mapped_column(primary_key=True)
    hcp_id: Mapped[int]=mapped_column(ForeignKey('hcps.id'), index=True)
    interaction_type: Mapped[str]=mapped_column(String(60), default='Meeting')
    interaction_date: Mapped[date]=mapped_column(Date)
    interaction_time: Mapped[time|None]=mapped_column(Time)
    attendees: Mapped[str|None]=mapped_column(Text)
    topics_discussed: Mapped[str]=mapped_column(Text)
    materials_shared: Mapped[str|None]=mapped_column(Text)
    samples_distributed: Mapped[str|None]=mapped_column(Text)
    sentiment: Mapped[str]=mapped_column(String(20), default='Neutral')
    outcomes: Mapped[str|None]=mapped_column(Text)
    follow_up_actions: Mapped[str|None]=mapped_column(Text)
    ai_summary: Mapped[str|None]=mapped_column(Text)
    source: Mapped[str]=mapped_column(String(20), default='form')
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    hcp: Mapped[HCP]=relationship(back_populates='interactions')
    follow_ups: Mapped[list['FollowUp']]=relationship(back_populates='interaction', cascade='all, delete-orphan')

class FollowUp(Base):
    __tablename__='follow_ups'
    id: Mapped[int]=mapped_column(primary_key=True)
    interaction_id: Mapped[int|None]=mapped_column(ForeignKey('interactions.id'), index=True)
    hcp_id: Mapped[int]=mapped_column(ForeignKey('hcps.id'), index=True)
    due_date: Mapped[date]=mapped_column(Date)
    task: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30), default='Open')
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    interaction: Mapped[Interaction|None]=relationship(back_populates='follow_ups')
    hcp: Mapped[HCP]=relationship()
