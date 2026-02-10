"""
Demo Config model - stores configurable demo assignment IDs
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from database import Base


class DemoConfig(Base):
    """Demo configuration table - stores settings modifiable via database

    This table stores the assignment IDs for the 4 demo practice modes.
    Values can be updated via SQL without redeployment.

    Keys:
    - demo_reading_assignment_id: Assignment ID for example sentence reading demo
    - demo_rearrangement_assignment_id: Assignment ID for sentence rearrangement demo
    - demo_vocabulary_assignment_id: Assignment ID for vocabulary reading demo
    - demo_word_selection_assignment_id: Assignment ID for word selection demo
    """

    __tablename__ = "demo_config"

    key = Column(String(100), primary_key=True, comment="Configuration key")
    value = Column(
        String(500), nullable=True, comment="Configuration value (assignment ID)"
    )
    description = Column(
        String(500), nullable=True, comment="Description of this config key"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    def __repr__(self):
        return f"<DemoConfig {self.key}={self.value}>"
