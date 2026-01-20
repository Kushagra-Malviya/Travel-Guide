"""
API clients for external services.
Handles geocoding (Nominatim) and POI discovery (OpenTripMap).
"""

import os
import requests
import time
from typing import List, Optional, Dict, Any
from models import Place


class NominatimClient:
    """Client for Nominatim geocoding API."""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    
    def __init__(self, user_agent: str = "TravelItineraryBuilder/1.0"):
        """
        Initialize Nominatim client.
        
        Args:
            user_agent: User agent string for API requests
        """
        self.user_agent = user_agent
        self.headers = {"User-Agent": user_agent}
    
    def geocode_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Get coordinates for a city.
        
        Args:
            city_name: Name of the city to geocode
            
        Returns:
            Dictionary with lat, lon, display_name, and bounding box, or None if not found
        """
        try:
            params = {
                "q": city_name,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"DEBUG: Geocoding '{city_name}' returned {len(data)} result(s)")
            if not data:
                return None
            
            result = data[0]
            return {
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
                "display_name": result.get("display_name", city_name),
                "boundingbox": result.get("boundingbox")
            }
            
        except Exception as e:
            print(f"Error geocoding city {city_name}: {e}")
            return None


class OverpassPOIClient:
    """Client for Overpass API (OpenStreetMap) to fetch POIs - completely free, no API key needed."""
    
    # Multiple Overpass API servers as fallbacks
    OVERPASS_SERVERS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]
    
    # OSM tag mapping for interests
    INTEREST_TO_OSM_TAGS = {
        "museums": ["tourism=museum"],
        "history": ["tourism=museum", "historic=monument", "historic=castle"],
        "culture": ["tourism=museum", "tourism=gallery", "tourism=theatre"],
        "art": ["tourism=gallery", "tourism=artwork"],
        "nature": ["leisure=park", "leisure=garden", "natural=beach"],
        "parks": ["leisure=park", "leisure=garden"],
        "outdoor": ["leisure=park", "natural=peak", "tourism=viewpoint"],
        "food": ["amenity=restaurant", "amenity=cafe", "amenity=bar"],
        "restaurants": ["amenity=restaurant", "amenity=cafe"],
        "architecture": ["tourism=attraction", "historic=building", "building=cathedral"],
        "religion": ["amenity=place_of_worship", "building=church", "building=mosque"],
        "sport": ["leisure=sports_centre", "leisure=stadium"],
        "shopping": ["shop=mall", "shop=department_store"],
        "entertainment": ["tourism=attraction", "leisure=amusement_arcade"],
        "amusements": ["tourism=theme_park", "leisure=amusement_arcade"]
    }
    
    def __init__(self):
        """Initialize Overpass API client (no API key needed)."""
        self.headers = {"User-Agent": "TravelItineraryBuilder/1.0"}
    
    def fetch_pois(
        self,
        latitude: float,
        longitude: float,
        radius: int = 10000,
        interests: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Place]:
        """
        Fetch points of interest within a radius using OpenStreetMap data.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters
            interests: List of interest categories
            limit: Maximum number of POIs to return
            
        Returns:
            List of Place objects
        """
        places = []
        
        # Get OSM tags based on interests
        if interests:
            osm_tags = self._map_interests_to_tags(interests)
        else:
            osm_tags = ["tourism=museum", "amenity=restaurant", "leisure=park"]
        
        # Build Overpass query
        query = self._build_query(latitude, longitude, radius, osm_tags)
        
        # Try multiple Overpass servers
        last_error = None
        for server_url in self.OVERPASS_SERVERS:
            try:
                print(f"DEBUG: Fetching POIs from OpenStreetMap at ({latitude}, {longitude}) via {server_url}")
                response = requests.post(
                    server_url,
                    data={"data": query},
                    headers=self.headers,
                    timeout=15
                )
                response.raise_for_status()
                
                data = response.json()
                elements = data.get("elements", [])
                print(f"DEBUG: Found {len(elements)} POIs from OpenStreetMap")
                break  # Success, exit the loop
            except Exception as e:
                last_error = e
                print(f"DEBUG: Server {server_url} failed: {e}")
                continue
        else:
            # All servers failed
            raise last_error if last_error else Exception("All Overpass servers failed")
        
        try:
            
            # Process each element
            for element in elements[:limit]:
                try:
                    place = self._parse_element(element)
                    if place:
                        places.append(place)
                except Exception as e:
                    print(f"Error parsing element: {e}")
                    continue
            
            print(f"DEBUG: Successfully parsed {len(places)} places")
            return places
            
        except Exception as e:
            print(f"Error fetching POIs from Overpass API: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _map_interests_to_tags(self, interests: List[str]) -> List[str]:
        """Map user interests to OSM tags."""
        tags = []
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in self.INTEREST_TO_OSM_TAGS:
                tags.extend(self.INTEREST_TO_OSM_TAGS[interest_lower])
        
        # Remove duplicates
        return list(set(tags)) if tags else ["tourism=attraction"]
    
    def _build_query(self, lat: float, lon: float, radius: int, tags: List[str]) -> str:
        """Build Overpass QL query - simplified for better performance."""
        # Limit to first 3 tags to avoid timeout
        tags = tags[:3]
        
        # Build tag filters - only search nodes for better performance
        tag_filters = []
        for tag in tags:
            key, value = tag.split("=")
            tag_filters.append(f'  node["{key}"="{value}"](around:{radius},{lat},{lon});')
        
        query = f"""[out:json][timeout:10];
(
{chr(10).join(tag_filters)}
);
out body 50;"""
        return query
    
    def _parse_element(self, element: Dict[str, Any]) -> Optional[Place]:
        """Parse an OSM element into a Place object."""
        try:
            tags = element.get("tags", {})
            
            # Get name
            name = tags.get("name")
            if not name:
                # Try alternative name fields
                name = tags.get("name:en") or tags.get("official_name")
            
            if not name:
                return None
            
            # Get coordinates
            if element.get("type") == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            elif "center" in element:
                lat = element["center"].get("lat")
                lon = element["center"].get("lon")
            else:
                return None
            
            if lat is None or lon is None:
                return None
            
            # Determine category
            category = self._determine_category(tags)
            
            # Estimate cost and time
            estimated_cost = self._estimate_cost(category, tags)
            time_needed = self._estimate_time(category)
            
            # Get opening hours if available
            hours = tags.get("opening_hours")
            
            # Get description
            description = tags.get("description") or tags.get("wikipedia")
            
            # Get address
            address = tags.get("addr:street")
            
            return Place(
                name=name,
                category=category,
                latitude=lat,
                longitude=lon,
                estimated_cost=estimated_cost,
                hours=hours,
                description=description,
                rating=None,  # OSM doesn't have ratings
                time_needed=time_needed,
                address=address
            )
            
        except Exception as e:
            print(f"Error parsing element: {e}")
            return None
    
    def _determine_category(self, tags: Dict[str, str]) -> str:
        """Determine category from OSM tags."""
        # Priority order for category determination
        if tags.get("tourism") == "museum":
            return "museum"
        elif tags.get("tourism") == "gallery":
            return "art_gallery"
        elif tags.get("tourism") == "attraction":
            return "attraction"
        elif tags.get("tourism") == "viewpoint":
            return "viewpoint"
        elif tags.get("amenity") == "restaurant":
            return "restaurant"
        elif tags.get("amenity") == "cafe":
            return "cafe"
        elif tags.get("amenity") == "place_of_worship":
            return "religious_site"
        elif tags.get("leisure") == "park":
            return "park"
        elif tags.get("leisure") == "garden":
            return "garden"
        elif tags.get("historic"):
            return f"historic_{tags['historic']}"
        elif tags.get("shop"):
            return f"shopping"
        else:
            return "attraction"
    
    def _estimate_cost(self, category: str, tags: Dict[str, str]) -> float:
        """Estimate cost based on category and tags."""
        # Check if there's a fee tag
        fee = tags.get("fee", "").lower()
        if fee == "no":
            return 0.0
        
        cost_map = {
            "museum": 15.0,
            "art_gallery": 12.0,
            "park": 0.0,
            "garden": 5.0,
            "restaurant": 25.0,
            "cafe": 15.0,
            "religious_site": 0.0,
            "historic": 10.0,
            "attraction": 10.0,
            "shopping": 20.0,
            "viewpoint": 0.0
        }
        
        for key, cost in cost_map.items():
            if key in category.lower():
                return cost
        return 10.0
    
    def _estimate_time(self, category: str) -> int:
        """Estimate time needed in minutes based on category."""
        time_map = {
            "museum": 120,
            "art_gallery": 90,
            "park": 60,
            "garden": 45,
            "restaurant": 90,
            "cafe": 45,
            "religious": 45,
            "historic": 60,
            "attraction": 90,
            "shopping": 90,
            "viewpoint": 30
        }
        
        for key, time_min in time_map.items():
            if key in category.lower():
                return time_min
        return 60


# Singleton instances
nominatim = NominatimClient()
opentripmap = OverpassPOIClient()  # Using Overpass API instead of OpenTripMap
