from datetime import datetime
from enum import Enum
from typing import List, Union, Dict

from pydantic import BaseModel, Field, validator


PRODUCT_STRING_VALUES = ["latest", "initial", "all"]


# class ProductTreeEntry(BaseModel):
#     __root__: List[str]


class AOITreeEntry(BaseModel):
    __root__: Dict[str, List[str]]


class ActivationTreeEntry(BaseModel):
    __root__: Dict[str, Dict[str, List[str]]]


class CopernicusTree(BaseModel):
    __root__: Dict[str, Dict[str, Dict[str, List[str]]]]


class ActivationStatus(str, Enum):
    open = "Open"
    closed = "Closed"


class EMSRProduct(BaseModel):
    name: str
    monitoring: int
    release: int
    version: int
    status: str
    download_id: int
    created: datetime


class ActivationAOI(BaseModel):
    id: int
    name: str
    products: List[EMSRProduct]


class CopernicusActivation(BaseModel):
    id: int
    aois: List[ActivationAOI]
    name: str
    status: ActivationStatus
    created: datetime
    content_hash: str
    description: str
    event_timestamp: datetime
    event_type: str


class CopernicusImportBody(BaseModel):
    activation: str = Field(
        ...,
        description="ID of the activation to import or import from")
    aois: List[str] | str = Field(
        "all",
        description="Activation AOIs to import or import products from. "
                    "Takes either a list of specific AOI names, a single AOI name or 'all'.")
    products: List[str] | str = Field(
        "latest",
        description=f"Products to import. Takes either a list of specific Product names, a single Product name or"
                    f"one of {PRODUCT_STRING_VALUES}. Specific products can only be imported for a single AOI")

    @validator('activation')
    def existing_activation(cls, v):
        from app.adapters import CopernicusAdapter
        from .api import get_adapter
        adapter: CopernicusAdapter = get_adapter()
        adapter.get_activation(v)  # raises value error if activation not available
        return v

    @validator('aois')
    def aois_available(cls, v, values):
        if 'activation' not in values:  # activation validator raised error
            raise ValueError("Invalid activation")
        from app.adapters import CopernicusAdapter
        from .api import get_adapter
        adapter: CopernicusAdapter = get_adapter()
        if v not in ['all']:
            act_name = values['activation']
            act = adapter.get_activation(act_name)
            if type(v) == str:
                entry = adapter.get_aoi(act, v)
                if not entry:
                    raise ValueError(
                        f"No AOI '{v}' in activation 'EMSR{act.id:03}'. "
                        f"Choose out of [{', '.join(adapter.get_aois(act_name))}]"
                    )
            else:
                for aoi in v:
                    entry = adapter.get_aoi(act, aoi)
                    if not entry:
                        raise ValueError(
                            f"No AOI '{aoi}' in activation 'EMSR{act.id:03}'. "
                            f"Choose out of [{', '.join(adapter.get_aois(act_name))}]"
                        )
        return v

    @validator('products')
    def products_available(cls, v, values, **kwargs):
        if 'aois' not in values:  # aois validator raised error
            raise ValueError("Invalid AOI")
        from app.adapters import CopernicusAdapter
        from .api import get_adapter
        adapter: CopernicusAdapter = get_adapter()
        if v not in PRODUCT_STRING_VALUES:
            aois = values['aois']
            only_generic_values_error = TypeError(
                f"If multiple AOIs are specified, "
                f"only the generic {PRODUCT_STRING_VALUES} product types can be imported.")
            if aois == "all":
                raise only_generic_values_error
            if type(aois) == list:
                if len(aois) != 1:
                    raise only_generic_values_error
                aois = aois[0]
            act_name = values['activation']
            act = adapter.get_activation(act_name)
            aoi = adapter.get_aoi(act, aois)
            products = adapter.get_products(aoi)
            if type(v) == str:
                v = [v]
            for product in v:
                if product not in products:
                    raise ValueError(f"No product {product} in AOI '{aois}' of activation 'EMSR{act.id}'. "
                                     f"Choose out of [{', '.join(adapter.get_products(aoi))}]")
        return v
