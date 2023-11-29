"""Schemas module for schemas definition."""
from marshmallow import INCLUDE, post_dump
from marshmallow.validate import OneOf

from . import BaseSchema as Schema
from . import Id, Pagination, UploadDatetime, fields


# ---------------------------------------------------------------------
# Definition of User schemas
class User(Schema):
    """User schema definition."""

    #: (Text, required, dump_only):
    #: Primary key containing the OIDC subject the model instance
    sub = fields.String(
        description="String containing an OIDC subject",
        example="NzbLsXh8uDCcd-6MNwXF4W_7noWXFZAfHkxZsRGC9Xs",
        required=True,
    )

    #: (Text, required, dump_only):
    #: Primary key containing the OIDC issuer of the model instance
    iss = fields.String(
        description="String containing an OIDC issuer",
        example="https://self-issued.me", required=True,

    )

    #: (Email, required):
    #: Electronic mail collected from OIDC access token
    email = fields.String(
        description="Email of user collected by the OIDC token",
        example="simple_email@gmail.com", required=True
    )

    #: (Email) Electronic mail collected from OIDC access token
    registration_datetime = fields.DateTime(
        description="Time when the user was registered",
        example="2021-09-11 10:16:11.732268", required=True
    )


class Users(Pagination, Schema):
    """Users pagination schema definition."""

    #: ([User], required):
    #: List of site items for the pagination object
    items = fields.Nested(User, required=True, many=True)


# ---------------------------------------------------------------------
# Definition of Report schemas

class Submit(UploadDatetime, Schema):
    """Submit schema definition."""

    #: (String, required):
    #: Resource discriminator
    resource_type = fields.String(
        description="Resource type discriminator",
        example="benchmark", required=True,
        validate=OneOf(["benchmark", "claim", "site", "flavor"])
    )

    #: (UUID, required):
    #: Resource unique identification
    resource_id = fields.UUID(
        description="UUID resource unique identification",
        example="b491d3ee-064d-48a2-9547-0c4c636466db",
        required=True
    )

    #: (User, required):
    #: Resource uploader/creator
    uploader = fields.Nested(
        User, attribute="resource.uploader",
        required=True, dump_only=True,
    )

    @post_dump
    def aggregate_claims(self, data, **kwargs):
        """Aggregate claims to the submit report."""
        data = super().remove_skip_values(data, **kwargs)
        if 'resource_type' in data:
            if "claim" in data['resource_type']:
                data['resource_type'] = "claim"
        return data


class Submits(Pagination, Schema):
    """Submits pagination schema definition."""

    #: ([Submit], required):
    #: List of submit items for the pagination object
    items = fields.Nested(Submit, required=True, many=True)


class CreateClaim(Schema):
    """Claim creation schema definition."""

    #: (String, required):
    #: Claim text describing the resource issue
    message = fields.String(
        description="Resource type discriminator",
        example="The resource uses negative time", required=True
    )


class Claim(Id, UploadDatetime, CreateClaim):
    """Claim schema definition."""

    #: (UUID, required):
    #: Resource unique identification
    resource_type = fields.String(
        description="Resource type discriminator",
        example="result", required=True,
        validate=OneOf(["result"]),
    )

    #: (UUID, required):
    #: Resource unique identification
    resource_id = fields.UUID(
        description="UUID resource unique identification",
        example="3ddd146f-c2c6-487e-ac40-df1dbb971b2c",
        required=True, dump_only=True,
    )

    #: (User, required):
    #: Claim uploader/creator
    uploader = fields.Nested(User, required=True, dump_only=True)


class Claims(Pagination, Schema):
    """Claims pagination schema definition."""

    #: ([Claim], required):
    #: List of claim items for the pagination object
    items = fields.Nested(Claim, required=True, many=True)


# ---------------------------------------------------------------------
# Definition of Tag schemas

class CreateTag(Schema):
    """Tag creation schema definition."""

    #: (Text, required):
    #: Human readable feature identification
    name = fields.String(
        description="String with short feature identification",
        example="python", required=True
    )

    #: (Text):
    #: Useful information to help users to understand the label context
    description = fields.String(
        description="String with an statement about the object",
        example="This is a simple description example",
    )


class Tag(Id, CreateTag):
    """Tag schema definition."""


class Tags(Pagination, Schema):
    """Tags pagination schema definition."""

    #: ([Tag], required):
    #: List of tag items for the pagination object
    items = fields.Nested(Tag, required=True, many=True)


class TagsIds(Schema):
    """Tags Ids schema definition."""

    #: ([UUID]):
    #: List of tag ids
    tags_ids = fields.List(fields.UUID)


# ---------------------------------------------------------------------
# Definition of benchmark schemas

class CreateBenchmark(Schema):
    """Benchmark creation schema definition."""

    #: (Text, required):
    #: Docker image referenced by the benchmark
    docker_image = fields.String(
        description="String with a docker hub container name",
        example="deephdc/deep-oc-benchmarks_cnn", required=True,
    )

    #: (Text, required):
    #: Docker image version/tag referenced by the benchmark
    docker_tag = fields.String(
        description="String with a docker hub container tag",
        example="1.0.2-gpu", required=True,
    )

    #: (Text, required):
    #: URL to the benchmark container documentation
    url = fields.String(
        description="String with a docker hub container tag",
        example="https://hub.docker.com/r/deephdc/deep-oc-benchmarks_cnn",
        required=True,
    )

    #: (JSON, required):
    #: Schema used to validate benchmark results before upload
    json_schema = fields.Dict(
        # description="JSON Schema for result validation",
        required=True,
        example={
            "$id": "https://example.com/benchmark.schema.json",
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "type": "object",
            "properties": {
                "start_datetime": {
                    "description": "The benchmark start datetime.",
                    "type": "string",
                    "format": "date-time"
                },
                "end_datetime": {
                    "description": "The benchmark end datetime.",
                    "type": "string",
                    "format": "date-time"
                },
                "machine": {
                    "description": "Execution machine details.",
                    "type": "object",
                    "properties": {
                        "cpus": {
                            "description": "Number of CPU.",
                            "type": "integer"
                        },
                        "ram": {
                            "description": "Available RAM in MB.",
                            "type": "integer"
                        },
                    },
                    "required": ["cpus", "ram"]
                }
            },
            "required": ["start_datetime", "end_datetime", "machine"]
        }
    )

    #: (Text):
    #: Short text describing the main benchmark features
    description = fields.String(
        description="String with an statement about the object",
        example="This is a simple description example",
    )


class Benchmark(Id, UploadDatetime, CreateBenchmark):
    """Benchmark schema definition."""


class Benchmarks(Pagination, Schema):
    """Benchmarks pagination schema definition."""

    #: ([Benchmark], required):
    #: List of benchmark items for the pagination object
    items = fields.Nested("Benchmark", required=True, many=True)


# ---------------------------------------------------------------------
# Definition of Site schemas

class CreateSite(Schema):
    """Create site schema definition."""

    #: (Text, required):
    #: Human readable institution identification
    name = fields.String(
        description="String with human readable institution identification",
        example="Karlsruhe Institute of Technology", required=True,
    )

    #: (Text, required):
    #: Place where a site is physically located
    address = fields.String(
        description="String with place where a site is located",
        example="76131 Karlsruhe, Germany", required=True,
    )

    #: (Text, required):
    #: Useful site information to help users
    description = fields.String(
        description="String with an statement about the object",
        example="This is a simple description example",
    )


class Site(Id, UploadDatetime, CreateSite):
    """Site schema definition."""


class Sites(Pagination, Schema):
    """Sites pagination schema definition."""

    #: ([Site], required):
    #: List of site items for the pagination object
    items = fields.Nested(Site, required=True, many=True)


# ---------------------------------------------------------------------
# Definition of Flavor schemas

class CreateFlavor(Schema):
    """Create flavor schema definition."""

    #: (Text, required):
    #: Text with virtual hardware template identification
    name = fields.String(
        description="String with virtual hardware template identification",
        example="c6g.medium", required=True,
    )

    #: (Text, required):
    #: Text with useful information for users
    description = fields.String(
        description="String with an statement about the object",
        example="This is a simple description example",
    )


class Flavor(Id, UploadDatetime, CreateFlavor):
    """Flavor schema definition."""


class Flavors(Pagination, Schema):
    """Flavors pagination schema definition."""

    #: ([Flavor], required):
    #: List of flavor items for the pagination object
    items = fields.Nested(Flavor, required=True, many=True)


# ---------------------------------------------------------------------
# Definition of Result schemas

class Result(Id, UploadDatetime, Schema):
    """Result schema definition."""

    #: (ISO8601, required) :
    #: Benchmark execution **START**
    execution_datetime = fields.DateTime(
        description="START execution datetime of the result",
        example="2021-09-08 20:37:10.192459", required=True,
    )

    #: (Benchmark, required):
    #: Benchmark used to provide the results
    benchmark = fields.Nested("Benchmark", required=True)

    #: (Site, required):
    #: Site where the benchmark was executed
    site = fields.Nested("Site", required=True)

    #: (Flavor, required):
    #: Flavor used to executed the benchmark
    flavor = fields.Nested("Flavor", required=True)

    #: ([Tag], required):
    #: List of associated tags to the model
    tags = fields.Nested("Tag", many=True, required=True)

    #: (JSON, required):
    #: Benchmark execution results
    json = fields.Dict(required=True)


class Results(Pagination, Schema):
    """Results pagination schema definition."""""

    #: ([Result], required):
    #: List of results items for the pagination object
    items = fields.Nested(Result, required=True, many=True)


class Json(Schema):
    """Special schema to allow free JSON property."""

    class Meta:  # noqa: D106
        #: Accept and include the unknown fields
        unknown = INCLUDE
