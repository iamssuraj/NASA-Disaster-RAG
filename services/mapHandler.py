import folium
from folium import CircleMarker
from folium.plugins import Fullscreen
from datetime import datetime

DISASTER_COLORS = {
    "Wildfires": "red",
    "Floods": "blue",
    "Severe Storms": "orange",
    "Volcanoes": "darkred",
    "Earthquakes": "purple",
    "Drought": "brown",
    "Sea and Lake Ice": "lightblue",
    "Landslides": "gray",
}

WORLD_BOUNDS = [[-85, -180], [85, 180]]  # world limits to prevent infinite scrolling


def create_disaster_map(events, center=None, zoom=2):
    try:
        if center is None:
            center = [20, 0]  

        map = folium.Map(
            location=center,
            zoom_start=zoom,
            min_zoom=2,
            max_zoom=8,
            world_copy_jump=False,
            no_wrap=True
        )

        
        map.fit_bounds(WORLD_BOUNDS)
        map.options["maxBounds"] = WORLD_BOUNDS

        Fullscreen(position="topleft").add_to(map)

        for event in events:
            metadata = getattr(event, "metadata", event)
            lat = metadata.get("latitude")
            lon = metadata.get("longitude")
            title = metadata.get("title")
            category = metadata.get("category")
            raw_date = metadata.get("date")
            try:
                date = datetime.fromisoformat(raw_date.replace("Z", "")).strftime("%b %d, %Y")
            except Exception:
                date = raw_date

            if lat and lon:
                color = DISASTER_COLORS.get(category)
                CircleMarker(
                    location=[lat, lon],
                    radius=7,
                    popup=f"<b>{title}</b><br>Type: {category}<br>Date: {date}",
                    tooltip=f"{category}: {title[:50]}",
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.75,
                ).add_to(map)

        return map

    except Exception as e:
        raise RuntimeError(f"Failed to create map: {e}")
