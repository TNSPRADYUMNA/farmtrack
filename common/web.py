import logging
import time
from uuid import uuid4
from fastapi import HTTPException, Request

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('farmtrack')


def configure(app, db, service):
    @app.middleware('http')
    async def access_log(request: Request, call_next):
        request_id = str(uuid4())
        start = time.monotonic()
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        logger.info('service=%s method=%s path=%s status=%s duration_ms=%.1f request_id=%s',
                    service, request.method, request.url.path, response.status_code,
                    (time.monotonic() - start) * 1000, request_id)
        return response

    @app.get('/health/live', include_in_schema=False)
    def live():
        return {'status': 'ok', 'service': service}

    @app.get('/health/ready', include_in_schema=False)
    def ready():
        try:
            db.query('SELECT 1')
        except Exception:
            raise HTTPException(503, 'Database unavailable')
        return {'status': 'ready', 'service': service}
