# Disaster Portal Documentation

Welcome to the HeiGIT Disaster Portal Documentation.

This will give you a short introduction on what the selected disaster region
means, how to use the client to add new disaster areas and how to calculate
routes.

## Disaster region selection

When starting the HeiGIT Disaster Portal, you'll be greeted by the following screen:

![Disaster Portal starting page showing disaster region selection](img/disaster_portal_overview_with_selection.png)

Selecting a disaster region will limit your routing capabilities to the selected region.

![Selectable Regions](img/disaster_region_selection.png)

As an example, selecting the *Slovenia* region will result in the following
view.  Note, that everything *but* the selected region is not routable,
indicated by being greyed out.  OpenStreetMap data for the highlighted area
will be updated every 10 minutes. If a road is changed in OSM, e.g. marked as
impassable, this change will be respected after 15-20 minutes.

![Disaster Portal, Slovenia selected](img/disaster_portal_overview.png)

Compared to the classic client, the following controls are new or have special functionalities:

![Disaster Portal overview with annotated controls](img/disaster_portal_annotated.png)

1. Activate [Administration Mode](#administration-mode) to add/edit areas
2. Re-open the region selection.
3. Control the loaded layers to toggle impassable areas
4. Add areas (only in [Administration Mode](#administration-mode)


## Administration Mode

To be able to add or edit any of the given areas, you have to have access to any given data provider.
TODO: Contact XYZ if you need to edit areas, but don't have any access token.

Select your Data Provider and enter your access token here:

![Data Provider Authentication](img/data_provider_selection.png)

