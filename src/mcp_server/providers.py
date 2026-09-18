"""Travel tool implementation"""

from __future__ import annotations
from datetime import date,timedelta
 
from src.config import get_settings
from src.mcp_server import MissingCredentials, ToolError
from src.schemas import Activity, FlightOption, HotelOption, WeatherDay, LocationMatch
from src.mcp_server.clients import get_json, http_client

TRAVELPAYOUTS_BASE = "https://api.travelpayouts.com"
TRAVELPAYOUTS_HOTEL_BASE = "https://engine.hotellook.com/api/v2"


def _travelpayouts_params(*, currency: str = "usd") -> dict[str, str]:
    settings = get_settings()
    token = (settings.travelpayouts_api_key or "").strip()
    if not token:
        raise MissingCredentials("travelpayouts")

    params: dict[str, str] = {"token": token, "currency": currency.lower()}
    marker = (settings.travelpayouts_marker or "").strip()
    if marker:
        params["marker"] = marker
    return params

_WMO:dict[int,str]= {
    0:"Clear sky",
    1:"Mainly clear",
    2:"Partly cloudy",
    3:"Overcast",
    45:"Fog",
    48:"Depositing rime fog",
    51:"Drizzle: Light",
    53:"Drizzle: Moderate",
    55:"Drizzle: Heavy"
}

def _geocode_open_meteo(client,city:str)-> tuple[float,float,str]:
    data = get_json(
        client,
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name":city,"count":1,"format":"json"}
    )
    results = data.get("results") or []
    if not results:
        raise ToolError(f"could not geocode city:{city!r}")
    top = results[0]
    label = ", ".join(p for p in (top.get("name"),top.get("country")) if p)
    return float(top["latitude"]), float(top["longitude"]),label

def get_weather(city:str, start_date:str,days:int=7) -> dict:
    """Return a daily forecast for `city` starting at `start_date` (ISO date)."""
    if days < 1:
        raise ToolError(f"days must be >= 1, got {days!r}")

    try:
        start = date.fromisoformat(start_date)
    except ValueError as exc:
        raise ToolError(f"invalid start_date: {start_date!r}") from exc

    client = http_client()
    try:
        latitude, longitude, label = _geocode_open_meteo(client, city)
        end_date = start + timedelta(days=max(days - 1, 0))
        payload = get_json(
            client,
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "start_date": start.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
    finally:
        client.close()

    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []

    forecast: list[WeatherDay] = []
    for idx, day in enumerate(times[:days]):
        code = codes[idx] if idx < len(codes) else None
        summary = _WMO.get(int(code), "Variable conditions") if code is not None else "Variable conditions"
        high = highs[idx] if idx < len(highs) and highs[idx] is not None else None
        low = lows[idx] if idx < len(lows) and lows[idx] is not None else None
        forecast.append(
            WeatherDay(
                day=date.fromisoformat(day),
                summary=summary,
                high_c=float(high) if high is not None else None,
                low_c=float(low) if low is not None else None,
            )
        )

    return {
        "location": label,
        "days": [d.model_dump(mode="json") for d in forecast],
    }


def convert_currency(amount: float, from_currency: str | None = None, to_currency: str = "USD", **kwargs) -> dict:
    """Convert an amount between currencies using the Frankfurter API."""
    if from_currency is None:
        from_currency = kwargs.pop("from_city", "USD")
    if "to_ccy" in kwargs:
        to_currency = kwargs.pop("to_ccy")
    if kwargs:
        unexpected = ", ".join(kwargs.keys())
        raise TypeError(f"Unexpected keyword arguments: {unexpected}")

    src = (from_currency or "USD").upper()
    dst = (to_currency or "USD").upper()
    with http_client() as client:
        payload = get_json(
            client,
            "https://api.frankfurter.app/latest",
            params={"from": src, "to": dst},
        )

    if "rates" not in payload or dst not in payload["rates"]:
        raise ToolError(f"no exchange rate available for {src} -> {dst}")

    rate = float(payload["rates"][dst])
    converted = float(amount) * rate
    return {
        "amount": float(amount),
        "from": src,
        "to": dst,
        "converted": converted,
        "rate": rate,
    }

# ---
#Places - OpenTripMap(API key required)
#---

_INTEREST_KINDS: dict[str, list[str]] = {
    "food": ["foods", "restaurants", "cafes"],
    "foods": ["foods", "restaurants", "cafes"],
    "drink": ["foods", "drinking_water", "beer"],
    "nightlife": ["nightclubs", "bars"],
    "history": ["historic", "architecture", "churches"],
    "culture": ["museums", "theatres", "art"],
    "nature": ["natural", "parks", "beaches", "mountains"],
    "outdoors": ["parks", "beaches", "natural", "mountains"],
    "shopping": ["shops", "markets"],
    "relax": ["beaches", "parks", "spa"],
    "family": ["amusements", "parks", "museums"],
    "default": ["interesting_places", "historic", "museums"],
}


def search_places(city:str, interests:list[str], limit:int = 10) -> dict:
    """Find points of interest in `city` matching a traveler's interests."""
    settings = get_settings()
    if not settings.opentripmap_api_key:
        raise MissingCredentials("opentripmap")

    kinds = []
    for interest in interests or ["default"]:
        lookup = str(interest).lower()
        kinds.extend(_INTEREST_KINDS.get(lookup, _INTEREST_KINDS["default"]))

    unique_kinds = list(dict.fromkeys(kinds))
    if not unique_kinds:
        unique_kinds = _INTEREST_KINDS["default"]

    with http_client() as client:
        geoname = get_json(
            client,
            "https://api.opentripmap.com/0.1/en/places/geoname",
            params={"name": city, "apikey": settings.opentripmap_api_key},
        )
        if not geoname:
            raise ToolError(f"could not resolve city: {city!r}")

        radius = get_json(
            client,
            "https://api.opentripmap.com/0.1/en/places/radius",
            params={
                "radius": 25000,
                "lon": geoname["lon"],
                "lat": geoname["lat"],
                "kinds": ",".join(unique_kinds),
                "limit": max(1, min(limit, 20)),
                "apikey": settings.opentripmap_api_key,
            },
        )

    features = radius.get("features") or []
    places: list[Activity] = []
    for feat in features[:limit]:
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None]
        lat_val = coords[1] if len(coords) > 1 and coords[1] is not None else None
        lon_val = coords[0] if len(coords) > 0 and coords[0] is not None else None
        places.append(
            Activity(
                name=str(props.get("name") or props.get("xid") or "Unnamed place"),
                category=str(props.get("kinds") or "general"),
                est_cost_usd=float(props.get("rate") or 0.0),
                lat=float(lat_val) if lat_val is not None else None,
                lon=float(lon_val) if lon_val is not None else None,
            )
        )

    return {
        "city": city,
        "places": [p.model_dump(mode="json") for p in places],
    }

#Flights - Travelpayouts API

def search_flights(origin:str, destination:str, depart_date:str, travelers:int = 1) -> dict:
    """Search flight offers via Travelpayouts. Falls back to mock data if the API key is missing."""
    params = _travelpayouts_params(currency="usd")
    params.update({
        "origin": origin.upper(),
        "destination": destination.upper(),
        "depart_date": depart_date,
    })

    try:
        with http_client() as client:
            payload = get_json(
                client,
                f"{TRAVELPAYOUTS_BASE}/v1/prices/cheap",
                params=params,
            )
    except MissingCredentials:
        demo = [
            FlightOption(
                airline="TP",
                price_usd=245.0 + (travelers * 15),
                depart=f"{depart_date}T08:30:00",
                arrive=f"{depart_date}T12:45:00",
                stops=0,
            ),
            FlightOption(
                airline="TP",
                price_usd=289.0 + (travelers * 18),
                depart=f"{depart_date}T11:00:00",
                arrive=f"{depart_date}T15:15:00",
                stops=1,
            ),
        ]
        return {"origin": origin.upper(), "destination": destination.upper(), "offers": [f.model_dump(mode="json") for f in demo]}

    data = payload.get("data") or {}
    offers = []
    for _destination, items in data.items():
        if isinstance(items, list):
            offers.extend(items)
        elif isinstance(items, dict):
            offers.append(items)

    flights: list[FlightOption] = []
    for item in offers[:5]:
        flights.append(
            FlightOption(
                airline=str(item.get("airline") or item.get("carrier") or "TP"),
                price_usd=float(item.get("price") or item.get("value") or 0.0),
                depart=str(item.get("depart_date") or item.get("departure_at") or depart_date),
                arrive=str(item.get("return_date") or item.get("arrival_at") or depart_date),
                stops=int(item.get("stops") or 0),
            )
        )

    if not flights:
        return {"origin": origin.upper(), "destination": destination.upper(), "offers": []}

    return {"origin": origin.upper(), "destination": destination.upper(), "offers": [f.model_dump(mode="json") for f in flights]}


def search_hotels(city:str, check_in:str, nights:int,travelers:int =1, max_price_usd: float | None = None) -> dict:
    """Search hotel offers via Travelpayouts/Hotellook. Falls back to demo pricing if the key is missing."""
    if nights < 1:
        raise ToolError(f"nights must be >= 1, got {nights!r}")

    params = _travelpayouts_params(currency="usd")
    params.update({
        "query": city,
        "limit": "10",
    })

    try:
        with http_client() as client:
            payload = get_json(
                client,
                f"{TRAVELPAYOUTS_HOTEL_BASE}/lookup.json",
                params=params,
            )
    except MissingCredentials:
        demo_hotels = [
            HotelOption(name=f"{city.title()} Central Hotel", price_per_night_usd=140.0, rating=4.5, area="downtown"),
            HotelOption(name=f"{city.title()} Riverside Stay", price_per_night_usd=185.0, rating=4.7, area="waterfront"),
            HotelOption(name=f"{city.title()} Budget Inn", price_per_night_usd=95.0, rating=4.1, area="midtown"),
        ]
        if max_price_usd is not None:
            demo_hotels = [h for h in demo_hotels if h.price_per_night_usd <= max_price_usd]
        return {"city": city, "hotels": [h.model_dump(mode="json") for h in demo_hotels]}

    results = payload.get("results") or payload.get("hotels") or payload.get("data") or []
    hotels_out: list[HotelOption] = []
    for hotel in results[:10]:
        price = float(hotel.get("price_from") or hotel.get("price") or 0.0)
        if max_price_usd is not None and price > max_price_usd:
            continue
        hotels_out.append(
            HotelOption(
                name=str(hotel.get("label") or hotel.get("name") or "Unnamed hotel"),
                price_per_night_usd=price,
                rating=float(hotel.get("stars") or 0.0) if hotel.get("stars") is not None else None,
                area=str(hotel.get("city") or hotel.get("location") or ""),
            )
        )

    return {"city": city, "hotels": [h.model_dump(mode="json") for h in hotels_out]}

_SUBTYPE_MAP = {
    "city": "CITY",
    "airport": "AIRPORT",
    "any": "CITY,AIRPORT",
}

def resolve_location(query:str, subtype:str="any") -> dict:
    """Resolve a location query to a normalized location with IATA code using Travelpayouts-compatible metadata when available."""
    subtype = _SUBTYPE_MAP.get(subtype.lower(), "CITY,AIRPORT")
    settings = get_settings()
    if settings.travelpayouts_api_key:
        with http_client() as client:
            payload = get_json(
                client,
                f"{TRAVELPAYOUTS_BASE}/v1/airports",
                params={"token": settings.travelpayouts_api_key, "marker": settings.travelpayouts_marker or "wandermind"},
            )
        airports = payload.get("airports") or payload.get("data") or {}
        for code, info in airports.items():
            name = info.get("name") if isinstance(info, dict) else None
            if name and query.lower() in str(name).lower():
                return {
                    "name": str(name),
                    "iata_code": str(code),
                    "subtype": subtype,
                    "country": str(info.get("country") or ""),
                    "lat": float(info.get("lat") or 0.0),
                    "lon": float(info.get("lon") or 0.0),
                }

    return {
        "name": query.strip() or "Unknown City",
        "iata_code": "",
        "subtype": subtype,
        "country": "",
        "lat": 0.0,
        "lon": 0.0,
    }