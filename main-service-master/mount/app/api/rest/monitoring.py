import prometheus_client as prometheus

from fastapi import APIRouter, Depends
from starlette.responses import Response

# from app.adapters import health
from app.common import logger

router = APIRouter()


# @router.route('/health')
# async def health_check(request):
#     db = request.state.db
#     statuses = [
#         await health.db_health_check(db.read_connection),
#         await health.db_health_check(db.write_connection)
#     ]

#     successes = map(lambda x: x.is_healthy, statuses)
#     resp = dict(map(lambda x: (x.name, x.msg), statuses))

#     if all(successes):
#         return responses.success(resp)
#     else:
#         return responses.failure(resp, status_code=500)


@router.get('/metrics')
def metrics():
    logger.info('prometheus stats')
    return Response(
        prometheus.generate_latest(),
        media_type=prometheus.CONTENT_TYPE_LATEST,
    )
