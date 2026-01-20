"""
Pydantic AI agent for intelligent itinerary planning.
Handles POI ranking, day allocation, and cost estimation.
"""

import os
from datetime import timedelta
from typing import List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
import math

from models import TripRequest, Place, DayPlan, Itinerary


# Dependencies for the agent
class PlannerDeps:
    """Dependencies passed to the agent."""
    trip_request: TripRequest
    available_places: List[Place]
    city_coords: tuple[float, float]


# Initialize the agent
try:
    # Try to use Google Gemini if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        model = GeminiModel("gemini-1.5-flash", api_key=api_key)
    else:
        # Fallback to test model (rule-based)
        model = "test"
except Exception:
    model = "test"

planner_agent = Agent(
    model=model,
    deps_type=PlannerDeps,
    system_prompt="""You are an expert travel planner. Your job is to create balanced, 
    enjoyable itineraries that respect the user's budget, interests, and pace preferences.
    
    Key principles:
    - Distribute attractions evenly across days
    - Consider geographic proximity to minimize travel time
    - Respect daily budget constraints
    - Match activity types to user interests
    - Adjust density based on pace (relaxed=2-3 places/day, moderate=3-4, packed=5-6)
    - Include rest time and meals
    - Stay within total budget
    - Provide helpful notes and recommendations
    
    Return a complete Itinerary object with all required fields.
    """
)


@planner_agent.tool
def calculate_distance(ctx: RunContext[PlannerDeps], lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@planner_agent.tool
def rank_places_by_relevance(ctx: RunContext[PlannerDeps]) -> List[Place]:
    """
    Rank available places by relevance to user interests and proximity to city center.
    Returns sorted list of places.
    """
    places = ctx.deps.available_places
    interests = ctx.deps.trip_request.interests
    city_lat, city_lon = ctx.deps.city_coords
    
    scored_places = []
    
    for place in places:
        score = 0.0
        
        # Interest match score (0-10)
        for interest in interests:
            if interest.lower() in place.category.lower() or interest.lower() in place.name.lower():
                score += 5.0
        
        # Proximity score (closer to center = higher score, max 5)
        distance = calculate_distance(ctx, city_lat, city_lon, place.latitude, place.longitude)
        proximity_score = max(0, 5 - (distance / 2))
        score += proximity_score
        
        # Rating score (0-5)
        if place.rating:
            score += place.rating
        
        # Lower cost = slightly higher score for budget travelers
        if place.estimated_cost < ctx.deps.trip_request.daily_budget / 3:
            score += 2.0
        
        scored_places.append((place, score))
    
    # Sort by score descending
    scored_places.sort(key=lambda x: x[1], reverse=True)
    
    return [place for place, score in scored_places]


@planner_agent.tool
def allocate_places_to_days(ctx: RunContext[PlannerDeps], ranked_places: List[Place]) -> List[DayPlan]:
    """
    Allocate ranked places to specific days based on pace and budget.
    Returns list of DayPlan objects.
    """
    trip = ctx.deps.trip_request
    num_days = trip.num_days
    
    # Determine places per day based on pace
    pace_map = {
        "relaxed": 2,
        "moderate": 3,
        "packed": 5
    }
    target_places_per_day = pace_map.get(trip.pace, 3)
    
    daily_plans = []
    current_place_index = 0
    
    for day_num in range(1, num_days + 1):
        day_date = trip.start_date + timedelta(days=day_num - 1)
        day_places = []
        day_cost = 0.0
        
        # Add meal costs (breakfast, lunch, dinner)
        meal_cost = 40.0 * trip.group_size
        day_cost += meal_cost
        
        # Add places for this day
        while (
            len(day_places) < target_places_per_day 
            and current_place_index < len(ranked_places)
            and day_cost + ranked_places[current_place_index].estimated_cost * trip.group_size <= trip.daily_budget * 1.2
        ):
            place = ranked_places[current_place_index]
            day_places.append(place)
            day_cost += place.estimated_cost * trip.group_size
            current_place_index += 1
        
        # Add transport cost estimate
        transport_cost = 15.0 * trip.group_size
        day_cost += transport_cost
        
        notes = f"Includes meals (~${meal_cost:.0f}) and transport (~${transport_cost:.0f})"
        
        daily_plans.append(
            DayPlan(
                day_index=day_num,
                date=day_date,
                places=day_places,
                total_cost=round(day_cost, 2),
                notes=notes
            )
        )
    
    return daily_plans


def create_itinerary(trip_request: TripRequest, places: List[Place], city_coords: tuple[float, float]) -> Itinerary:
    """
    Main function to create a complete itinerary using the Pydantic AI agent.
    
    Args:
        trip_request: User's trip requirements
        places: Available POIs from API
        city_coords: (latitude, longitude) of the city center
        
    Returns:
        Complete Itinerary object
    """
    
    # For test model, use simple rule-based approach
    if model == "test":
        return create_itinerary_simple(trip_request, places, city_coords)
    
    # For OpenAI model, use AI agent
    deps = PlannerDeps(
        trip_request=trip_request,
        available_places=places,
        city_coords=city_coords
    )
    
    try:
        # Run the agent
        result = planner_agent.run_sync(
            f"""Create a {trip_request.num_days}-day itinerary for {trip_request.city} 
            with a budget of ${trip_request.budget} for {trip_request.group_size} people.
            Interests: {', '.join(trip_request.interests)}.
            Pace: {trip_request.pace}.
            Trip dates: {trip_request.start_date} to {trip_request.end_date}.
            
            Use the provided tools to rank places and allocate them to days optimally.""",
            deps=deps
        )
        
        return result.data
        
    except Exception as e:
        print(f"Error using AI agent, falling back to simple planner: {e}")
        return create_itinerary_simple(trip_request, places, city_coords)


def create_itinerary_simple(trip_request: TripRequest, places: List[Place], city_coords: tuple[float, float]) -> Itinerary:
    """
    Simple rule-based itinerary creation (fallback when AI not available).
    
    Args:
        trip_request: User's trip requirements
        places: Available POIs from API
        city_coords: (latitude, longitude) of the city center
        
    Returns:
        Complete Itinerary object
    """
    
    # Rank places by relevance
    scored_places = []
    interests = trip_request.interests
    city_lat, city_lon = city_coords
    
    for place in places:
        score = 0.0
        
        # Interest match
        for interest in interests:
            if interest.lower() in place.category.lower() or interest.lower() in place.name.lower():
                score += 5.0
        
        # Proximity to center
        distance = math.sqrt(
            (place.latitude - city_lat) ** 2 + (place.longitude - city_lon) ** 2
        )
        score += max(0, 5 - distance * 100)
        
        # Rating
        if place.rating:
            score += place.rating
        
        # Budget friendly
        if place.estimated_cost < trip_request.daily_budget / 3:
            score += 2.0
        
        scored_places.append((place, score))
    
    scored_places.sort(key=lambda x: x[1], reverse=True)
    ranked_places = [place for place, score in scored_places]
    
    # Allocate to days
    pace_map = {"relaxed": 2, "moderate": 3, "packed": 5}
    target_places_per_day = pace_map.get(trip_request.pace, 3)
    
    daily_plans = []
    current_index = 0
    
    for day_num in range(1, trip_request.num_days + 1):
        day_date = trip_request.start_date + timedelta(days=day_num - 1)
        day_places = []
        day_cost = 0.0
        
        # Meals
        meal_cost = 40.0 * trip_request.group_size
        day_cost += meal_cost
        
        # Add places
        while (
            len(day_places) < target_places_per_day 
            and current_index < len(ranked_places)
            and day_cost + ranked_places[current_index].estimated_cost * trip_request.group_size <= trip_request.daily_budget * 1.2
        ):
            place = ranked_places[current_index]
            day_places.append(place)
            day_cost += place.estimated_cost * trip_request.group_size
            current_index += 1
        
        # Transport
        transport_cost = 15.0 * trip_request.group_size
        day_cost += transport_cost
        
        notes = f"Includes meals (~${meal_cost:.0f}) and transport (~${transport_cost:.0f})"
        
        daily_plans.append(
            DayPlan(
                day_index=day_num,
                day_date=day_date,
                places=day_places,
                total_cost=round(day_cost, 2),
                notes=notes
            )
        )
    
    total_cost = sum(day.total_cost for day in daily_plans)
    
    budget_status = "within budget" if total_cost <= trip_request.budget else "slightly over budget"
    notes = f"Itinerary created for {trip_request.num_days} days with {trip_request.pace} pace. Total cost is {budget_status}."
    
    return Itinerary(
        trip_request=trip_request,
        days=daily_plans,
        total_cost=round(total_cost, 2),
        notes=notes
    )
