["Select a disaster region"-Popup showing three regions]
This is a short introduction to the disaster portal developed at HeiGIT gGmbH
in Heidelberg.  The portal aims at helping during disaster relief efforts by
providing up to date information for planning routes and generating areas of
reachability while considering inaccessible parts of the road network.

The web application is based on our existing map client showcasing the features of the openrouteservice API, but this one has some additional features which help during desaster scenarios. OpenStreetMap data is used for building the road network, which is updated every 10 minutes. If a road in OpenStreetMap is marked as impassable, the change will be respected after 15 - 20 minutes. To make this fast update cycle possible, the region needs to be limited, which is why we only have these three different regions available for now.

These can be added by us on demand. For now, let's choose the Anatolia region

{Click on "Earthquake in Anatolia region"}
[BBox showing region with green, red, yellow, blue marks on map. Everything outside of region greyed out.]

The overlay currently shows some relevant information on the status of border control points and roads where "green" is "passable", "yellow" is "restricted" and "red" is "closed" or "impassable".

{Click on "Layer" button in top right corner}
[As before, Layer popup showing with toggle for "Custom overlayer"].

The overlay can be disabled {Click} using the layer switcher

The portal includes a feature storage for disaster areas like flooded or blocked roads, which are automatically avoided when generating routes or isochrones

{Zoom to urban area}
[Urban Area, showing blue polygonal overlays]

[Route generation process using right-click context menu is executed ]
If you want to generate a route from this point to here.

As you can see, this area is automatically avoided when calculating the route.
{Shows area being avoided}

Using and viewing the data can be done by everyone, but to add, edit or remove features you need to be a registered Data Provider.
If you already have a Data Provider, you can log in in the bottom right corner

{Click on Lock in Bottom right corner}
[Popup for Authorization is shown]

choosing your Data Provider and entering the matching token.

{Click on "Save"}

And now you can add, adjust or remove data for your provider.

{Right-click on Region showing context menu}
{Click on Trash bin to remove stuff}

You can add areas by clicking one of these two buttons

{Mouse hovering over two add area buttons in top left}.
{Click on upper button}

and just draw a polygon

{Clicking to draw polygon}

give it a unique Name

{Clicking on first point to finish}
[Popup of Polygon Information is shown]

select a disaster type from the predefined list
the subtype is optional
and give it a description.

When recalculating the route, it is immediately respected and also available for other users of the portal.
If you don't have a data provider but would like to use the feature storage, you can contact us.
The features are available via a REST API and can therefore also be consumed and/or managed programatically by other applications

[Swagger API Docs visible, from "Disaster types" on]

Currently, we are looking into providing additionaly data sources and automatically importing the latest changes
This is the end for the short intro
We are happy to get feedback regarding needed features or datasets and also bug report are very welcome.
If you want to know more, please contact us at info@heigit.org.
Thank you very much.
