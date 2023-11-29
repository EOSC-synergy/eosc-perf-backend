"""Routes for results.

Results URL routes. Collection of controller methods to create and
operate existing benchmark results on the database.
"""
import datetime as dt

import pytz
from flask_smorest import Blueprint, abort
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from .. import models, notifications
from ..extensions import db, flaat
from ..schemas import args, schemas
from ..utils import filters, queries

blp = Blueprint(
    'results', __name__, description='Operations on results'
)

collection_url = ""
resource_url = "/<uuid:result_id>"


@blp.route(collection_url, methods=["GET"])
@blp.doc(operationId='ListResults')
@blp.arguments(args.ResultFilter, location='query')
@blp.response(200, schemas.Results)
@queries.to_pagination()
@queries.add_sorting(models.Result)
@queries.add_datefilter(models.Result)
def list(*args, **kwargs):
    """(Public) Filter and list results.

    Use this method to get a list of results filtered according to your
    requirements. The response returns a pagination object with the
    filtered results (if succeeds).

    This method allows to return results filtered by values inside the
    result. The filter is composed by 3 arguments separated by spaces
    ('%20' on URL-encoding): <path.separated.by.dots> <operator> <value>

    There are five filter operators:

     - **Equals (==)**: Return results where path value is exact to the
       query value. For example *filters=cpu.count == 5*
     - **Greater than (>)**: Return results where path value strictly
       greater than the query value. For example *filters=cpu.count > 5*
     - **Less than (<)**: Return results where path value strictly lower
       than the query value. For example *filters=cpu.count < 5*
     - **Greater or equal (>=)**: Return results where path value is equal
       or greater than the query value. For example *filters=cpu.count >= 5*
     - **Less or equal (<=)**: Return results where path value is equal or
       lower than the query value. For example *filters=cpu.count <= 5*

    Note that in the provided examples the filter is not URL-encoded as
    most libraries do it automatically, however there might be exception.
    In such cases, use the url encoding guide at:
    https://datatracker.ietf.org/doc/html/rfc3986#section-2.1
    """
    return __list(*args, **kwargs)


def __list(query_args):
    """Return a list of filtered results.

    Note the URL-encoding is only needed when accessing the function as
    HTTP request. The python call handles the filters only as strings.

    :param query_args: The request query arguments as python dictionary
    :type query_args: dict
    :raises UnprocessableEntity: Wrong query/body parameters
    :return: Pagination object with filtered results
    :rtype: :class:`flask_sqlalchemy.Pagination`
    """
    query = models.Result.query  # Create the base query

    # Extend query with tags
    for tags_ids in query_args.pop('tags_ids', []):
        query = query.filter(models.Result.tags_ids.in_([tags_ids]))

    # Extend query with execution times
    before = query_args.pop('execution_before', None)
    if before:
        query = query.filter(models.Result.execution_datetime < before)

    after = query_args.pop('execution_after', None)
    if after:
        query = query.filter(models.Result.execution_datetime > after)

    # Extend query with filters
    parsed_filters = []
    for filter in query_args.pop('filters'):
        try:
            new_filter = filters.new_filter(models.Result, filter)
            parsed_filters.append(new_filter)
        except ValueError as err:
            abort(422, messages={
                'filter': filter, 'reason': err.args,
                'hint': "Probably missing spaces (%20)",
                'example': "filters=machine.cpu.count%20%3E%205"
            })
        except KeyError as err:
            abort(422, message={
                'filter': filter, 'reason': err.args,
                'hint': "Use only one of ['==', '>', '<', '>=', '<=']",
                'example': "filters=machine.cpu.count%20%3E%205"
            })
    query = query.filter(and_(True, *parsed_filters))

    # Model filter with remaining standard parameters
    return query.filter_by(**query_args)


@blp.route(collection_url, methods=["POST"])
@blp.doc(operationId='CreateResult')
@flaat.access_level("user")
@flaat.inject_user_infos()
@blp.arguments(args.ResultContext, location='query')
@blp.arguments(schemas.Json)
@blp.response(201, schemas.Result)
def create(*args, **kwargs):
    """(Users) Upload a new result.

    Use this method to create a new result in the database so it can
    be accessed by the application users. The method returns the complete
    created result (if succeeds).

    The uploaded result must pass the benchmark JSON Schema to be
    accepted, otherwise 422 UnprocessableEntity is produced.
    In addition, an execution_datetime must be provided in order to indicate
    the time when the benchmark was executed. It should be in ISO8601
    format and include the timezone.
    """
    return __create(*args, **kwargs)


def __create(query_args, body_args, user_infos):
    """Create a new result in the database.

    :param query_args: The request query arguments as python dictionary
    :type query_args: dic
    :param body_args: The request body arguments as python dictionary
    :type body_args: dict
    :raises Unauthorized: The server could not verify the user identity
    :raises Forbidden: The user is not registered
    :raises NotFound: One or more query items do not exist in the database
    :raises UnprocessableEntity: Wrong query/body parameters
    :raises Conflict: Created object conflicts a database item
    :return: The result created into the database.
    :rtype: :class:`models.Result`
    """
    if query_args['execution_datetime'].tzinfo is None:
        error_msg = "Execution date must include timezone"
        abort(422, messages={'error': error_msg})
    if query_args['execution_datetime'] > dt.datetime.now(pytz.utc):
        error_msg = "Execution date cannot be in future"
        abort(422, messages={'error': error_msg})

    def get(model, result_id):
        item = model.read(result_id)
        if item is None:
            err_msg = f"{item.__class__.__name__} {result_id} not in database"
            abort(404, messages={'error': err_msg})
        elif hasattr(item, "status") and item.status.name != "approved":
            err_msg = f"{item.__class__.__name__} {result_id} not approved"
            abort(422, messages={'error': err_msg})
        else:
            return item

    result = models.Result.create(dict(
        benchmark=get(models.Benchmark, query_args.pop('benchmark_id')),
        flavor=get(models.Flavor, query_args.pop('flavor_id')),
        tags=[get(models.Tag, id) for id in query_args.pop('tags_ids')],
        uploader=models.User.read((user_infos.subject, user_infos.issuer)),
        json=body_args, **query_args
    ))

    try:  # Transaction execution
        db.session.commit()
    except IntegrityError:
        error_msg = "Integrity error"
        abort(409, messages={'error': error_msg})

    return result


@blp.route(collection_url + ':search', methods=["GET"])
@blp.doc(operationId='SearchResults')
@blp.arguments(args.ResultSearch, location='query')
@blp.response(200, schemas.Results)
@queries.to_pagination()
@queries.add_sorting(models.Result)
@queries.add_datefilter(models.Result)
def search(*args, **kwargs):
    """(Public) Filter and list results.

    Use this method to get a list of results based on a general search
    of terms. For example, calling this method with terms=v1&terms=0
    returns all results with 'v1' and '0' on the 'docker_image',
    'docker_tag', 'site_name', 'flavor_name' fields or 'tags'.
    The response returns a pagination object with the filtered results
    (if succeeds).
    """
    return __search(*args, **kwargs)


def __search(query_args):
    """Filter and list results using generic terms.

    :param query_args: The request query arguments as python dictionary
    :type query_args: dict
    :raises UnprocessableEntity: Wrong query/body parameters
    :return: Pagination object with filtered results
    :rtype: :class:`flask_sqlalchemy.Pagination`
    """
    search = models.Result.query
    for keyword in query_args.pop('terms'):
        search = search.filter(
            or_(
                models.Result.benchmark_name.contains(keyword),
                models.Result.site_name.contains(keyword),
                models.Result.site_address.contains(keyword),
                models.Result.flavor_name.contains(keyword),
                models.Result.tags_names == keyword
            ))

    # Model filter with remaining standard parameters
    return search.filter_by(**query_args)


@blp.route(resource_url, methods=["GET"])
@blp.doc(operationId='GetResult')
@blp.response(200, schemas.Result)
def get(*args, **kwargs):
    """(Public) Retrieve result details.

    Use this method to retrieve a specific result from the database.
    """
    return __get(*args, **kwargs)


def __get(result_id):
    """Return the id matching result.

    If no result exists with the indicated id, then 404 NotFound
    exception is raised.

    :param result_id: The id of the result to retrieve
    :type result_id: uuid
    :raises NotFound: No result with id found
    :return: The database result using the described id
    :rtype: :class:`models.Result`
    """
    result = models.Result.read(result_id, with_deleted=True)
    if result is None:
        error_msg = f"Result {result_id} not found in the database"
        abort(404, messages={'error': error_msg})
    else:
        return result


@blp.route(resource_url, methods=["DELETE"])
@blp.doc(operationId='DeleteResult')
@flaat.access_level("admin")
@blp.response(204)
def delete(*args, **kwargs):
    """(Admin) Delete an existing result.

    Use this method to delete a specific result from the database.
    """
    return __delete(*args, **kwargs)


def __delete(result_id):
    """Delete the id matching result.

    If no result exists with the indicated id, then 404 NotFound
    exception is raised.

    :param result_id: The id of the result to delete
    :type result_id: uuid
    :raises Unauthorized: The server could not verify the user identity
    :raises Forbidden: The user has not the required privileges
    :raises NotFound: No result with id found
    """
    result = __get(result_id)
    result.delete()

    try:  # Transaction execution
        db.session.commit()
    except IntegrityError:
        error_msg = f"Conflict deleting {result_id}"
        abort(409, messages={'error': error_msg})


@blp.route(resource_url + ":claim", methods=["POST"])
@blp.doc(operationId='ClaimReport')
@flaat.access_level("user")
@flaat.inject_user_infos()
@blp.arguments(schemas.CreateClaim)
@blp.response(201, schemas.Claim)
def claim(*args, **kwargs):
    """(Users) Report a result.

    Use this method to create a report for a specific result so the
    administrators are aware of issues. The reported result is hidden
    from generic responses until the issue is corrected and approved
    by the administrators.
    """
    return __claim(*args, **kwargs)


def __claim(body_args, result_id, user_infos):
    """Create a claim linked to the report.

    If no result exists with the indicated id, then 404 NotFound
    exception is raised.

    :param result_id: The id of the result created by the returned user
    :type result_id: uuid
    :raises Unauthorized: The server could not verify the user identity
    :raises Forbidden: The user is not registered
    :raises NotFound: No result with id found
    :raises UnprocessableEntity: Wrong query/body parameters
    """
    result = __get(result_id)
    claim = result.claim(
        claimer=models.User.read((user_infos.subject, user_infos.issuer)),
        message=body_args['message']
    )

    try:  # Transaction execution
        db.session.commit()
    except IntegrityError:
        error_msg = f"Conflict updating {result_id}"
        abort(409, messages={'error': error_msg})

    notifications.result_claimed(result, claim)
    return claim


@blp.route(resource_url + '/tags', methods=["PUT"])
@blp.doc(operationId='UpdateResult')
@flaat.access_level("user")
@flaat.inject_user_infos()
@blp.arguments(schemas.TagsIds)
@blp.response(204)
def update_tags(*args, **kwargs):
    """(Owner or Admin) Update an existing result tags.

    Use this method to update tags on a specific result from the database.
    """
    return __update_tags(*args, **kwargs)


def __update_tags(body_args, result_id, user_infos):
    """Update a result specific fields.

    If no result exists with the indicated id, then 404 NotFound
    exception is raised.

    :param body_args: The request body arguments as python dictionary
    :type body_args: dict
    :param result_id: The id of the result to update
    :type result_id: uuid
    :raises Unauthorized: The server could not verify the user identity
    :raises Forbidden: The user has not the required privileges
    :raises NotFound: No result with id found
    :raises UnprocessableEntity: Wrong query/body parameters
    """
    result = __get(result_id)

    if 'tags_ids' in body_args:
        tags_ids = body_args.pop('tags_ids')
        body_args['tags'] = [models.Tag.read(id) for id in tags_ids]

    subiss = user_infos.subject, user_infos.issuer
    is_admin = flaat.access_levels[1].requirement.func(user_infos)
    is_owner = subiss == (result.uploader.sub, result.uploader.iss)
    if is_admin or is_owner:
        result.update(body_args)
    else:
        abort(403)

    try:  # Transaction execution
        db.session.commit()
    except IntegrityError:
        error_msg = f"Conflict updating {result_id}"
        abort(409, messages={'error': error_msg})


@blp.route(resource_url + "/claims", methods=["GET"])
@blp.doc(operationId='ListResultClaims')
@flaat.access_level("user")
@flaat.inject_user_infos()
@blp.arguments(args.ClaimFilter, location='query')
@blp.response(200, schemas.Claims)
@queries.to_pagination()
@queries.add_sorting(models.Claim)
@queries.add_datefilter(models.Claim)
def list_claims(*args, **kwargs):
    """(Owner or Admins) Returns the result claims.

    Use this method to retrieve all the result claims.
    """
    return __list_claims(*args, **kwargs)


def __list_claims(query_args, result_id, user_infos):
    """Return the result claims filtered by the query args.

    :param query_args: The request query arguments as python dictionary
    :type query_args: dict
    :param result_id: The id of the result from to collect the claims
    :type result_id: uuid
    :raises Unauthorized: The server could not verify your identity
    :raises Forbidden: You don't have the administrator rights
    """
    result = __get(result_id)

    subiss = user_infos.subject, user_infos.issuer
    is_admin = flaat.access_levels[1].requirement.func(user_infos)
    is_owner = subiss == (result.uploader.sub, result.uploader.iss)
    if is_admin or is_owner:
        pass
    else:
        abort(403)

    query = models.Result._claim_report_class.query
    return query.filter_by(resource_id=result_id, **query_args)


@blp.route(resource_url + "/uploader", methods=["GET"])
@blp.doc(operationId='ResultUploader')
@flaat.access_level("admin")
@blp.response(200, schemas.User)
def get_uploader(*args, **kwargs):
    """(Admins) Retrieve result uploader.

    Use this method to retrieve the uploader of a specific result
    from the database.
    """
    return __get_uploader(*args, **kwargs)


def __get_uploader(result_id):
    """Return the uploader of the id matching result.

    If no result exists with the indicated id, then 404 NotFound
    exception is raised.

    :param result_id: The id of the result created by the returned user
    :type result_id: uuid
    :raises Unauthorized: The server could not verify the user identity
    :raises Forbidden: The user has not the required privileges
    :raises NotFound: No result with id found
    """
    return __get(result_id).uploader
