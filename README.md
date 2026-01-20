# ✈️ Travel Itinerary Builder (Pydantic AI MVP)

An intelligent travel planning application that generates personalized day-by-day itineraries using **Pydantic AI**, **free APIs**, and **Streamlit**.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-0.0.14-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.40.2-red.svg)

---

## 🎯 Features

### Core Functionality
- **🗺️ Smart Itinerary Generation**: AI-powered day-by-day planning based on your preferences
- **💰 Budget Management**: Automatic cost estimation and budget tracking
- **📍 Interactive Maps**: Visualize your trip with OpenStreetMap markers
- **🎨 Interest Matching**: Filter attractions by museums, nature, food, history, and more
- **⚡ Pace Control**: Choose between relaxed, moderate, or packed schedules
- **👥 Group Support**: Cost calculations for solo travelers or groups

### What You Get
- Day-by-day itinerary with timing and descriptions
- Estimated costs (attractions + meals + transport)
- Interactive map with color-coded day markers
- Place details (hours, ratings, categories)
- Budget vs. actual cost comparison

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this project**
   ```bash
   cd "c:\Users\annan\Downloads\Mr K project"
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   .\venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your OpenAI API key (optional)
   # If not provided, the app uses a rule-based planner
   ```

### Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📖 How to Use

### 1. Enter Trip Details (Sidebar)
- **Destination City**: Enter any city name (e.g., "Paris", "Tokyo", "New York")
- **Dates**: Select your start and end dates
- **Budget**: Set your total budget in USD
- **Group Size**: Number of travelers

### 2. Select Interests
Choose from:
- Museums
- Nature
- Food
- Architecture
- History
- Art
- Shopping
- Entertainment

### 3. Choose Trip Pace
- **Relaxed**: 2-3 places per day
- **Moderate**: 3-4 places per day
- **Packed**: 5-6 places per day

### 4. Generate Itinerary
Click **"🎯 Generate Itinerary"** and wait for:
1. City geocoding
2. POI discovery
3. AI-powered planning

### 5. Explore Your Itinerary
- **📅 Daily Itinerary**: Browse day-by-day plans
- **🗺️ Map View**: See all places on an interactive map
- **💰 Cost Breakdown**: Review budget and expenses

---

## 🏗️ Architecture

### Project Structure
```
Mr K project/
├── app.py              # Streamlit UI
├── models.py           # Pydantic data models
├── api_clients.py      # API integrations
├── agent.py            # Pydantic AI agent
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore file
└── README.md           # This file
```

### Data Flow
```
User Input → Geocoding (Nominatim) → POI Discovery (OpenTripMap)
    ↓
Pydantic AI Agent
    ├─ Rank places by relevance
    ├─ Calculate distances
    ├─ Allocate to days
    └─ Estimate costs
    ↓
Itinerary Output → Streamlit Display
    ├─ Day-by-day cards
    ├─ Interactive map
    └─ Cost summary
```

### Key Components

#### 1. **Pydantic Models** (`models.py`)
- `TripRequest`: User input validation
- `Place`: POI with location and cost
- `DayPlan`: Single day's itinerary
- `Itinerary`: Complete trip plan

#### 2. **API Clients** (`api_clients.py`)
- **Nominatim**: Free geocoding API
- **OpenTripMap**: Free POI discovery API

#### 3. **Pydantic AI Agent** (`agent.py`)
- Ranks places by relevance
- Calculates optimal routes
- Allocates places to days
- Estimates costs
- Falls back to rule-based planning if no API key

#### 4. **Streamlit UI** (`app.py`)
- Input form
- Progress indicators
- Tabbed results view
- Interactive Folium maps

---

## 🔑 API Keys & Configuration

### Required APIs (All FREE - No Setup Needed!)
- ✅ **Nominatim** (Geocoding): No key needed - fully free
- ✅ **OpenTripMap** (POIs): Free key already included in code
- ✅ **OpenStreetMap** (Map tiles): No key needed - open source

### Optional: Google Gemini API Key
For enhanced AI planning, add your Google Gemini API key:

1. **Get a free API key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Create a `.env` file:
   ```bash
   copy .env.example .env
   ```

3. Edit `.env`:
   ```
   GOOGLE_API_KEY=your-actual-gemini-key-here
   ```

**Without Gemini**: The app uses a smart rule-based planner (works great!)

---

## 💡 Example Usage

### Sample Trip
```
City: Paris
Dates: Feb 1 - Feb 4, 2026 (3 days)
Budget: $1,200
Interests: Museums, Food, Architecture
Pace: Moderate
Group Size: 2 people
```

### Result
- **Day 1**: Louvre Museum → Notre-Dame → Seine River Cruise
- **Day 2**: Eiffel Tower → Arc de Triomphe → Champs-Élysées
- **Day 3**: Musée d'Orsay → Montmartre → Sacré-Cœur

**Total Cost**: ~$1,150 (within budget!)

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| **Pydantic AI** | Intelligent itinerary planning with tool calling |
| **Google Gemini** | AI model for smart recommendations (optional) |
| **Pydantic** | Data validation and schema definition |
| **Streamlit** | Web UI framework |
| **Folium** | Interactive maps |
| **Nominatim** | City geocoding (FREE - no key needed) |
| **OpenTripMap** | POI discovery (FREE - key included) |
| **OpenStreetMap** | Map tiles (FREE - no key needed) |

---

## 📝 MVP Scope

### ✅ Included
- Day-by-day itinerary generation
- Budget tracking and cost estimation
- POI discovery with categories
- Interactive map visualization
- Interest-based filtering
- Pace customization
- Group size support

### ❌ Out of Scope (Future Enhancements)
- Real-time routing and travel times
- Hotel recommendations
- Flight booking
- Restaurant reservations
- User accounts and saved trips
- Weather integration
- Real-time pricing

---

## 🐛 Troubleshooting

### Common Issues

**1. Import errors**
```bash
pip install --upgrade -r requirements.txt
```

**2. API timeout**
- Check your internet connection
- Try a different city name
- The OpenTripMap API has rate limits

**3. No places found**
- Try broader interests
- Increase the search radius (edit `api_clients.py`)
- Use a larger city

**4. Streamlit errors**
```bash
streamlit cache clear
streamlit run app.py
```

---

## 🤝 Contributing

This is an MVP project. Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Fork and customize

---

## 📄 License

MIT License - Feel free to use this project for personal or commercial purposes.

---

## 🙏 Acknowledgments

- **Pydantic AI** team for the amazing framework
- **OpenStreetMap** contributors
- **OpenTripMap** for the free POI API
- **Streamlit** for the easy-to-use UI framework

---

## 📧 Support

Having issues? Try these steps:
1. Check the troubleshooting section
2. Review the code comments
3. Test with a simple input (e.g., "Paris", 2 days, $500)
4. Ensure all dependencies are installed

---

## 🎉 Enjoy Your Trip Planning!

Built with ❤️ using **Pydantic AI**

Happy travels! ✈️🌍
