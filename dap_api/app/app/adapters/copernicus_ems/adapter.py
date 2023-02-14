import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import List, Any, Union, Optional
import os
import feedparser
import requests
from fastapi import APIRouter, Query
from feedparser import FeedParserDict
from geoalchemy2 import func
# from tqdm import tqdm
from enum import Enum

from app import crud
from app.adapters.base import BaseAdapter, Singleton
from app.adapters.copernicus_ems.schemas import CopernicusActivation, ActivationAOI, ActivationStatus, EMSRProduct
from app.db.session import SessionLocal

from pydantic import BaseModel, HttpUrl

from app.schemas import DisasterAreaPropertiesCreate


def json_serial(obj):
    """JSON serializer for datetime objects, which are not serializable by default json code"""
    if isinstance(obj, datetime):
        return int(obj.timestamp())
    elif isinstance(obj, CopernicusActivation):
        return obj.dict()
    raise TypeError("Type %s not serializable" % type(obj))

# read from file?

# data in
# for feature in FC
# for poly in multipoly
# if raster polygon -> simplify polygon (which algo?) douglas-peucker either use ST_simplify or
# how to check for raster polygon:

# extract info
# save d_area
# output = List[DisasterArea]

# Adapter should output a List of disaster Areas adhering to the schema for disaster area creation in CRUD

# Error handling of adapter


def extract_int(string: str) -> int:
    return int("".join([c for c in string if c.isdigit()]))


def parse_file_name(file_name: List[str], old: bool = False):
    if not old:
        name, release, _, version, _ = file_name
    else:
        name, version, _ = file_name
        release = "1"

    monitoring = 0
    if name in ["MAP", "OVERVIEW", "PRODUCT"]:
        name = "Product"
    elif name.startswith("MONIT") or name.startswith("OVERVIEW-MONIT"):
        monitoring = extract_int(name)
        name = f"Product"
    elif name.startswith("DETAIL"):
        if len(name) == 8:
            name = f"Detail {name[-2:]}"
        else:
            detail, monit = name.split("-")
            name = f"Detail {detail[-2:]}"
            monitoring = extract_int(monit)
    elif name == 'S1DETAIL01':
        name = "Detail 01 (Sentinel)"
    elif name == 'S1OVERVIEW':
        name = "Product (Sentinel)"
    return name, monitoring, extract_int(release), extract_int(version)


def get_temporal_activation_info(a: dict):
    created = datetime(*a['published_parsed'][:6], tzinfo=timezone.utc)
    target_string = "<b>Date/Time of Event (UTC):</b> "
    event_datetime_str = a['summary'][a['summary'].index(target_string) + len(target_string):][:19]
    try:
        event_timestamp = datetime.strptime(f"{event_datetime_str}Z", "%Y-%m-%d %H:%M:%S%z")
    except ValueError:
        event_timestamp = created
        print(f"Event time for {a['id']} inferred from activation creation time.")
    return created, event_timestamp


def get_json_file(file_path: str) -> dict:
    if os.path.isfile(file_path):
        with open(file_path, 'r') as fp:
            content = json.load(fp)
        return content
    else:
        return dict()


@Singleton
class CopernicusAdapter(BaseAdapter):
    host_domain: HttpUrl = "https://emergency.copernicus.eu/"
    name: str = "CopernicusEMS"
    activations: dict = {}
    here = os.path.dirname(__file__)
    scrapes_path = here + "/data/scrapes"
    feeds_path = here + "/data/feeds"

    def __init__(self):
        print("Initializing Copernicus Adapter")
        super().__init__()

        # load existing activations
        if json_activations := get_json_file(f"{self.here}/activations.json"):
            for key, value in json_activations.items():
                self.activations[int(key)] = CopernicusActivation(**value)
            print("Activations loaded from file")
        #     TODO Update activations from remote like when updating normally
        else:
            # use feed to create activations
            if ems_feed := get_json_file(f'{self.here}/feed.json'):
                pass
            else:
                ems_feed = feedparser.parse('https://emergency.copernicus.eu/mapping/activations-rapid/feed/?limit=25')
            activations = ems_feed['entries']
            for a in activations:
                activation_scrape_path = f'{self.scrapes_path}/{a["id"]}.json'
                if product_urls := get_json_file(activation_scrape_path):
                    pass
                else:
                    product_urls = self.scrape_downloadable_delineation_products(a['id'])
                    with open(activation_scrape_path, 'w') as fp:
                        json.dump(product_urls, fp)
                if product_urls:
                    c_act = self.create_copernicus_activation(a, product_urls)
                    if c_act:
                        self.activations[extract_int(a['id'])] = c_act
                    else:
                        pass
                        # print(f"No suitable products in {a['id']}")  # TODO log this instead
                else:
                    pass
                    # print(f"No downloadable products for {a['id']}")  # TODO log this instead
            with open(f'{self.here}/activations.json', 'w') as ap:
                json.dump(self.activations, ap, default=json_serial)
                print("activations.json written")

        print("Finished initializing")

    def __call__(self):
        return self.instance()

    def create_copernicus_activation(self, a: dict, available_products: List[HttpUrl]):
        activation_feed_path = f'{self.here}/data/feeds/{a["id"]}.json'
        if act_feed := get_json_file(activation_feed_path):
            pass
        else:
            act_feed = feedparser.parse(a['iwgsem_activationrss'])
            with open(activation_feed_path, 'w') as fp:
                json.dump(act_feed, fp)

        content_hash = hashlib.md5(json.dumps(available_products).encode('utf-8')).hexdigest()
        aoi_ids = [aoi for aoi in set([p.split("_")[1] for p in available_products])]
        aois = []
        for n in aoi_ids:
            aoi_feed_entries = [e for e in act_feed["entries"] if n in e['gdacs_cemsaoi']]
            aoi_products = [p for p in available_products if n in p]
            aoi = self.create_activation_aoi(n, aoi_feed_entries, aoi_products)
            if aoi:
                aois.append(aoi)
        if aois:
            created, event_timestamp = get_temporal_activation_info(a)
            return CopernicusActivation(
                id=extract_int(a['id']),
                name=a['title'],
                status=a['iwgsem_activationstatus'],
                event_type=a['iwgsem_activationeventtype'],
                content_hash=content_hash,
                aois=aois,
                # description=a['iwgsem_activationdescription'][3:-4],
                description="",
                created=created,
                event_timestamp=event_timestamp
            )

    def create_activation_aoi(self, n: str, aoi_feed_entries: list,
                              available_products: list):  # TODO change to FeedParserDict type
        aoi_index = [k for (k, v) in enumerate(aoi_feed_entries) if v['tags'][0]['term'] == "AOI"][0]
        aoi_entry = aoi_feed_entries.pop(aoi_index)
        products = []
        for p in available_products:
            # only delineation products
            if any(sub in ["DEL", "01DELINEATION", "DELINEATION"] for sub in p.split("_")):
                # yes, of course, structure every f**** thing differently
                product_feed_entry = \
                    [x for x in aoi_feed_entries if p.split("/")[1].startswith(x["link"].split("/")[-2])][0]
                # and only Vector products no reference maps
                if any(sub in product_feed_entry["title"] for sub in ["Vector Package", "Delineation Map"]):
                    products.append(self.create_ems_product(p, product_feed_entry))
        if products:
            return ActivationAOI(
                id=extract_int(n),
                name=aoi_entry["title"].split("] ")[1],
                products=products
            )
        else:
            return None

    @staticmethod
    def create_ems_product(p: str, feed_entry: dict):
        download_id, file_name = p.split("/")
        name_parts = file_name.split("_")
        emsr_id = extract_int(name_parts.pop(0))
        # extract available AOI numbers for both old(pre EMSR252) "01LOCATION" and new format "AOI01"
        aoi = extract_int(name_parts.pop(0))
        name, monitoring, release, version = parse_file_name(name_parts[1:], old="DELINEATION" in p)
        status = feed_entry['tags'][0]['term'].split(": ")[1]
        if status == "Production finished, quality approved":
            status = "Quality approved"
        created = datetime(*feed_entry['published_parsed'][:6], tzinfo=timezone.utc)
        return EMSRProduct(
            name=name,
            monitoring=monitoring,
            release=release,
            version=version,
            status=status,
            download_id=int(download_id),
            created=created
        )

    @staticmethod
    def get_open_activations() -> list:
        feed = feedparser.parse('https://emergency.copernicus.eu/mapping/activations-rapid/feed/open')
        return [e.id for e in feed.entries]

    def get_activation(self, act_name: str) -> CopernicusActivation:
        try:
            act_id = extract_int(act_name)
        except ValueError:
            raise ValueError(f"No activation entry for {act_name}")
        if act_id in self.activations.keys():
            return self.activations[act_id]
        else:
            raise ValueError(f"No activation entry for EMSR{act_id:03}")

    def get_aois(self, act_name: str) -> list:
        try:
            activation = self.get_activation(act_name)
        except ValueError as e:
            return []
        return [aoi.name for aoi in activation.aois]

    @staticmethod
    def get_aoi(activation: CopernicusActivation, aoi_name: str) -> ActivationAOI:
        return next((aoi for aoi in activation.aois if aoi.name == aoi_name), None)

    @staticmethod
    def get_products(aoi: ActivationAOI) -> list:
        sorted_products = sorted(aoi.products, key=lambda x: x.monitoring, reverse=True)
        return [product_to_name(p) for p in sorted_products]

    @staticmethod
    def get_product(aoi: ActivationAOI, product_name: str) -> EMSRProduct | None:
        name_parts = product_name.split(" - ")
        if not name_parts:
            return None
        name = name_parts[0]
        monitoring = 0 if len(name_parts) == 1 else extract_int(name_parts[1])
        return next(
            iter([product for product in aoi.products if product.name == name and product.monitoring == monitoring]),
            None
        )

    def scrape_downloadable_delineation_products(self, ems_id: str) -> List[HttpUrl]:
        r = requests.get(f'{self.host_domain}/mapping/list-of-components/{ems_id}/DELINEATION/ALL')
        if r.status_code != 200:
            print(f"Request for {ems_id} not successful")
        return re.findall(r'href=[\'"]?/mapping/download/([0-9]+/[^\'" >]+)', r.text)

    # def _read_in_file(self) -> None:
    #     with open(self.file_path, 'r') as in_file:
    #         self.json_data = json.load(in_file)
    #         self.name = self.file_path.stem
    #
    # def _process_geometry(self):
    #     """
    #     default process for feature collections
    #     :return:
    #     """
    #     pass
    #
    # def _get_meta_information(self, props: dict) -> DisasterAreaPropertiesCreate:
    #     db = SessionLocal()
    #     # transform e.g. "5-Flood" -> "flood"
    #     d = props.get("event_type").split("-")[1].lower()
    #     # get
    #     d_type = crud.disaster_type.get_by_name(db=db, name=d)
    #     s = "_".join(props.get("obj_desc").lower().split(" "))
    #     ds_type = next((x for x in d_type.sub_types if x.name == s), None)
    #     db.close()
    #     return DisasterAreaPropertiesCreate(
    #         name=self.name,
    #         provider_id=2,
    #         d_type_id=d_type.id,
    #         ds_type_id=ds_type.id if ds_type else None
    #     )
    #
    # def _create_disaster_areas(self, simplify_percentage: int = 0):
    #     features = self.json_data.get("features")
    #     start = time()
    #     skipped = []
    #     self.times = dict({
    #         "simplify": 0,
    #         "make_valid": 0,
    #         "correct_collection": 0,
    #         "insert": 0
    #     })
    #     for i, f in enumerate(features, start=1):
    #         db = SessionLocal()
    #         props = self._get_meta_information(f.get("properties"))
    #         props.name = f"{props.name}-{i}"
    #         area = 0
    #         geom = func.ST_GeomFromGeoJSON(json.dumps(f.get("geometry")))
    #         if simplify_percentage:
    #             s_start = time()
    #             # get the best Projection for area calculation
    #             best_area_projection = db.execute(func._ST_BestSRID(geom)).scalar()
    #             # reproject
    #             transformed_geom = func.ST_Transform(geom, best_area_projection)
    #             # simplify using percentage of raster pixel size
    #             simple = func.ST_Simplify(transformed_geom, self.raster_size * (simplify_percentage / 100))
    #             # calculate area here to avoid re-projecting during db insertion
    #             area = round(db.execute(func.ST_Area(transformed_geom)).scalar(), 1)
    #             # skip area creation if there is no geometry left after simplification
    #             if not db.execute(func.ST_GeometryType(simple)).scalar():
    #                 skipped.append(i)
    #                 self.times["simplify"] += time() - s_start
    #                 db.close()
    #                 continue
    #             # transform back
    #             geom = func.ST_Transform(simple, 4326)
    #             self.times["simplify"] += time() - s_start
    #         m_start = time()
    #         # fix self intersection and other topology problems
    #         geom = func.ST_MakeValid(geom)
    #         self.times["make_valid"] += time() - m_start
    #         geom_type = db.execute(func.ST_GeometryType(geom)).scalar()
    #         if geom_type not in ["ST_GeometryCollection", "ST_MultiPolygon", "ST_Polygon"]:
    #             skipped.append(i)
    #             db.close()
    #             continue
    #         # treat GeometryCollections
    #         if geom_type == 'ST_GeometryCollection':
    #             c_start = time()
    #             # only use polygons
    #             geom = func.ST_CollectionExtract(geom, 3)
    #             self.times["correct_collection"] += time() - c_start
    #         # Geometry needs to be MultiPolygon for DB column
    #         geom = func.ST_Multi(geom)
    #         i_start = time()
    #         crud.disaster_area.create_from_geom(db=db, geom=geom, area=area, props=props)
    #         db.close()
    #         self.times["insert"] += time() - i_start
    #     end = time()
    #     self.times["total"] = end - start
    #     self.times = {k: round(v, 3) for (k, v) in self.times.items()}
    #     print(f"Inserting {len(features) - len(skipped)} areas took {end - start} seconds.")
    #     if skipped:
    #         print(f"{len(skipped)} Features were skipped: {str(skipped)}")
    #     print(str(self.times))
    #
    # def convert_disaster_areas(self, file_path: Path, simplify_percentage: int = 0, raster_size: float = 10) -> dict:
    #     self.file_path = file_path
    #     self._read_in_file()
    #     self._create_disaster_areas(simplify_percentage=simplify_percentage)
    #     return self.times


def product_to_name(p: EMSRProduct) -> str:
    p_name = p.name
    if p.monitoring:
        p_name += f" - Monitoring {p.monitoring}"
    return p_name

