import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID, uuid4
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from common.database import Database
from common.web import configure, logger

db = Database('activities')


@asynccontextmanager
async def lifespan(app):
    db.initialize('''CREATE TABLE IF NOT EXISTS activities (
        id TEXT PRIMARY KEY, field_id TEXT NOT NULL, kind TEXT NOT NULL,
        due_date TEXT NOT NULL, notes TEXT NOT NULL, status TEXT NOT NULL,
        created_at TEXT NOT NULL, completed_at TEXT)''')
    yield


app = FastAPI(title='FarmTrack Activity API', version='1.0.0', lifespan=lifespan)
configure(app, db, 'activities')


class ActivityInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    field_id: UUID
    kind: Literal['watering', 'fertilizing', 'harvesting']
    due_date: date
    notes: str = Field(default='', max_length=500)


class ActivityUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['completed']


@app.get('/api/activities')
def list_activities(field_id: UUID | None = None):
    if field_id:
        return db.query('SELECT * FROM activities WHERE field_id = ? ORDER BY due_date, created_at',
                        (str(field_id),))
    return db.query('SELECT * FROM activities ORDER BY due_date, created_at')


@app.post('/api/activities', status_code=201)
def create_activity(activity: ActivityInput):
    base = os.getenv('FIELD_SERVICE_URL', 'http://field-service:8000')
    try:
        response = httpx.get(f'{base}/api/fields/{activity.field_id}', timeout=3, trust_env=False)
    except httpx.RequestError:
        raise HTTPException(503, 'Cannot validate field: Field service unavailable')
    logger.info('event=field_validation field_id=%s upstream_status=%s', activity.field_id, response.status_code)
    if response.status_code == 404:
        raise HTTPException(404, 'Field not found; activity was not created')
    if response.status_code != 200:
        raise HTTPException(503, 'Cannot validate field: Field service unavailable')
    identifier = str(uuid4())
    db.query('INSERT INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (identifier, str(activity.field_id), activity.kind, activity.due_date.isoformat(),
         activity.notes, 'pending', datetime.now(timezone.utc).isoformat(), None))
    return db.query('SELECT * FROM activities WHERE id = ?', (identifier,), one=True)


@app.patch('/api/activities/{activity_id}')
def complete_activity(activity_id: UUID, update: ActivityUpdate):
    # COALESCE preserves the first completion time if the request is repeated.
    result = db.query('''UPDATE activities SET status = ?,
        completed_at = COALESCE(completed_at, ?) WHERE id = ? RETURNING *''',
        (update.status, datetime.now(timezone.utc).isoformat(), str(activity_id)), one=True)
    if not result:
        raise HTTPException(404, 'Activity not found')
    return result
