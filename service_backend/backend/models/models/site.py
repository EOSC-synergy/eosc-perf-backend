"""Sites module."""
from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship

from ..core import PkModel
from . import HasCreationDate
from .report import HasReports
from .user import HasCreationUser


class Site(HasReports, HasCreationDate, HasCreationUser, PkModel):
    """The Site model represents a location where a benchmark can be executed.

    This generally refers to the different virtual machine providers and
    should include a human readable name and physical location.
    """
    #: (Text, required) Human readable institution identification
    name = Column(Text, unique=True, nullable=False)

    #: (Text, required) Place where a site is physically located
    address = Column(Text, nullable=False)

    #: (Text) Useful site information to help users
    description = Column(Text, nullable=True, default="")

    #: ([Flavor], read_only) List of flavors available at the site
    flavors = relationship("Flavor", cascade="all, delete-orphan")

    def __init__(self, **properties):
        """Model initialization"""
        super().__init__(**properties)

    def __repr__(self) -> str:
        """Human-readable representation string"""
        return "<{} {}>".format(self.__class__.__name__, self.name)
