"""
Nothing to do here yet
If we have to initialize the database with users or datasets we can do this here
"""
# TODO:
# add Users: Oscar User
# add Providers: Oscar Provider(from oscar user)
# add disaster subtypes
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import settings
from app.db import import_models  # noqa: F401


# make sure all SQL Alchemy models are imported (app.db.import_models) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
# from app.db.base import BaseTable


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # BaseTable.metadata.create_all(bind=engine)

    admin = crud.user.get_by_email(db, email=settings.ADMIN_USER)
    if not admin:
        user_in = schemas.UserCreateOut(
            email=settings.ADMIN_USER,
            secret=settings.ADMIN_USER_SECRET,
            is_admin=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841

    # see https://emergency.copernicus.eu/mapping/ems/domains#_ftnref1
    d_types = [
        dict({
            "earthquake": "Earthquake info",
            "sub_types": [
                {"ground_shaking": "Ground shaking info"},
                {"tsunami": "Tsunami info"}
            ]
        }),
        {
            "volcanic_activity": "Volcanic activity info",
            "sub_types": [
                {"ash_fall": "Ash fall info"},
                {"lahar": "Lahar info"},
                {"pyroclastic_flow": "Pyroclastic flow info"},
                {"lava_flow": "Lava flow info"}
            ]
        },
        {
            "storm": "Storm info",
            "sub_types": [
                {"extra_tropical_storm": "Extra-tropical storm info"},
                {"tropical_cyclone": "Tropical cyclone info"},
                {"connective_storm": "Connective storm info"}
            ]
        },
        {
            "extreme_temperature": "Extreme temperature info",
            "sub_types": [
                {"cold_wave": "Cold wave info"},
                {"heat_wave": "Heat wave info"},
                {"severe_winter_conditions": "Severe winter conditions info"}
            ]
        },
        {
            "flood": "Flood info",
            "sub_types": [
                {"coastal_flood": "coastal_flood info"},
                {"riverine_flood": "riverine_flood info"},
                {"flash_flood": "flash_flood info"},
                {"ice_jam_flood": "ice_jam_flood info"}
            ]
        },
        {
            "mass_movement": "mass_movement info",
            "sub_types": [
                {"landslide": "landslide info"},
                {"avalanche": "avalanche info"},
                {"subsidence": "subsidence info"},
                {"rock_fall": "Rock or debris fall"},
                {"mudflow": "mudflow info"},
            ]
        },
        {
            "drought": "drought info",
            "sub_types": [
                {"drought": "drought info"}
            ]
        },
        {
            "wildfire": "wildfire info",
            "sub_types": [
                {"forest_fire": "forest_fire info"},
                {"land_fire": "Bush, brush or Pasture fire"},
                {"urban_fire": "urban_fire info"}
            ]
        },
        {
            "epidemic": "epidemic info",
            "sub_types": [
                {"viral_disease": "viral_disease info"},
                {"bacterial_disease": "bacterial_disease info"},
                {"parasitic_disease": "parasitic_disease info"},
                {"fungal_disease": "fungal_disease info"},
                {"prion_disease": "prion_disease info"}
            ]
        },
        {
            "infestation": "infestation info",
            "sub_types": [
                {"grasshopper": "grasshopper info"},
                {"locust": "locust info"},
                {"pathogen": "pathogen info"}
            ]
        },
        {
            "industrial_accident": "industrial_accident info",
            "sub_types": [
                {"chemical_spill": "chemical_spill info"},
                {"collapse": "collapse info"},
                {"explosion": "explosion info"},
                {"fire": "fire info"},
                {"gas_leak": "gas_leak info"},
                {"poisoning": "poisoning info"},
                {"radiation": "radiation info"}
            ]
        },
        {
            "transport_accident": "transport_accident info",
            "sub_types": [
                {"air": "air info"},
                {"road": "road info"},
                {"rail": "rail info"},
                {"water": "water info"}
            ]
        },
        {
            "humanitarian": "humanitarian info",
            "sub_types": [
                {"conflict": "conflict info"},
                {"population_displacement": "Internally displaced persons"},
                {"rail": "rail info"},
                {"water": "water info"}
            ]
        },
        {
            "other": "other info",
            "sub_types": [
                {"other": "other info"}
            ]
        }
    ]
    d_types = [dict(x) for x in d_types]
    for d_type in d_types:
        name = list(d_type.keys())[0]
        db_entry = crud.disaster_type.get_by_name(db=db, name=name)
        if not db_entry:
            info = d_type[name]
            d_type_obj = schemas.DisasterTypeCreate(
                name=name,
                description=info
            )
            db_entry = crud.disaster_type.create(db=db, obj_in=d_type_obj)

        # TODO: generate Sub types


if __name__ == '__main__':
    import logging
    from app.db.session import SessionLocal, engine

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Creating initial data")
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")
