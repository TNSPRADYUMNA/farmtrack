import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from common.database import Database
from common.web import configure

db = Database('fields')


@asynccontextmanager
async def lifespan(app):
    db.initialize('''CREATE TABLE IF NOT EXISTS fields (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, area_hectares REAL NOT NULL,
        crop TEXT NOT NULL, created_at TEXT NOT NULL)''')
    yield


app = FastAPI(title='FarmTrack Field API', version='1.0.0', lifespan=lifespan)
configure(app, db, 'fields')


class FieldInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name: str = Field(min_length=1, max_length=80)
    area_hectares: float = Field(gt=0, le=1000000, allow_inf_nan=False)
    crop: str = Field(min_length=1, max_length=80)


@app.get('/api/fields')
def list_fields():
    return db.query('SELECT * FROM fields ORDER BY created_at DESC')


@app.post('/api/fields', status_code=201)
def create_field(field: FieldInput):
    identifier = str(uuid4())
    db.query('INSERT INTO fields VALUES (?, ?, ?, ?, ?)',
             (identifier, field.name, field.area_hectares, field.crop,
              datetime.now(timezone.utc).isoformat()))
    return db.query('SELECT * FROM fields WHERE id = ?', (identifier,), one=True)


@app.get('/api/fields/{field_id}')
def get_field(field_id: UUID):
    field = db.query('SELECT * FROM fields WHERE id = ?', (str(field_id),), one=True)
    if not field:
        raise HTTPException(404, 'Field not found')
    return field


# A small backend-for-frontend proxy gives the browser a single origin.
# Only these fixed routes can be proxied; users cannot choose an upstream URL.
async def forward(request, suffix=''):
    base = os.getenv('ACTIVITY_SERVICE_URL', 'http://activity-service:8000')
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            result = await client.request(request.method, f'{base}/api/activities{suffix}',
                params=request.query_params, content=await request.body(),
                headers={'Content-Type': 'application/json'})
    except httpx.RequestError:
        raise HTTPException(503, 'Activity service unavailable. Please try again.')
    return Response(result.content, status_code=result.status_code,
                    media_type='application/json')


@app.api_route('/api/activities', methods=['GET', 'POST'], include_in_schema=False)
async def activities_proxy(request: Request):
    return await forward(request)


@app.patch('/api/activities/{activity_id}', include_in_schema=False)
async def activity_proxy(activity_id: UUID, request: Request):
    return await forward(request, '/' + str(activity_id))


app.mount('/', StaticFiles(directory=Path(__file__).parent / 'static', html=True), name='ui')
