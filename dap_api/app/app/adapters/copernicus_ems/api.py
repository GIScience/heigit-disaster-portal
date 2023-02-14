import json
from typing import Any, List, Union, Optional, Dict

from fastapi import APIRouter, Depends, Query, Path
from pydantic import Field

from app.adapters import CopernicusAdapter
from app.adapters.copernicus_ems import CopernicusActivation, ActivationAOI
from app.adapters.copernicus_ems.adapter import product_to_name
from app.adapters.copernicus_ems.schemas import EMSRProduct, CopernicusImportBody, CopernicusTree

router = APIRouter()


def get_adapter() -> Optional[Any]:
    adapter: CopernicusAdapter = CopernicusAdapter.instance()
    try:
        return adapter
    finally:
        pass


copernicus_adapter = get_adapter()


@router.get(
    "/tree",
    response_model=dict,
    summary="JSON tree of available activations, aois and products"
)
def activations_tree() -> Any:
    """
    JSON tree of available activations, areas of interest (AOIs) and products.
    Usable to create dynamic dropdown entries in frontend applications.
    """
    activation_tree = {
        act.name: {
            aoi.name: [
                product_to_name(p) for p in aoi.products
            ] for aoi in act.aois
        } for act in copernicus_adapter.activations.values()
    }
    return activation_tree


@router.get(
    "/activations",
    response_model=List[str],
    summary="List of available activations"
)
def activations() -> Any:
    return [a.name for a in copernicus_adapter.activations.values()]


@router.get(
    "/activations/{activation}",
    response_model=List[str] | CopernicusActivation,
    summary="List available AOIs of an activation"
)
def get_aois(
        activation: str,
        v: bool = False) -> Any:
    if v:
        return copernicus_adapter.get_activation(activation)
    return copernicus_adapter.get_aois(act_name=activation)


@router.get(
    "/activations/{activation}/aois/{aoi}",
    response_model=List[str] | ActivationAOI,
    summary="List available products of an AOI"
)
def get_products(
        activation: str,
        aoi: str,
        v: bool = False) -> Any:
    act = copernicus_adapter.get_activation(activation)
    aoi_model = copernicus_adapter.get_aoi(act, aoi)
    if v:
        return aoi_model
    return copernicus_adapter.get_products(aoi=aoi_model)


@router.get(
    "/activations/{activation}/aois/{aoi}/products/{product}",
    response_model=EMSRProduct,
    summary="List product"
)
def get_product(
        activation: str,
        aoi: str,
        product: str,
) -> Any:
    act = copernicus_adapter.get_activation(activation)
    aoi_model = copernicus_adapter.get_aoi(act, aoi)
    product_model = copernicus_adapter.get_product(aoi_model, product)
    return product_model


@router.post(
    "/import",
    response_model=str,
    summary="Import Copernicus EMS products"
)
def import_products(
        body: CopernicusImportBody
        # activation: str = Query(
        #     ...,
        #     description="ID of the activation to import or import from"),
        # aois: List[str] | str = Query(
        #     default=["all"],
        #     description="Activation AOIs to import or import products from."),
        # products: List[str] | str = Query(
        #     default=["latest"],
        #     description="Products to import. By default only the latest products are imported. Specific products can "
        #                 "only be imported for a single AOI")
) -> Any:
    return json.dumps(body.dict())
    # act = copernicus_adapter.get_activation(activation)
    # if "all" in aois:
    #     return str(copernicus_adapter.get_aoi(activation=act, aoi_name=aois))
    # else:
    #     for aoi in aois:
    #         return"for aoi in aois"
    # #         import aoi
    # #     for a in act.aois:
    # #         print(str(a.products))
    # return "Imported ... or maybe not"
