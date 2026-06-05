from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from database.db import Base


class Lead(Base):

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    phone_number = Column(String, unique=True)

    name = Column(String)

    email = Column(String)

    city = Column(String)

    target_goal = Column(String)

    course_interest = Column(String)

    institute_type = Column(String)

    conversation_summary = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )