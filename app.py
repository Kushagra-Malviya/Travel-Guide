"""
Travel Itinerary Builder - Streamlit Application
Main UI for generating personalized travel itineraries using Pydantic AI.
"""

import streamlit as st
from datetime import date, timedelta
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

from models import TripRequest
from api_clients import nominatim, opentripmap
from agent import create_itinerary

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Travel Itinerary Builder",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .day-card {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .place-card {
        background-color: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
    }
    .cost-badge {
        background-color: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
    .budget-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Header
    st.markdown('<div class="main-header">✈️ Travel Itinerary Builder</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Generate personalized day-by-day itineraries powered by Pydantic AI</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar - Input Form
    with st.sidebar:
        st.header("Trip Details")
        
        # City input
        city = st.text_input(
            "Destination City",
            value="Paris",
            help="Enter the city you want to visit"
        )
        
        # Date selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today() + timedelta(days=7),
                min_value=date.today()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today() + timedelta(days=10),
                min_value=start_date + timedelta(days=1)
            )
        
        # Budget
        budget = st.number_input(
            "Total Budget (USD)",
            min_value=100.0,
            max_value=50000.0,
            value=1500.0,
            step=100.0,
            help="Your total budget for the entire trip"
        )
        
        # Group size
        group_size = st.number_input(
            "Group Size",
            min_value=1,
            max_value=10,
            value=2,
            help="Number of travelers"
        )
        
        # Interests
        st.subheader("Interests")
        interests = []
        
        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox("Museums", value=True):
                interests.append("museums")
            if st.checkbox("Nature"):
                interests.append("nature")
            if st.checkbox("Food", value=True):
                interests.append("food")
            if st.checkbox("Architecture"):
                interests.append("architecture")
        
        with col2:
            if st.checkbox("History"):
                interests.append("history")
            if st.checkbox("Art"):
                interests.append("art")
            if st.checkbox("Shopping"):
                interests.append("shopping")
            if st.checkbox("Entertainment"):
                interests.append("entertainment")
        
        # Pace
        pace = st.select_slider(
            "Trip Pace",
            options=["relaxed", "moderate", "packed"],
            value="moderate",
            help="Relaxed: 2-3 places/day, Moderate: 3-4 places/day, Packed: 5-6 places/day"
        )
        
        # Generate button
        generate_button = st.button("🎯 Generate Itinerary", type="primary", use_container_width=True)
    
    # Main content area
    if generate_button:
        if not city:
            st.error("Please enter a destination city!")
            return
        
        if not interests:
            st.warning("No interests selected. Using default interests (museums, food).")
            interests = ["museums", "food"]
        
        # Create trip request
        try:
            trip_request = TripRequest(
                city=city,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                interests=interests,
                pace=pace,
                group_size=group_size
            )
        except Exception as e:
            st.error(f"Invalid input: {e}")
            return
        
        # Show progress
        with st.spinner("🌍 Geocoding city..."):
            city_data = nominatim.geocode_city(city)
            
            if not city_data:
                st.error(f"Could not find city: {city}. Please try a different name.")
                return
            
            city_coords = (city_data["latitude"], city_data["longitude"])
            st.success(f"Found: {city_data['display_name']}")
        
        with st.spinner("🔍 Discovering points of interest..."):
            places = opentripmap.fetch_pois(
                latitude=city_coords[0],
                longitude=city_coords[1],
                radius=10000,
                interests=interests,
                limit=50
            )
            
            if not places:
                st.warning("No places found. Try adjusting your search criteria.")
                return
            
            st.success(f"Found {len(places)} places!")
        
        with st.spinner("🤖 Creating your personalized itinerary..."):
            itinerary = create_itinerary(trip_request, places, city_coords)
            st.success("Itinerary created!")
        
        # Store in session state
        st.session_state['itinerary'] = itinerary
        st.session_state['city_data'] = city_data
    
    # Display itinerary if it exists
    if 'itinerary' in st.session_state:
        itinerary = st.session_state['itinerary']
        city_data = st.session_state['city_data']
        
        # Summary section
        st.header("📋 Trip Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{itinerary.num_days} days")
        with col2:
            st.metric("Total Places", itinerary.total_places)
        with col3:
            budget_color = "normal" if itinerary.total_cost <= itinerary.trip_request.budget else "inverse"
            st.metric(
                "Estimated Cost",
                f"${itinerary.total_cost:,.0f}",
                delta=f"{itinerary.total_cost - itinerary.trip_request.budget:+,.0f}",
                delta_color=budget_color
            )
        with col4:
            st.metric("Budget Used", f"{itinerary.budget_used_percentage:.1f}%")
        
        if itinerary.notes:
            st.info(f"ℹ️ {itinerary.notes}")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📅 Daily Itinerary", "🗺️ Map View", "💰 Cost Breakdown"])
        
        with tab1:
            # Display day-by-day itinerary
            st.header("Day-by-Day Itinerary")
            
            for day in itinerary.days:
                with st.expander(
                    f"**Day {day.day_index}** - {day.day_date.strftime('%A, %B %d, %Y')} "
                    f"({day.place_count} places, ${day.total_cost:.2f})",
                    expanded=True
                ):
                    if day.notes:
                        st.caption(day.notes)
                    
                    if not day.places:
                        st.warning("No places scheduled for this day.")
                    else:
                        for idx, place in enumerate(day.places, 1):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{idx}. {place.name}**")
                                st.caption(f"📍 {place.category.title()}")
                                
                                if place.description:
                                    # Use a popover or just show truncated text instead of nested expander
                                    desc = place.description[:200] + "..." if len(place.description) > 200 else place.description
                                    st.caption(f"ℹ️ {desc}")
                                
                                if place.hours:
                                    st.caption(f"🕐 {place.hours}")
                            
                            with col2:
                                cost_per_person = place.estimated_cost
                                total_cost = cost_per_person * itinerary.trip_request.group_size
                                
                                if cost_per_person == 0:
                                    st.success("Free")
                                else:
                                    st.info(f"${cost_per_person:.0f}/person")
                                    if itinerary.trip_request.group_size > 1:
                                        st.caption(f"${total_cost:.0f} total")
                                
                                st.caption(f"⏱️ ~{place.time_needed} min")
                            
                            st.divider()
        
        with tab2:
            # Map view
            st.header("Map View")
            
            # Create map centered on city
            m = folium.Map(
                location=[city_data["latitude"], city_data["longitude"]],
                zoom_start=13,
                tiles="OpenStreetMap"
            )
            
            # Add city center marker
            folium.Marker(
                [city_data["latitude"], city_data["longitude"]],
                popup=city_data["display_name"],
                tooltip="City Center",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            
            # Color scheme for days
            colors = ["blue", "green", "purple", "orange", "darkred", "lightblue", "darkgreen"]
            
            # Add markers for each place
            for day in itinerary.days:
                color = colors[day.day_index % len(colors)]
                
                for place in day.places:
                    popup_html = f"""
                    <div style="width: 200px">
                        <h4>{place.name}</h4>
                        <p><b>Day {day.day_index}</b></p>
                        <p>{place.category.title()}</p>
                        <p>Cost: ${place.estimated_cost:.0f}/person</p>
                        <p>Time: ~{place.time_needed} min</p>
                    </div>
                    """
                    
                    folium.Marker(
                        [place.latitude, place.longitude],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=f"Day {day.day_index}: {place.name}",
                        icon=folium.Icon(color=color, icon="map-marker", prefix="fa")
                    ).add_to(m)
            
            # Display map
            st_folium(m, width=None, height=600)
            
            # Legend
            st.subheader("Legend")
            legend_cols = st.columns(len(itinerary.days) + 1)
            
            with legend_cols[0]:
                st.markdown("🔴 **City Center**")
            
            for idx, day in enumerate(itinerary.days):
                with legend_cols[idx + 1]:
                    color = colors[day.day_index % len(colors)]
                    color_emoji = {"blue": "🔵", "green": "🟢", "purple": "🟣", 
                                   "orange": "🟠", "darkred": "🔴", "lightblue": "🔵", 
                                   "darkgreen": "🟢"}.get(color, "⚪")
                    st.markdown(f"{color_emoji} **Day {day.day_index}**")
        
        with tab3:
            # Cost breakdown
            st.header("Cost Breakdown")
            
            # Daily costs table
            st.subheader("Daily Costs")
            
            cost_data = []
            for day in itinerary.days:
                cost_data.append({
                    "Day": f"Day {day.day_index}",
                    "Date": day.day_date.strftime("%b %d"),
                    "Places": day.place_count,
                    "Cost": f"${day.total_cost:.2f}"
                })
            
            st.table(cost_data)
            
            # Budget comparison
            st.subheader("Budget Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Budget", f"${itinerary.trip_request.budget:,.2f}")
                st.metric("Estimated Cost", f"${itinerary.total_cost:,.2f}")
                
                remaining = itinerary.budget_remaining
                if remaining >= 0:
                    st.success(f"Remaining: ${remaining:,.2f}")
                else:
                    st.error(f"Over budget by: ${-remaining:,.2f}")
            
            with col2:
                st.metric("Daily Budget", f"${itinerary.trip_request.daily_budget:,.2f}")
                
                avg_daily_cost = itinerary.total_cost / itinerary.num_days
                st.metric("Avg Daily Cost", f"${avg_daily_cost:,.2f}")
                
                if itinerary.trip_request.group_size > 1:
                    cost_per_person = itinerary.total_cost / itinerary.trip_request.group_size
                    st.metric("Cost per Person", f"${cost_per_person:,.2f}")
            
            # Progress bar
            budget_percentage = min(itinerary.budget_used_percentage / 100, 1.0)
            st.progress(budget_percentage)
            
            # Cost categories breakdown
            st.subheader("Estimated Cost Categories")
            
            total_places_cost = sum(
                place.estimated_cost * itinerary.trip_request.group_size
                for day in itinerary.days
                for place in day.places
            )
            
            meals_cost = 40.0 * itinerary.trip_request.group_size * itinerary.num_days
            transport_cost = 15.0 * itinerary.trip_request.group_size * itinerary.num_days
            
            cost_breakdown = {
                "Attractions & Activities": f"${total_places_cost:.2f}",
                "Meals": f"${meals_cost:.2f}",
                "Local Transport": f"${transport_cost:.2f}",
            }
            
            for category, cost in cost_breakdown.items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(category)
                with col2:
                    st.write(cost)


if __name__ == "__main__":
    main()
