# Disaster Portal Documentation

Welcome to the HeiGIT Disaster Portal Documentation.

This will give you a short introduction on what the selected disaster region
means and how to use the client to add new disaster areas

The portal aims at helping during disaster relief efforts by providing up to
date information regarding inaccessible parts of the road network. This is done
by drawing areas that mark the underlying parts of the road network as
impassable. These areas will be automatically taken into account when
calculating routes or analyzing reachability.

## Disaster region selection

When starting the HeiGIT Disaster Portal, you'll be greeted by the following screen:

![Disaster Portal starting page showing disaster region selection](img/disaster_portal_overview_with_selection_lowres.png)

Selecting a disaster region will limit your routing capabilities to the selected region.

<p align=center>
<kbd>
    <img src="img/disaster_region_selection.png" />
</kbd>
</p>

As an example, selecting the *Slovenia* region will result in the following
view:

 ![Disaster Portal, Slovenia selected](img/disaster_portal_overview_lowres.png)

Note, that everything *but* the selected region is not routable,
indicated by being greyed out.  OpenStreetMap data for the highlighted area
will be updated every 10 minutes. If a road is changed in OSM, e.g. marked as
impassable, this change will be respected after 15-20 minutes.


## Disaster Portal Controls

Compared to the regular client, the following controls are new or have special functionalities:

![Disaster Portal overview with annotated controls](img/portal_controls_lowres.png)

1. Activate [Administration Mode](#administration-mode) to add/edit areas
2. Re-open the region selection.
3. Control the loaded layers to toggle impassable areas
4. Add areas (only in [Administration Mode](#administration-mode))

Routes and isochrones can be calculated by anyone without access to a data
provider. The shown areas are automatically taken into account.  Data provider
access is only used for adding and editing areas.

## Administration Mode

To be able to add or edit any of the given areas, you have to have access to any given data provider.
Contact support@smartmobility.heigit.org if you need to edit areas, but don't have any access token.

Once you have an access token, click on the button marked with `1` in [the
controls section](#disaster-portal-controls) and select your Data Provider and
enter your access token in the following dialog:

<p align=center>
<kbd>
    <img alt="Data Provider Authentication" src="img/data_provider_selection.png" />
</kbd>
</p>

Once you are authenticated, you can add areas using button `4` mentioned in [the
controls section](#disaster-portal-controls).

### Area Creation

Click to mark every corner of your area, and click on the first point to finish your area:

https://github.com/koebi/heigit-disaster-portal/assets/4692974/30d1ca1e-ce0e-4c9d-9e00-5c78f442640e

### Area Metadata

Once the area is finished, the following dialog will open up to enter metadata concerning the area:

<p align=center>
<kbd>
    <img alt="Editing description for new region" src="img/new_region_description.png" />
</kbd>
</p>

The following information can be set:


| Key         | Description |
| ----------- | ----------- |
| `Name` | Unique name of the drawn region |
| `Disaster type` | Specify the type of incindent that caused the impassable area. The following types are available: <br />  _earthquake_, _volcanic activity_, _storm_, _extreme temperature_, _flood_, _mass movement_, _drought_, _wildfire_, _epidemic_, _infestation_, _industrial accident_, _transport accident_, _humanitarian_ or _other_ |
| `Disaster subtype` (optional) | More detailed type of incident, depending on `Disaster type` |
| `Description` | Text field to input more information |

### Area Editing

Via a click on an existing area, the following options are available:

<p align=center>
<kbd>
    <img alt="Options for existing area" src="img/area_left_click_overlay.png" />
</kbd>
</p>

From left to right, they are:

1. Edit the area
2. Delete the area
3. Edit the area information

When recalculating a route, the new or changed area is immediately respected and available for other users of the portal.
