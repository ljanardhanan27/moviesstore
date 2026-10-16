REGIONS = {
    "atlanta": {
        "name": "Atlanta, GA",
        "lat": 33.7490,
        "lng": -84.3880,
    },
    "new_york": {
        "name": "New York, NY",
        "lat": 40.7128,
        "lng": -74.0060,
    },
    "chicago": {
        "name": "Chicago, IL",
        "lat": 41.8781,
        "lng": -87.6298,
    },
    "los_angeles": {
        "name": "Los Angeles, CA",
        "lat": 34.0522,
        "lng": -118.2437,
    },
    "houston": {
        "name": "Houston, TX",
        "lat": 29.7604,
        "lng": -95.3698,
    }
}

REGION_CHOICES = [
    (code, region["name"])
    for code, region in REGIONS.items()
]