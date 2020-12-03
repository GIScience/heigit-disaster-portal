# Import all the models, so that BaseTable has them before being
# imported by Alembic
from app.models import User, Provider, DisasterType, DisasterSubType # noqa
from .base import BaseTable  # noqa
