from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# initialise the Groq client with our API key
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Groq client only initialises when an AI endpoint is actually called, not at startup
client = None

def get_client():
    global client
    if client is None:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return client

def interpret_mood(analytics_data: dict) -> str:
    """
    Takes pre-computed analytics from our own endpoints and asks
    Llama 3 to interpret them in natural language.
    """
    username = analytics_data.get('username', 'you') #  making the result more personalised

    # build a structured prompt from our analytics data
    
    prompt = f"""
    You are a music psychology analyst speaking directly to {username}.
    Address them as "you" throughout — never say "this person".
    Be warm, personal and conversational.

    {username}'s listening analytics:
    - Overall mood score: {analytics_data.get('overall_mood_score')} (0=very negative, 1=very positive)
    - Dominant emotion: {analytics_data.get('dominant_emotion')}
    - Most listened genre: {analytics_data.get('top_genre')}
    - Favourite context: {analytics_data.get('favourite_context')}
    - Average energy level: {analytics_data.get('avg_energy')}
    - Average danceability: {analytics_data.get('avg_danceability')}
    - Total sessions analysed: {analytics_data.get('total_sessions')}
    - Top track: "{analytics_data.get('top_track_title')}" by {analytics_data.get('top_track_artist')}

    Please provide:
    1. A 2-3 sentence personal interpretation of their mood-linked listening pattern
    2. What their favourite context suggests about how they use music
    3. One personal insight about their top track choice

    Important: Speak directly to {username} using "you" and "your".
    Non-clinical, warm and concise. No bullet numbers — write in flowing paragraphs.
    Keep it under 150 words total.
    """

    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",  # groq's free model
            messages=[
                {
                    "role": "system",
                    "content": "You are a thoughtful music psychology analyst who provides warm, non-clinical reflective insights about listening patterns. You never make medical or diagnostic claims."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=250,   # keep responses concise
            temperature=0.7   # slight creativity but still grounded
        )
        return response.choices[0].message.content

    except Exception as e:
        # graceful fallback if Groq API is unavailable
        return generate_fallback_interpretation(analytics_data)


def generate_fallback_interpretation(analytics_data: dict) -> str:
    """
    Fallback interpretation if the AI API is unavailable.
    Ensures the endpoint always returns a valid response.
    """
    mood_score = analytics_data.get('overall_mood_score', 0.5)
    emotion = analytics_data.get('dominant_emotion', 'Calm')
    context = analytics_data.get('favourite_context', 'various contexts')
    top_track = analytics_data.get('top_track_title', 'Unknown')

    if mood_score >= 0.6:
        mood_desc = "generally positive and uplifting"
    elif mood_score >= 0.4:
        mood_desc = "balanced and reflective"
    else:
        mood_desc = "introspective and emotionally complex"

    return (
        f"Your listening patterns suggest a {mood_desc} musical taste, "
        f"with a dominant emotional tone of {emotion.lower()}. "
        f"You most frequently listen to music while {context}, suggesting music plays "
        f"an important role in that part of your daily routine. "
        f"Your top track '{top_track}' reflects your current listening mood. "
        f"(Note: AI interpretation temporarily unavailable — this is a rule-based summary.)"
    )


def recommend_context(analytics_data: dict) -> str:
    """
    Takes a user's mood analytics and recommends the best context
    for listening based on their current emotional patterns.
    """

    prompt = f"""
    You are a music and wellbeing advisor. Based on someone's current listening mood analytics,
    suggest the most beneficial context for them to listen to music in right now.

    Current Mood Analytics:
    - Overall mood score: {analytics_data.get('overall_mood_score')} (0=very negative, 1=very positive)
    - Dominant emotion: {analytics_data.get('dominant_emotion')}
    - Average energy of listened tracks: {analytics_data.get('avg_energy')}
    - Most common listening context: {analytics_data.get('favourite_context')}

    Available contexts: working, commuting, exercising, relaxing, socialising, sleeping

    Provide:
    1. Your recommended context (one word from the list above)
    2. A 2 sentence explanation of why this context suits their current mood patterns
    3. A suggestion for what kind of track energy would complement this context

    Keep it concise, warm and practical. Non-clinical only.
    """

    try:
        response = get_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a warm, practical music and wellbeing advisor. You give concise, non-clinical suggestions about music listening habits."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        # fallback if API unavailable
        mood_score = analytics_data.get('overall_mood_score', 0.5)
        if mood_score < 0.4:
            return "Recommended context: relaxing. Your listening patterns suggest you may benefit from calm, low-energy music in a relaxed setting."
        elif mood_score > 0.6:
            return "Recommended context: exercising. Your positive mood patterns align well with high-energy physical activity."
        else:
            return "Recommended context: working. Your balanced listening patterns suggest music works well as a focus aid for you."