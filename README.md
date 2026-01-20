# ✈️ Travel Itinerary Builder (Pydantic AI MVP)

An intelligent travel planning application that generates personalized day-by-day itineraries using **Pydantic AI**, **free APIs**, and **Streamlit**.

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
   
   # Edit .env and add your gemini key
   # If not provided, the app uses a rule-based planner
   ```

### Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---
