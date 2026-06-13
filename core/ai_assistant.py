"""
AI Safety Assistant - Provides intelligent responses about safety.
Uses rule-based NLP for hackathon MVP. Can be upgraded to Gemini/OpenAI.
"""
import random
from .models import SafeZone, CrimeReport, SafetyReport


def get_ai_response(message, context=None):
    """
    Generate AI response based on user message.
    For hackathon MVP, uses intelligent rule-based responses.
    Can be replaced with Gemini/OpenAI API call.
    """
    message_lower = message.lower().strip()

    # Safety score queries
    if any(word in message_lower for word in ['safety score', 'how safe', 'score', 'rating']):
        return _handle_safety_score_query(message_lower, context)

    # Route safety
    if any(word in message_lower for word in ['route', 'path', 'way', 'direction', 'travel']):
        return _handle_route_query(message_lower, context)

    # Emergency guidance
    if any(word in message_lower for word in ['emergency', 'help', 'sos', 'danger', 'unsafe', 'scared']):
        return _handle_emergency_query(message_lower)

    # Time-based recommendations
    if any(word in message_lower for word in ['night', 'late', 'dark', 'evening', 'morning', 'time']):
        return _handle_time_query(message_lower)

    # Nearby places
    if any(word in message_lower for word in ['nearby', 'nearest', 'close', 'police', 'hospital', 'pharmacy']):
        return _handle_nearby_query(message_lower, context)

    # Safety tips
    if any(word in message_lower for word in ['tip', 'advice', 'suggest', 'recommend', 'precaution']):
        return _handle_tips_query(message_lower)

    # Reporting
    if any(word in message_lower for word in ['report', 'complaint', 'harassment', 'stalking']):
        return _handle_report_query(message_lower)

    # General greeting
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'assalam', 'salam']):
        return _handle_greeting()

    # About SafePath
    if any(word in message_lower for word in ['what', 'who', 'safepath', 'about', 'feature']):
        return _handle_about_query(message_lower)

    # Default intelligent response
    return _handle_default(message_lower)


def _handle_safety_score_query(message, context):
    responses = [
        "Safety scores in SafePath AI range from 0-100, calculated using multiple factors:\n\n"
        "🔴 **Crime Reports (40%)** - Historical crime data in the area\n"
        "👥 **Community Reports (20%)** - User-submitted safety reports\n"
        "💡 **Street Lighting (15%)** - Quality of lighting on the route\n"
        "🚶 **Crowd Density (15%)** - Expected foot traffic\n"
        "🕐 **Time of Day (10%)** - Day vs night adjustments\n\n"
        "**Risk Levels:**\n"
        "- 🟢 70-100: Low Risk (Safe)\n"
        "- 🟡 45-69: Medium Risk (Caution)\n"
        "- 🔴 0-44: High Risk (Avoid if possible)\n\n"
        "Use the Route Planner to see safety scores for specific routes!",

        "The safety score tells you how safe an area or route is on a scale of 0-100. "
        "Higher scores mean safer conditions. The score considers crime history, lighting, "
        "crowd presence, community reports, and time of day. "
        "A score above 70 is generally safe, 45-70 requires caution, and below 45 suggests avoiding the area.",
    ]
    return random.choice(responses)


def _handle_route_query(message, context):
    responses = [
        "For the safest route, I recommend:\n\n"
        "1. **Use the Route Planner** - Enter your source and destination\n"
        "2. **Check all 3 options** - Shortest, Fastest, and Safest routes\n"
        "3. **Choose the Safest Route** (marked with ★) even if slightly longer\n"
        "4. **Start a Journey** to enable live tracking and check-ins\n\n"
        "💡 Tips for route selection:\n"
        "- At night, prioritize well-lit routes over shorter ones\n"
        "- Check for nearby safe zones along the route\n"
        "- Share your tracking link with trusted contacts\n"
        "- Set up check-in timers for longer journeys",

        "When choosing a route, always consider:\n\n"
        "- **Safety Score** - Higher is better\n"
        "- **Lighting** - Especially important at night\n"
        "- **Crowd Density** - More people = generally safer\n"
        "- **Safe Zones Nearby** - Police stations, hospitals along the way\n\n"
        "The recommended safest route may be slightly longer but keeps you away from "
        "crime hotspots and near safe zones. You can start a tracked journey for real-time monitoring.",
    ]
    return random.choice(responses)


def _handle_emergency_query(message):
    return (
        "🚨 **EMERGENCY GUIDANCE:**\n\n"
        "**If you are in immediate danger:**\n"
        "1. Press the **SOS Button** - it alerts all your trusted contacts\n"
        "2. Call **Police: 15** immediately\n"
        "3. Call **Rescue 1122** for emergency services\n\n"
        "**Pakistan Emergency Numbers:**\n"
        "- 🚔 Police: **15**\n"
        "- 🚑 Rescue: **1122**\n"
        "- 👩 Women Helpline: **1043**\n"
        "- 🏥 Edhi Foundation: **115**\n"
        "- 🚒 Fire: **16**\n\n"
        "**Quick Actions:**\n"
        "- Use the SOS feature to alert contacts with your location\n"
        "- Head toward the nearest safe zone (police station, hospital)\n"
        "- Make noise to attract attention\n"
        "- If being followed, enter a busy shop or public area\n\n"
        "Stay calm and remember - your safety comes first. Don't hesitate to call for help."
    )


def _handle_time_query(message):
    if any(word in message for word in ['night', 'late', 'dark', 'evening']):
        return (
            "🌙 **Night Travel Safety Recommendations:**\n\n"
            "1. **Always use SafePath's route planner** - Night scores differ significantly\n"
            "2. **Start a tracked journey** with check-in timer (every 15 min)\n"
            "3. **Share tracking link** with at least 2 trusted contacts\n"
            "4. **Stay on well-lit main roads** even if the route is longer\n"
            "5. **Avoid isolated areas** - parks, underpasses, empty lanes\n"
            "6. **Keep emergency numbers ready** - Police 15, Rescue 1122\n"
            "7. **Don't use headphones** - stay alert to surroundings\n"
            "8. **Travel with companion** if possible\n\n"
            "⚠️ Safety scores drop 20-40% at night. A score of 70 during day "
            "might become 45 at night. Plan accordingly!"
        )
    return (
        "🌞 **Best Travel Times:**\n\n"
        "- **Safest:** 8 AM - 6 PM (daylight hours)\n"
        "- **Moderate:** 6 PM - 9 PM (evening, still some activity)\n"
        "- **Higher Risk:** 9 PM - 6 AM (limited visibility, fewer people)\n\n"
        "If you must travel late, always:\n"
        "- Use tracked journey feature\n"
        "- Set check-in timers\n"
        "- Choose safest route option\n"
        "- Keep trusted contacts informed"
    )


def _handle_nearby_query(message, context):
    # Get actual counts from database
    try:
        police_count = SafeZone.objects.filter(zone_type='police', is_active=True).count()
        hospital_count = SafeZone.objects.filter(zone_type='hospital', is_active=True).count()
    except Exception:
        police_count = 0
        hospital_count = 0

    return (
        f"📍 **Nearby Safe Places:**\n\n"
        f"SafePath has mapped **{police_count} police stations** and **{hospital_count} hospitals** "
        f"in the Lahore area.\n\n"
        "To find the nearest safe place:\n"
        "1. Go to **Nearby Safe Places** page\n"
        "2. Allow location access\n"
        "3. Filter by type (police, hospital, pharmacy, transit)\n"
        "4. Click any marker for directions\n\n"
        "**Quick access in emergencies:**\n"
        "- The SOS page shows nearest emergency services\n"
        "- Route planner shows safe zones along your path\n"
        "- Journey tracking page displays nearby safe places\n\n"
        "You can also use the API: `/api/nearby-places/?lat=31.55&lng=74.34`"
    )


def _handle_tips_query(message):
    tips = [
        "🛡️ **Top Safety Tips for Women in Pakistan:**\n\n"
        "**Before Traveling:**\n"
        "- Plan your route using SafePath AI\n"
        "- Share your plan with trusted contacts\n"
        "- Keep your phone fully charged\n"
        "- Save emergency numbers on speed dial\n\n"
        "**During Travel:**\n"
        "- Start a tracked journey in SafePath\n"
        "- Set check-in timers (15/30/60 min)\n"
        "- Stay on well-populated streets\n"
        "- Avoid using phone while walking\n"
        "- Keep valuables hidden\n\n"
        "**In Public Transport:**\n"
        "- Note vehicle number before boarding\n"
        "- Share ride details with family\n"
        "- Sit near other women or the driver\n"
        "- Avoid empty buses/compartments at night\n\n"
        "**Digital Safety:**\n"
        "- Enable SafePath SOS feature\n"
        "- Keep location sharing on with family\n"
        "- Learn your phone's emergency SOS shortcut",
    ]
    return random.choice(tips)


def _handle_report_query(message):
    return (
        "📝 **How to Report Safety Concerns:**\n\n"
        "**In SafePath App:**\n"
        "1. Go to **Community Reports** > **Submit Report**\n"
        "2. Select report type:\n"
        "   - 🚨 Harassment\n"
        "   - 👁️ Stalking\n"
        "   - ⚠️ Unsafe Area\n"
        "   - 💡 Broken Streetlight\n"
        "   - 🚧 Unsafe Road\n"
        "   - 👤 Suspicious Activity\n"
        "3. Add severity level and location\n"
        "4. Describe what happened\n\n"
        "**For Official Complaints:**\n"
        "- Police: Call **15** or visit nearest station\n"
        "- Women Helpline: **1043**\n"
        "- Punjab Safe Cities: **0800-00-786**\n"
        "- Pakistan Citizen Portal: File online complaint\n\n"
        "Your reports help improve safety scores and warn other users!"
    )


def _handle_greeting():
    greetings = [
        "Assalam o Alaikum! 👋 I'm your SafePath AI Safety Assistant. "
        "I can help you with:\n\n"
        "- 🗺️ Route safety questions\n"
        "- 📊 Safety score explanations\n"
        "- 🚨 Emergency guidance\n"
        "- 💡 Safety tips\n"
        "- 📍 Finding nearby safe places\n"
        "- ⏰ Best travel time recommendations\n\n"
        "How can I help you stay safe today?",

        "Hello! I'm SafePath AI Assistant. I'm here to help with your safety. "
        "Ask me about routes, safety scores, emergency procedures, or safety tips. "
        "What would you like to know?",
    ]
    return random.choice(greetings)


def _handle_about_query(message):
    return (
        "🛡️ **About SafePath AI:**\n\n"
        "SafePath AI is a Women Safety Route Assistant that helps you travel safely.\n\n"
        "**Key Features:**\n"
        "- 🗺️ AI-powered safe route recommendations\n"
        "- 📊 Real-time safety scores (0-100)\n"
        "- 📍 Live journey tracking\n"
        "- 🚨 SOS emergency button\n"
        "- 👥 Trusted contacts system\n"
        "- ⏰ Check-in timers\n"
        "- 🔔 Arrival confirmation\n"
        "- 📝 Community safety reports\n"
        "- 🤖 AI safety assistant (that's me!)\n"
        "- 🗺️ Nearby safe places finder\n\n"
        "**How it works:**\n"
        "Our AI analyzes crime data, street lighting, crowd density, "
        "and community reports to calculate safety scores and recommend "
        "the safest routes for your journey."
    )


def _handle_default(message):
    return (
        "I understand you're asking about safety. Here's how I can help:\n\n"
        "- Ask about **safety scores** - \"How is my area's safety score?\"\n"
        "- Ask about **routes** - \"What's the safest route at night?\"\n"
        "- Ask about **emergencies** - \"What do I do in an emergency?\"\n"
        "- Ask about **tips** - \"Give me safety tips for night travel\"\n"
        "- Ask about **nearby places** - \"Where is the nearest police station?\"\n"
        "- Ask about **reporting** - \"How do I report harassment?\"\n\n"
        "Feel free to ask anything related to your safety!"
    )
