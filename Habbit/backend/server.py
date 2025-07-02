from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
import json
from openai import OpenAI
import logging
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="HabitVerse API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "habitverse")

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Pydantic models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    avatar_level: int = 1
    total_xp: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    world_type: str = "forest"  # forest, city, fantasy
    avatar_customization: Dict[str, Any] = Field(default_factory=lambda: {
        "color": "#90EE90",
        "accessories": [],
        "background": "forest"
    })
    achievements: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Habit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: str
    category: str  # fitness, focus, sleep, wellness, productivity
    difficulty: int  # 1-5 scale
    xp_reward: int = 10
    is_active: bool = True
    target_frequency: str = "daily"  # daily, weekly
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HabitCompletionRequest(BaseModel):
    user_id: str
    habit_id: str
    mood_rating: Optional[int] = 4
    energy_level: Optional[int] = 4
    notes: Optional[str] = None

class HabitCompletion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    habit_id: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    xp_earned: int
    mood_rating: Optional[int] = None  # 1-5 scale
    energy_level: Optional[int] = None  # 1-5 scale
    notes: Optional[str] = None

class MoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood_rating: int  # 1-5 scale
    energy_level: int  # 1-5 scale
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    requirement: Dict[str, Any]
    reward_xp: int = 0

class AIMessage(BaseModel):
    message: str
    message_type: str  # encouragement, suggestion, coaching, quest

# Helper functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB's _id field
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

def calculate_level(xp: int) -> int:
    """Calculate user level based on XP"""
    return min(50, max(1, int((xp / 100) ** 0.5) + 1))

def get_avatar_evolution(level: int) -> Dict[str, Any]:
    """Get avatar appearance based on level"""
    evolutions = {
        1: {"stage": "Seedling", "color": "#90EE90", "size": "small", "emoji": "🌱"},
        5: {"stage": "Sprout", "color": "#32CD32", "size": "medium", "emoji": "🌿"},
        10: {"stage": "Young Tree", "color": "#228B22", "size": "large", "emoji": "🌳"},
        20: {"stage": "Mature Tree", "color": "#006400", "size": "xl", "emoji": "🌲"},
        30: {"stage": "Ancient Tree", "color": "#8B4513", "size": "2xl", "emoji": "🌴"},
        40: {"stage": "Magical Tree", "color": "#FFD700", "size": "3xl", "emoji": "✨🌳"},
        50: {"stage": "Legendary Tree", "color": "#FF6347", "size": "4xl", "emoji": "🏆🌳"}
    }
    
    current_stage = evolutions[1]
    for level_threshold in sorted(evolutions.keys(), reverse=True):
        if level >= level_threshold:
            current_stage = evolutions[level_threshold]
            break
    
    return current_stage

def get_available_achievements() -> List[Achievement]:
    """Get all available achievements"""
    return [
        Achievement(
            id="first_habit",
            name="Baby Steps",
            description="Complete your first habit",
            icon="👶",
            requirement={"type": "habit_completions", "count": 1},
            reward_xp=50
        ),
        Achievement(
            id="week_warrior",
            name="Week Warrior",
            description="Maintain a 7-day streak",
            icon="⚔️",
            requirement={"type": "streak", "count": 7},
            reward_xp=100
        ),
        Achievement(
            id="habit_collector",
            name="Habit Collector",
            description="Create 5 different habits",
            icon="📋",
            requirement={"type": "habit_count", "count": 5},
            reward_xp=75
        ),
        Achievement(
            id="xp_master",
            name="XP Master",
            description="Earn 500 total XP",
            icon="⭐",
            requirement={"type": "total_xp", "count": 500},
            reward_xp=100
        ),
        Achievement(
            id="consistency_king",
            name="Consistency King",
            description="Complete 30 habits total",
            icon="👑",
            requirement={"type": "habit_completions", "count": 30},
            reward_xp=200
        ),
        Achievement(
            id="mood_tracker",
            name="Mood Tracker",
            description="Log your mood 10 times",
            icon="😊",
            requirement={"type": "mood_entries", "count": 10},
            reward_xp=50
        ),
        Achievement(
            id="level_up",
            name="Level Up Legend",
            description="Reach level 10",
            icon="🚀",
            requirement={"type": "level", "count": 10},
            reward_xp=150
        )
    ]

async def check_achievements(user_id: str):
    """Check and award new achievements for user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return []
    
    user = serialize_doc(user)
    current_achievements = user.get("achievements", [])
    available_achievements = get_available_achievements()
    new_achievements = []
    
    # Get user stats
    habits_count = await db.habits.count_documents({"user_id": user_id, "is_active": True})
    completions_count = await db.habit_completions.count_documents({"user_id": user_id})
    mood_entries_count = await db.mood_entries.count_documents({"user_id": user_id})
    current_level = calculate_level(user["total_xp"])
    
    for achievement in available_achievements:
        if achievement.id in current_achievements:
            continue
            
        req = achievement.requirement
        earned = False
        
        if req["type"] == "habit_completions" and completions_count >= req["count"]:
            earned = True
        elif req["type"] == "streak" and user["current_streak"] >= req["count"]:
            earned = True
        elif req["type"] == "habit_count" and habits_count >= req["count"]:
            earned = True
        elif req["type"] == "total_xp" and user["total_xp"] >= req["count"]:
            earned = True
        elif req["type"] == "mood_entries" and mood_entries_count >= req["count"]:
            earned = True
        elif req["type"] == "level" and current_level >= req["count"]:
            earned = True
        
        if earned:
            new_achievements.append(achievement)
            current_achievements.append(achievement.id)
            
            # Award XP bonus
            if achievement.reward_xp > 0:
                await db.users.update_one(
                    {"id": user_id},
                    {"$inc": {"total_xp": achievement.reward_xp}}
                )
    
    # Update user achievements
    if new_achievements:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"achievements": current_achievements}}
        )
    
    return new_achievements

async def get_ai_suggestion(user_data: Dict, habit_data: List[Dict], mood_data: List[Dict]) -> str:
    """Get AI-powered habit suggestions and coaching"""
    if not openai_client:
        return "Keep up the great work! Your consistency is building a stronger you every day! 🌟"
    
    try:
        # Prepare context for AI
        context = f"""
        User Profile:
        - Level: {calculate_level(user_data.get('total_xp', 0))}
        - Total XP: {user_data.get('total_xp', 0)}
        - Current Streak: {user_data.get('current_streak', 0)}
        - Habits: {len(habit_data)} active habits
        - Achievements: {len(user_data.get('achievements', []))}
        
        Recent Habits: {', '.join([h.get('name', '') for h in habit_data[:3]])}
        
        Recent Mood: {mood_data[0].get('mood_rating', 3) if mood_data else 3}/5
        """
        
        prompt = f"""You are a supportive AI coach for HabitVerse, a gamified habit-building app. 
        
        User Context: {context}
        
        Provide a personalized, encouraging message (max 2 sentences) that:
        1. Acknowledges their progress
        2. Offers gentle motivation or a specific tip
        3. Uses gamification language (XP, level up, quest, etc.)
        4. Keeps it positive and engaging
        
        Make it feel like a friendly companion, not a formal coach."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"AI suggestion error: {e}")
        return "You're doing amazing! Every small step counts toward your bigger goals! 🚀"

async def generate_habit_suggestions(user_interests: List[str], current_habits: List[str]) -> List[Dict]:
    """Generate AI-powered habit suggestions"""
    if not openai_client:
        return [
            {"name": "Morning Meditation", "description": "Start your day with 5 minutes of mindfulness", "category": "wellness"},
            {"name": "Evening Walk", "description": "Take a 15-minute walk to unwind", "category": "fitness"},
            {"name": "Gratitude Journal", "description": "Write down 3 things you're grateful for", "category": "wellness"}
        ]
    
    try:
        prompt = f"""Generate 3 personalized habit suggestions for a user with these interests: {', '.join(user_interests)}
        
        They already have these habits: {', '.join(current_habits)}
        
        Return ONLY a JSON array with this format:
        [
            {{"name": "Habit Name", "description": "Brief description", "category": "fitness|focus|sleep|wellness|productivity"}},
            {{"name": "Habit Name", "description": "Brief description", "category": "fitness|focus|sleep|wellness|productivity"}},
            {{"name": "Habit Name", "description": "Brief description", "category": "fitness|focus|sleep|wellness|productivity"}}
        ]
        
        Make habits specific, achievable, and different from existing ones."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.8
        )
        
        suggestions = json.loads(response.choices[0].message.content.strip())
        return suggestions
    
    except Exception as e:
        logger.error(f"Habit suggestion error: {e}")
        return [
            {"name": "Power Walk", "description": "Take a brisk 10-minute walk", "category": "fitness"},
            {"name": "Digital Detox", "description": "30 minutes without screens", "category": "wellness"},
            {"name": "Learning Sprint", "description": "Read for 15 minutes", "category": "productivity"}
        ]

async def get_analytics_data(user_id: str) -> Dict[str, Any]:
    """Get comprehensive analytics data for user"""
    # Get completions from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    completions_cursor = db.habit_completions.find({
        "user_id": user_id,
        "completed_at": {"$gte": thirty_days_ago}
    }).sort("completed_at", 1)
    
    completions = await completions_cursor.to_list(None)
    completions = serialize_doc(completions)
    
    # Get mood entries from last 30 days
    mood_cursor = db.mood_entries.find({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago}
    }).sort("created_at", 1)
    
    mood_entries = await mood_cursor.to_list(None)
    mood_entries = serialize_doc(mood_entries)
    
    # Prepare daily data
    daily_data = {}
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).strftime("%Y-%m-%d")
        daily_data[date] = {
            "date": date,
            "completions": 0,
            "xp_earned": 0,
            "mood": None,
            "energy": None
        }
    
    # Fill in completion data
    for completion in completions:
        try:
            # Handle different datetime formats
            if isinstance(completion["completed_at"], str):
                if "T" in completion["completed_at"]:
                    date = completion["completed_at"].split("T")[0]
                else:
                    date = completion["completed_at"][:10]
            else:
                date = completion["completed_at"].strftime("%Y-%m-%d")
            
            if date in daily_data:
                daily_data[date]["completions"] += 1
                daily_data[date]["xp_earned"] += completion.get("xp_earned", 0)
        except Exception as e:
            logger.error(f"Error processing completion date: {e}")
            continue
    
    # Fill in mood data
    for mood in mood_entries:
        try:
            if isinstance(mood["created_at"], str):
                if "T" in mood["created_at"]:
                    date = mood["created_at"].split("T")[0]
                else:
                    date = mood["created_at"][:10]
            else:
                date = mood["created_at"].strftime("%Y-%m-%d")
            
            if date in daily_data:
                daily_data[date]["mood"] = mood["mood_rating"]
                daily_data[date]["energy"] = mood["energy_level"]
        except Exception as e:
            logger.error(f"Error processing mood date: {e}")
            continue
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    for date in sorted(daily_data.keys()):
        if daily_data[date]["completions"] > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0
    
    # Calculate current streak (from today backwards)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in daily_data and daily_data[date]["completions"] > 0:
            current_streak += 1
        else:
            break
    
    return {
        "daily_data": list(daily_data.values()),
        "total_completions": len(completions),
        "total_xp": sum(c.get("xp_earned", 0) for c in completions),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "avg_mood": sum(m["mood_rating"] for m in mood_entries) / len(mood_entries) if mood_entries else 3,
        "avg_energy": sum(m["energy_level"] for m in mood_entries) / len(mood_entries) if mood_entries else 3
    }

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "HabitVerse API is running"}

@app.post("/api/users")
async def create_user(user: User):
    """Create a new user"""
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    return serialize_doc(user_dict)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user profile"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = serialize_doc(user)
    
    # Calculate current level
    user["current_level"] = calculate_level(user["total_xp"])
    user["avatar_evolution"] = get_avatar_evolution(user["current_level"])
    
    # Get XP needed for next level
    next_level_xp = ((user["current_level"]) ** 2) * 100
    user["xp_to_next_level"] = max(0, next_level_xp - user["total_xp"])
    
    return user

@app.post("/api/habits")
async def create_habit(habit: Habit):
    """Create a new habit"""
    habit_dict = habit.dict()
    habit_dict["xp_reward"] = habit.difficulty * 10  # XP based on difficulty
    await db.habits.insert_one(habit_dict)
    return serialize_doc(habit_dict)

@app.get("/api/habits/{user_id}")
async def get_user_habits(user_id: str):
    """Get all habits for a user"""
    habits_cursor = db.habits.find({"user_id": user_id, "is_active": True})
    habits = await habits_cursor.to_list(None)
    habits = serialize_doc(habits)
    
    # Add completion stats for today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    for habit in habits:
        completion = await db.habit_completions.find_one({
            "user_id": user_id,
            "habit_id": habit["id"],
            "completed_at": {"$gte": today}
        })
        habit["completed_today"] = completion is not None
    
    return habits

@app.post("/api/habits/{habit_id}/complete")
async def complete_habit(habit_id: str, request: HabitCompletionRequest):
    """Mark a habit as completed"""
    # Get habit details
    habit = await db.habits.find_one({"id": habit_id})
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Check if already completed today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing = await db.habit_completions.find_one({
        "user_id": request.user_id,
        "habit_id": habit_id,
        "completed_at": {"$gte": today}
    })
    
    if existing:
        return {"message": "Habit already completed today", "xp_earned": 0}
    
    # Create completion record
    completion = HabitCompletion(
        user_id=request.user_id,
        habit_id=habit_id,
        xp_earned=habit["xp_reward"],
        mood_rating=request.mood_rating,
        energy_level=request.energy_level,
        notes=request.notes
    )
    
    # Record completion
    completion_dict = completion.dict()
    await db.habit_completions.insert_one(completion_dict)
    
    # Update user XP and streak
    user = await db.users.find_one({"id": request.user_id})
    if user:
        new_xp = user["total_xp"] + completion.xp_earned
        
        # Calculate streak
        yesterday = today - timedelta(days=1)
        yesterday_completion = await db.habit_completions.find_one({
            "user_id": request.user_id,
            "completed_at": {"$gte": yesterday, "$lt": today}
        })
        
        if yesterday_completion:
            new_streak = user["current_streak"] + 1
        else:
            new_streak = 1
        
        # Update user
        await db.users.update_one(
            {"id": request.user_id},
            {
                "$set": {
                    "total_xp": new_xp,
                    "current_streak": new_streak,
                    "longest_streak": max(user["longest_streak"], new_streak)
                }
            }
        )
        
        # Check for level up
        old_level = calculate_level(user["total_xp"])
        new_level = calculate_level(new_xp)
        level_up = new_level > old_level
        
        # Check for new achievements
        new_achievements = await check_achievements(request.user_id)
        
        return {
            "message": "Habit completed successfully!",
            "xp_earned": completion.xp_earned,
            "total_xp": new_xp,
            "current_level": new_level,
            "level_up": level_up,
            "current_streak": new_streak,
            "new_achievements": [{"name": a.name, "description": a.description, "icon": a.icon} for a in new_achievements]
        }
    
    return {"message": "Habit completed!", "xp_earned": completion.xp_earned}

@app.post("/api/mood")
async def log_mood(mood: MoodEntry):
    """Log daily mood and energy"""
    mood_dict = mood.dict()
    await db.mood_entries.insert_one(mood_dict)
    
    # Check for mood tracking achievement
    new_achievements = await check_achievements(mood.user_id)
    
    return {
        **serialize_doc(mood_dict),
        "new_achievements": [{"name": a.name, "description": a.description, "icon": a.icon} for a in new_achievements]
    }

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    """Get dashboard data for user"""
    # Get user data
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = serialize_doc(user)
    
    # Get habits
    habits_cursor = db.habits.find({"user_id": user_id, "is_active": True})
    habits = await habits_cursor.to_list(None)
    habits = serialize_doc(habits)
    
    # Get recent mood data
    mood_cursor = db.mood_entries.find({"user_id": user_id}).sort("created_at", -1).limit(7)
    mood_data = await mood_cursor.to_list(None)
    mood_data = serialize_doc(mood_data)
    
    # Get today's completions
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completions_cursor = db.habit_completions.find({
        "user_id": user_id,
        "completed_at": {"$gte": today}
    })
    today_completions = await completions_cursor.to_list(None)
    today_completions = serialize_doc(today_completions)
    
    # Calculate stats
    current_level = calculate_level(user["total_xp"])
    avatar_evolution = get_avatar_evolution(current_level)
    
    # Get AI coaching message
    ai_message = await get_ai_suggestion(user, habits, mood_data)
    
    # Generate daily quest
    incomplete_habits = [h for h in habits if not any(c["habit_id"] == h["id"] for c in today_completions)]
    daily_quest = None
    if incomplete_habits:
        quest_habit = incomplete_habits[0]  # Simple: pick first incomplete habit
        daily_quest = {
            "title": f"Complete {quest_habit['name']}",
            "description": f"Earn {quest_habit['xp_reward']} XP by completing this habit",
            "xp_reward": quest_habit["xp_reward"],
            "habit_id": quest_habit["id"]
        }
    
    # Get achievements
    all_achievements = get_available_achievements()
    user_achievements = user.get("achievements", [])
    unlocked_achievements = [a for a in all_achievements if a.id in user_achievements]
    
    return {
        "user": {
            **user,
            "current_level": current_level,
            "avatar_evolution": avatar_evolution,
            "xp_to_next_level": max(0, ((current_level) ** 2) * 100 - user["total_xp"])
        },
        "habits": habits,
        "today_completions": len(today_completions),
        "total_habits": len(habits),
        "completion_rate": len(today_completions) / len(habits) * 100 if habits else 0,
        "ai_message": ai_message,
        "daily_quest": daily_quest,
        "recent_mood": mood_data[0] if mood_data else None,
        "achievements": [{"id": a.id, "name": a.name, "description": a.description, "icon": a.icon} for a in unlocked_achievements]
    }

@app.get("/api/suggestions/{user_id}")
async def get_habit_suggestions(user_id: str):
    """Get AI-powered habit suggestions"""
    # Get user's current habits
    habits_cursor = db.habits.find({"user_id": user_id, "is_active": True})
    habits = await habits_cursor.to_list(None)
    habits = serialize_doc(habits)
    current_habits = [h["name"] for h in habits]
    
    # Get user interests from habit categories
    categories = list(set([h["category"] for h in habits]))
    if not categories:
        categories = ["wellness", "fitness", "productivity"]
    
    suggestions = await generate_habit_suggestions(categories, current_habits)
    return {"suggestions": suggestions}

@app.get("/api/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get detailed user statistics"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = serialize_doc(user)
    
    # Get completion history
    completions_cursor = db.habit_completions.find({"user_id": user_id}).sort("completed_at", -1).limit(30)
    completions = await completions_cursor.to_list(None)
    completions = serialize_doc(completions)
    
    # Calculate weekly progress
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_completions = [c for c in completions if datetime.fromisoformat(c["completed_at"].replace('Z', '+00:00')) >= week_ago]
    
    # Get mood trends
    mood_cursor = db.mood_entries.find({"user_id": user_id}).sort("created_at", -1).limit(14)
    mood_data = await mood_cursor.to_list(None)
    mood_data = serialize_doc(mood_data)
    
    return {
        "total_habits_completed": len(completions),
        "week_completions": len(week_completions),
        "current_level": calculate_level(user["total_xp"]),
        "avatar_evolution": get_avatar_evolution(calculate_level(user["total_xp"])),
        "mood_trend": [m["mood_rating"] for m in mood_data[:7]],
        "energy_trend": [m["energy_level"] for m in mood_data[:7]]
    }

@app.get("/api/analytics/{user_id}")
async def get_analytics(user_id: str):
    """Get comprehensive analytics data"""
    analytics_data = await get_analytics_data(user_id)
    return analytics_data

@app.get("/api/achievements")
async def get_all_achievements():
    """Get all available achievements"""
    achievements = get_available_achievements()
    return {"achievements": [{"id": a.id, "name": a.name, "description": a.description, "icon": a.icon, "reward_xp": a.reward_xp} for a in achievements]}

@app.get("/api/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    """Get user's achievements status"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = serialize_doc(user)
    all_achievements = get_available_achievements()
    user_achievements = user.get("achievements", [])
    
    achievements_status = []
    for achievement in all_achievements:
        achievements_status.append({
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "icon": achievement.icon,
            "reward_xp": achievement.reward_xp,
            "unlocked": achievement.id in user_achievements,
            "requirement": achievement.requirement
        })
    
    return {"achievements": achievements_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)