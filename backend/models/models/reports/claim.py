"""Claims module with mixin that provides a generic association
using a single target table and a single association table,
referred to by all parent tables.  The association table
contains a "discriminator" column which determines what type of
parent object associates to each particular row in the association
table.

SQLAlchemy's single-table-inheritance feature is used to target
different association types.
"""
from datetime import datetime as dt

from sqlalchemy import (Column, DateTime, ForeignKey, ForeignKeyConstraint,
                        String, Text)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref, relationship

from ...core import PkModel, SoftDelete
from ..user import HasUploader
from .submit import NeedsApprove


class Claim(NeedsApprove, HasUploader, PkModel):
    """The Claim model represents an user’s claim regarding a resource
    which should be processed by administrators.

    Claims can be manually generated by the users comunity if they suspect
    a resource may be falsified or incorrect.

    **Properties**:
    """
    #: (Text) Information created by user to describe the issue
    message = Column(Text, nullable=False)

    #: (Resource) Resource the claim is linked to
    resource = NotImplementedError()  # Implemented at NeedsApprove

    #: (String) Refers to the type report
    resource_type = Column(String, nullable=False)

    #: (Read_only) Resource unique identification
    resource_id = association_proxy("resource", "id")

    #: (Read_only) Upload datetime of the model instance
    # upload_datetime = association_proxy("resource", "upload_datetime")
    upload_datetime = Column(DateTime, nullable=False, default=dt.now)

    # Polymorphism related to the resource the claim is linked
    __mapper_args__ = {
        'polymorphic_on': resource_type,
        # 'with_polymorphic': '*'
    }

    __table_args__ = (
        ForeignKeyConstraint(['uploader_iss', 'uploader_sub'],
                             ['user.iss', 'user.sub']),
    )

    def __init__(self, **properties):
        """Model initialization"""
        super().__init__(**properties)

    def __repr__(self):
        """Human-readable representation string"""
        return "{}({}): {}".format(
            self.__class__.__name__,
            self.resource_type,
            self.message
        )

    def delete(self):
        """Deletes the claim report and restores the resource."""
        if self.resource.claims == []:
            self.resource.undelete()
        return super().delete()


class HasClaims(SoftDelete):
    """Provides the model the capability to perform claims.
    """
    __abstract__ = True

    @declared_attr
    def _claim_report_id(cls):
        return Column(ForeignKey('claim.id'))

    @declared_attr
    def _claim_report_class(cls):
        return type(
            f"{cls.__name__}ClaimReport", (Claim,),
            dict(
                __mapper_args__={
                    'polymorphic_identity': cls.__name__.lower(),
                    'polymorphic_load': 'inline'
                },
            ),
        )

    @declared_attr
    def claims(cls):
        """([Report]) Claim report related to the model instance"""
        return relationship(
            cls._claim_report_class,
            backref=backref("resource", uselist=False),
        )

    def claim(self, claimer, message):
        """Creates a pending claim related to the resource and soft
        deletes the resource.

        :param claimer: Message to include in the claim
        :type claimer: models.User 
        :param message: Message to include in the claim
        :type message: str
        """
        self.delete()
        return self.__class__._claim_report_class(
            uploader=claimer,
            message=message,
            resource=self
        )
