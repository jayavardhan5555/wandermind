"""Travel tool implementation"""

from __future__ import annotations
from datetime import date,timedelta

from config import get_settings
from mcp_server import MissingCredentials, ToolError
from schemas import Activity, FlightOption, HotelOption, WeatherDay,LocationMatch
from mcp_server.clients import AMADEUS_BASE, AmadeusAuth,get_json,http_client

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

#Flights - Amadeus self service - API key required

def search_flights(origin:str, destination:str, depart_date:str, travelers:int = 1) -> dict:
    """Search flight offers for a route/date using Amadeus."""
    settings = get_settings()
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        raise MissingCredentials("amadeus")

    client = http_client()
    try:
        headers = AmadeusAuth.auth_header(settings, client)
        payload = get_json(
            client,
            f"{AMADEUS_BASE}/v2/shopping/flight-offers",
            params={
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": depart_date,
                "adults": travelers,
                "max": 5,
            },
            headers=headers,
        )
    finally:
        client.close()

    offers = payload.get("data") or []
    flights: list[FlightOption] = []
    for offer in offers:
        itineraries = offer.get("itineraries") or []
        if not itineraries:
            continue
        outbound = itineraries[0].get("segments") or []
        if not outbound:
            continue
        depart_at = outbound[0].get("departure", {}).get("at") or ""
        arrive_at = outbound[-1].get("arrival", {}).get("at") or ""
        fare = offer.get("price") or {}
        airline = (
            outbound[0].get("carrierCode")
            or offer.get("validatingAirlineCodes", ["Unknown"])[0]
            or "Unknown"
        )
        flights.append(
            FlightOption(
                airline=str(airline),
                price_usd=float(fare.get("grandTotal") or 0.0),
                depart=depart_at,
                arrive=arrive_at,
                stops=max(0, len(outbound) - 1),
            )
        )

    return {"origin": origin.upper(), "destination": destination.upper(), "offers": [f.model_dump(mode="json") for f in flights]}


def search_hotels(city:str, check_in:str, nights:int,travelers:int =1, max_price_usd: float | None = None) -> dict:
    """Search hotel offers for a city code/date range using Amadeus."""
    if nights < 1:
        raise ToolError(f"nights must be >= 1, got {nights!r}")

    settings = get_settings()
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        raise MissingCredentials("amadeus")

    client = http_client()
    try:
        headers = AmadeusAuth.auth_header(settings, client)
        city_code = city.upper().strip()
        if len(city_code) != 3:
            raise ToolError(f"hotel search expects a 3-letter IATA city code, got {city!r}")

        location_payload = get_json(
            client,
            f"{AMADEUS_BASE}/v1/reference-data/locations/hotels/by-city",
            params={"cityCode": city_code},
            headers=headers,
        )
        hotels = location_payload.get("data") or []
        hotel_ids = [hotel.get("hotelId") for hotel in hotels if hotel.get("hotelId")][:10]
        if not hotel_ids:
            return {"city": city, "hotels": []}

        offers = get_json(
            client,
            f"{AMADEUS_BASE}/v3/shopping/hotel-offers",
            params={
                "hotelIds": ",".join(hotel_ids),
                "adults": travelers,
                "checkInDate": check_in,
                "checkOutDate": (date.fromisoformat(check_in) + timedelta(days=nights)).isoformat(),
                "currency": "USD",
            },
            headers=headers,
        )
    finally:
        client.close()

    hotel_items = offers.get("data") or []
    hotels_out: list[HotelOption] = []
    for item in hotel_items:
        offer = (item.get("offers") or [{}])[0]
        price = float((offer.get("price") or {}).get("total") or 0.0)
        if max_price_usd is not None and price > max_price_usd:
            continue
        hotel = item.get("hotel") or {}
        hotels_out.append(
            HotelOption(
                name=str(hotel.get("name") or "Unnamed hotel"),
                price_per_night_usd=price,
                rating=float(hotel.get("rating") or 0.0) if hotel.get("rating") is not None else None,
                area=str(hotel.get("cityCode") or ""),
            )
        )

    return {"city": city, "hotels": [h.model_dump(mode="json") for h in hotels_out]}

_SUBTYPE_MAP = {
    "city": "CITY",
    "airport": "AIRPORT",
    "any": "CITY,AIRPORT",
}

def resolve_location(query:str, subtype:str="any") -> dict:
    """Resolve a location query to a normalized location with IATA code."""
    subtype = _SUBTYPE_MAP.get(subtype.lower(), "CITY,AIRPORT")
    settings = get_settings()
    if not settings.amadeus_client_id or not settings.amadeus_client_secret:
        raise MissingCredentials("amadeus")

    client = http_client()
    try:
        headers = AmadeusAuth.auth_header(settings, client)
        payload = get_json(
            client,
            f"{AMADEUS_BASE}/v1/reference-data/locations",
            params={"keyword": query, "subType": subtype, "page[limit]": 1},
            headers=headers,
        )
    finally:
        client.close()

    locations = payload.get("data") or []
    if not locations:
        raise ToolError(f"could not resolve location: {query!r}")

    loc = locations[0]
    return {
        "name": str(loc.get("name") or ""),
        "iata_code": str(loc.get("iataCode") or ""),
        "subtype": str(loc.get("subType") or ""),
        "country": str((loc.get("address") or {}).get("countryName") or ""),
        "lat": float((loc.get("geoCode") or {}).get("latitude") or 0.0),
        "lon": float((loc.get("geoCode") or {}).get("longitude") or 0.0),
    }