"""
Pydantic models for the Travel Itinerary Builder.
Defines the data structures for trip requests, places, daily plans, and complete itineraries.
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TripRequest(BaseModel):
    """User's trip request with all preferences and constraints."""
    
    city: str = Field(..., description="Destination city name")
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    budget: float = Field(..., gt=0, description="Total budget in USD")
    interests: List[str] = Field(
        default_factory=list,
        description="User interests (e.g., museums, nature, food, history)"
    )
    pace: str = Field(
        default="moderate",
        description="Trip pace: relaxed, moderate, or packed"
    )
    group_size: int = Field(default=1, gt=0, description="Number of travelers")
    
    @field_validator("pace")
    @classmethod
    def validate_pace(cls, v: str) -> str:
        """Ensure pace is one of the allowed values."""
        allowed = ["relaxed", "moderate", "packed"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Pace must be one of {allowed}")
        return v_lower
    
    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        """Ensure end date is after start date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v
    
    @property
    def num_days(self) -> int:
        """Calculate number of days in the trip."""
        return (self.end_date - self.start_date).days
    
    @property
    def daily_budget(self) -> float:
        """Calculate daily budget."""
        return self.budget / max(self.num_days, 1)


class Place(BaseModel):
    """A point of interest (POI) with location and cost information."""
    
    name: str = Field(..., description="Place name")
    category: str = Field(..., description="Place category (e.g., museum, park, restaurant)")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    estimated_cost: float = Field(default=0.0, ge=0, description="Estimated cost in USD")
    hours: Optional[str] = Field(default=None, description="Opening hours")
    description: Optional[str] = Field(default=None, description="Place description")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Rating (0-5)")
    time_needed: int = Field(default=120, description="Estimated time needed in minutes")
    address: Optional[str] = Field(default=None, description="Street address")
    
    @property
    def coordinates(self) -> tuple[float, float]:
        """Return coordinates as a tuple."""
        return (self.latitude, self.longitude)


class DayPlan(BaseModel):
    """A single day's itinerary with planned places and costs."""
    
    day_index: int = Field(..., ge=1, description="Day number (1-indexed)")
    day_date: date = Field(..., description="Date of this day")
    places: List[Place] = Field(default_factory=list, description="List of places to visit")
    total_cost: float = Field(default=0.0, ge=0, description="Total cost for this day in USD")
    notes: Optional[str] = Field(default=None, description="Additional notes for the day")
    
    @property
    def place_count(self) -> int:
        """Number of places in this day's plan."""
        return len(self.places)
    
    @property
    def total_time(self) -> int:
        """Total estimated time in minutes for all activities."""
        return sum(place.time_needed for place in self.places)


class Itinerary(BaseModel):
    """Complete trip itinerary with all days and summary information."""
    
    trip_request: TripRequest = Field(..., description="Original trip request")
    days: List[DayPlan] = Field(default_factory=list, description="Daily plans")
    total_cost: float = Field(default=0.0, ge=0, description="Total estimated cost in USD")
    notes: Optional[str] = Field(default=None, description="General trip notes")
    created_at: datetime = Field(default_factory=datetime.now, description="When itinerary was created")
    
    @property
    def num_days(self) -> int:
        """Number of days in the itinerary."""
        return len(self.days)
    
    @property
    def total_places(self) -> int:
        """Total number of places across all days."""
        return sum(day.place_count for day in self.days)
    
    @property
    def budget_remaining(self) -> float:
        """Remaining budget after planned expenses."""
        return self.trip_request.budget - self.total_cost
    
    @property
    def budget_used_percentage(self) -> float:
        """Percentage of budget used."""
        if self.trip_request.budget == 0:
            return 0.0
        return (self.total_cost / self.trip_request.budget) * 100
