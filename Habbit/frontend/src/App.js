import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [habits, setHabits] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [newHabit, setNewHabit] = useState({
    name: '',
    description: '',
    category: 'wellness',
    difficulty: 1
  });
  const [suggestions, setSuggestions] = useState([]);
  const [showNewHabitForm, setShowNewHabitForm] = useState(false);
  const [moodEntry, setMoodEntry] = useState({ mood_rating: 3, energy_level: 3, notes: '' });
  const [notifications, setNotifications] = useState([]);

  // Initialize demo user
  useEffect(() => {
    initializeDemoUser();
  }, []);

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 4000);
  };

  const initializeDemoUser = async () => {
    try {
      const demoUserId = 'demo-user-123';
      
      // Try to get existing user
      let userData;
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/${demoUserId}`);
        if (response.ok) {
          userData = await response.json();
        }
      } catch (error) {
        console.log('Creating new demo user...');
      }

      // Create demo user if doesn't exist
      if (!userData) {
        const newUser = {
          id: demoUserId,
          username: 'HabitHero',
          email: 'demo@habitverse.com',
          avatar_level: 1,
          total_xp: 0,
          current_streak: 0,
          longest_streak: 0,
          world_type: 'forest',
          achievements: []
        };

        const response = await fetch(`${API_BASE_URL}/api/users`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newUser)
        });

        if (response.ok) {
          userData = await response.json();
        }
      }

      setUser(userData);
      await loadDashboard(demoUserId);
      await loadHabits(demoUserId);
      await loadAchievements(demoUserId);
    } catch (error) {
      console.error('Error initializing user:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const loadHabits = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/habits/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setHabits(data);
      }
    } catch (error) {
      console.error('Error loading habits:', error);
    }
  };

  const loadAnalytics = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const loadAchievements = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/achievements/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setAchievements(data.achievements);
      }
    } catch (error) {
      console.error('Error loading achievements:', error);
    }
  };

  const completeHabit = async (habitId) => {
    try {
      const completion = {
        user_id: user.id,
        habit_id: habitId,
        mood_rating: 4,
        energy_level: 4
      };

      const response = await fetch(`${API_BASE_URL}/api/habits/${habitId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(completion)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Refresh data
        await loadDashboard(user.id);
        await loadHabits(user.id);
        await loadAchievements(user.id);
        
        // Show success message
        if (result.level_up) {
          showNotification(`🎉 LEVEL UP! You reached Level ${result.current_level}! 🎉`, 'success');
        } else {
          showNotification(`✨ Habit completed! +${result.xp_earned} XP earned! ✨`, 'success');
        }

        // Show achievement notifications
        if (result.new_achievements && result.new_achievements.length > 0) {
          result.new_achievements.forEach(achievement => {
            showNotification(`🏆 Achievement Unlocked: ${achievement.name} - ${achievement.description}!`, 'achievement');
          });
        }
      }
    } catch (error) {
      console.error('Error completing habit:', error);
      showNotification('Failed to complete habit. Please try again.', 'error');
    }
  };

  const createHabit = async () => {
    try {
      const habit = {
        ...newHabit,
        user_id: user.id
      };

      const response = await fetch(`${API_BASE_URL}/api/habits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(habit)
      });

      if (response.ok) {
        setNewHabit({ name: '', description: '', category: 'wellness', difficulty: 1 });
        setShowNewHabitForm(false);
        await loadHabits(user.id);
        await loadDashboard(user.id);
        await loadAchievements(user.id);
        showNotification(`🌟 New habit "${habit.name}" created successfully!`, 'success');
      }
    } catch (error) {
      console.error('Error creating habit:', error);
      showNotification('Failed to create habit. Please try again.', 'error');
    }
  };

  const loadSuggestions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/suggestions/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const addSuggestedHabit = async (suggestion) => {
    try {
      const habit = {
        name: suggestion.name,
        description: suggestion.description,
        category: suggestion.category,
        difficulty: 2,
        user_id: user.id
      };

      const response = await fetch(`${API_BASE_URL}/api/habits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(habit)
      });

      if (response.ok) {
        await loadHabits(user.id);
        await loadDashboard(user.id);
        await loadAchievements(user.id);
        setSuggestions(suggestions.filter(s => s.name !== suggestion.name));
        showNotification(`✨ Added "${suggestion.name}" to your habits!`, 'success');
      }
    } catch (error) {
      console.error('Error adding suggested habit:', error);
    }
  };

  const logMood = async () => {
    try {
      const mood = {
        ...moodEntry,
        user_id: user.id
      };

      const response = await fetch(`${API_BASE_URL}/api/mood`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mood)
      });

      if (response.ok) {
        const result = await response.json();
        setMoodEntry({ mood_rating: 3, energy_level: 3, notes: '' });
        await loadDashboard(user.id);
        await loadAchievements(user.id);
        showNotification('✨ Mood logged successfully! ✨', 'success');

        // Show achievement notifications
        if (result.new_achievements && result.new_achievements.length > 0) {
          result.new_achievements.forEach(achievement => {
            showNotification(`🏆 Achievement Unlocked: ${achievement.name}!`, 'achievement');
          });
        }
      }
    } catch (error) {
      console.error('Error logging mood:', error);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      fitness: '💪',
      wellness: '🧘',
      productivity: '⚡',
      focus: '🎯',
      sleep: '😴'
    };
    return icons[category] || '⭐';
  };

  const getCategoryColor = (category) => {
    const colors = {
      fitness: 'bg-red-100 text-red-800',
      wellness: 'bg-green-100 text-green-800',
      productivity: 'bg-blue-100 text-blue-800',
      focus: 'bg-purple-100 text-purple-800',
      sleep: 'bg-indigo-100 text-indigo-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const renderProgressChart = () => {
    if (!analytics || !analytics.daily_data) return null;

    const maxCompletions = Math.max(...analytics.daily_data.map(d => d.completions), 1);
    
    return (
      <div className="grid grid-cols-10 gap-1">
        {analytics.daily_data.slice(-30).map((day, index) => (
          <div key={day.date} className="text-center">
            <div 
              className="w-full bg-white bg-opacity-20 rounded mb-1 transition-all duration-300 hover:bg-opacity-40"
              style={{ 
                height: `${Math.max(4, (day.completions / maxCompletions) * 40)}px`,
                backgroundColor: day.completions > 0 ? '#10B981' : 'rgba(255,255,255,0.2)'
              }}
              title={`${day.date}: ${day.completions} habits, ${day.xp_earned} XP`}
            />
            <div className="text-xs text-purple-200">
              {new Date(day.date).getDate()}
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 flex items-center justify-center">
        <div className="text-white text-2xl font-bold animate-pulse">🌟 Loading HabitVerse... 🌟</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500">
      {/* Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`notification ${notification.type} animate-slide-in`}
          >
            {notification.message}
          </div>
        ))}
      </div>

      {/* Header */}
      <header className="bg-white bg-opacity-20 backdrop-blur-lg border-b border-white border-opacity-20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl animate-bounce">🌟</div>
              <div>
                <h1 className="text-2xl font-bold text-white">HabitVerse</h1>
                <p className="text-purple-100 text-sm">Build your inner world</p>
              </div>
            </div>
            
            {dashboard && (
              <div className="flex items-center space-x-6 text-white">
                <div className="text-center group hover:scale-110 transition-transform">
                  <div className="text-2xl font-bold">{dashboard.user.current_level}</div>
                  <div className="text-xs opacity-75">Level</div>
                </div>
                <div className="text-center group hover:scale-110 transition-transform">
                  <div className="text-2xl font-bold">{dashboard.user.total_xp}</div>
                  <div className="text-xs opacity-75">XP</div>
                </div>
                <div className="text-center group hover:scale-110 transition-transform">
                  <div className="text-2xl font-bold">{dashboard.user.current_streak}</div>
                  <div className="text-xs opacity-75">Streak</div>
                </div>
                <div className="text-center group hover:scale-110 transition-transform">
                  <div className="text-2xl font-bold">{dashboard.achievements ? dashboard.achievements.length : 0}</div>
                  <div className="text-xs opacity-75">Badges</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white bg-opacity-10 backdrop-blur-lg border-b border-white border-opacity-20">
        <div className="container mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
              { id: 'habits', label: 'Habits', icon: '✅' },
              { id: 'ai-coach', label: 'AI Coach', icon: '🤖' },
              { id: 'achievements', label: 'Achievements', icon: '🏆' },
              { id: 'analytics', label: 'Analytics', icon: '📊' },
              { id: 'mood', label: 'Mood', icon: '😊' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  if (tab.id === 'analytics') loadAnalytics(user.id);
                }}
                className={`py-4 px-2 border-b-2 font-medium text-sm capitalize transition-colors flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-white text-white'
                    : 'border-transparent text-purple-100 hover:text-white hover:border-purple-200'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboard && (
          <div className="space-y-8">
            {/* Avatar & Progress */}
            <div className="card-glow">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">Welcome back, {user.username}! 🎉</h2>
                  <p className="text-purple-100">Your avatar is evolving beautifully!</p>
                </div>
                <div className="text-center">
                  <div 
                    className="w-32 h-32 rounded-full mx-auto mb-4 flex items-center justify-center text-6xl animate-float"
                    style={{ backgroundColor: dashboard.user.avatar_evolution.color }}
                  >
                    {dashboard.user.avatar_evolution.emoji}
                  </div>
                  <div className="text-white font-semibold text-lg">{dashboard.user.avatar_evolution.stage}</div>
                  <div className="text-purple-100 text-sm">Level {dashboard.user.current_level}</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between text-white text-sm mb-2">
                  <span>Progress to next level</span>
                  <span>{dashboard.user.xp_to_next_level} XP needed</span>
                </div>
                <div className="xp-bar">
                  <div 
                    className="xp-fill"
                    style={{ 
                      width: `${Math.max(10, 100 - (dashboard.user.xp_to_next_level / (dashboard.user.current_level * 100)) * 100)}%` 
                    }}
                  ></div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-4">
                <div className="stat-card">
                  <div className="stat-number">{dashboard.today_completions}</div>
                  <div className="stat-label">Today</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{Math.round(dashboard.completion_rate)}%</div>
                  <div className="stat-label">Success Rate</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{dashboard.user.longest_streak}</div>
                  <div className="stat-label">Best Streak</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{dashboard.achievements ? dashboard.achievements.length : 0}</div>
                  <div className="stat-label">Achievements</div>
                </div>
              </div>
            </div>

            {/* AI Coach Message */}
            {dashboard.ai_message && (
              <div className="ai-message">
                <div className="flex items-start space-x-4">
                  <div className="text-3xl">🤖</div>
                  <div>
                    <h3 className="text-white font-semibold mb-2">Your AI Coach</h3>
                    <p className="text-blue-100 leading-relaxed">{dashboard.ai_message}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Daily Quest */}
            {dashboard.daily_quest && (
              <div className="quest-card">
                <div className="flex items-center justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="text-3xl">⚡</div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Daily Quest</h3>
                      <p className="text-yellow-100 mb-2">{dashboard.daily_quest.title}</p>
                      <p className="text-yellow-200 text-sm">{dashboard.daily_quest.description}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => completeHabit(dashboard.daily_quest.habit_id)}
                    className="btn-success"
                  >
                    Complete Quest
                  </button>
                </div>
              </div>
            )}

            {/* Today's Habits */}
            <div className="card">
              <h3 className="text-xl font-bold text-white mb-4">Today's Habits</h3>
              <div className="space-y-3">
                {habits.slice(0, 4).map((habit) => (
                  <div key={habit.id} className={`habit-card ${habit.completed_today ? 'completed' : ''}`}>
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">{getCategoryIcon(habit.category)}</div>
                      <div>
                        <div className="text-white font-medium">{habit.name}</div>
                        <div className="text-purple-100 text-sm">{habit.description}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`category-badge ${getCategoryColor(habit.category)}`}>
                        +{habit.xp_reward} XP
                      </span>
                      {habit.completed_today ? (
                        <div className="text-green-300 text-2xl animate-bounce">✅</div>
                      ) : (
                        <button
                          onClick={() => completeHabit(habit.id)}
                          className="btn-success"
                        >
                          Complete
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Achievements */}
            {dashboard.achievements && dashboard.achievements.length > 0 && (
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">Recent Achievements 🏆</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {dashboard.achievements.slice(-4).map((achievement) => (
                    <div key={achievement.id} className="text-center p-4 bg-white bg-opacity-10 rounded-lg">
                      <div className="text-3xl mb-2">{achievement.icon}</div>
                      <div className="text-white font-medium text-sm">{achievement.name}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Habits Tab */}
        {activeTab === 'habits' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Your Habits</h2>
              <button
                onClick={() => setShowNewHabitForm(true)}
                className="btn-success"
              >
                + Add New Habit
              </button>
            </div>

            {/* New Habit Form */}
            {showNewHabitForm && (
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">Create New Habit</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Habit Name</label>
                    <input
                      type="text"
                      value={newHabit.name}
                      onChange={(e) => setNewHabit({...newHabit, name: e.target.value})}
                      className="input-glass"
                      placeholder="e.g., Morning Meditation"
                    />
                  </div>
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Description</label>
                    <textarea
                      value={newHabit.description}
                      onChange={(e) => setNewHabit({...newHabit, description: e.target.value})}
                      className="input-glass"
                      placeholder="Brief description of your habit"
                      rows="2"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Category</label>
                      <select
                        value={newHabit.category}
                        onChange={(e) => setNewHabit({...newHabit, category: e.target.value})}
                        className="input-glass"
                      >
                        <option value="wellness">🧘 Wellness</option>
                        <option value="fitness">💪 Fitness</option>
                        <option value="productivity">⚡ Productivity</option>
                        <option value="focus">🎯 Focus</option>
                        <option value="sleep">😴 Sleep</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Difficulty</label>
                      <select
                        value={newHabit.difficulty}
                        onChange={(e) => setNewHabit({...newHabit, difficulty: parseInt(e.target.value)})}
                        className="input-glass"
                      >
                        <option value="1">⭐ Easy (10 XP)</option>
                        <option value="2">⭐⭐ Medium (20 XP)</option>
                        <option value="3">⭐⭐⭐ Hard (30 XP)</option>
                        <option value="4">⭐⭐⭐⭐ Expert (40 XP)</option>
                        <option value="5">⭐⭐⭐⭐⭐ Master (50 XP)</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex space-x-4">
                    <button
                      onClick={createHabit}
                      className="btn-success"
                    >
                      Create Habit
                    </button>
                    <button
                      onClick={() => setShowNewHabitForm(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Habits List */}
            <div className="grid gap-4">
              {habits.map((habit) => (
                <div key={habit.id} className={`habit-card ${habit.completed_today ? 'completed' : ''}`}>
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">{getCategoryIcon(habit.category)}</div>
                    <div className="flex-1">
                      <h3 className="text-white font-semibold text-lg">{habit.name}</h3>
                      <p className="text-purple-100">{habit.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className={`category-badge ${getCategoryColor(habit.category)}`}>
                          {habit.category}
                        </span>
                        <span className="text-yellow-300 text-sm font-medium">+{habit.xp_reward} XP</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {habit.completed_today ? (
                      <div className="text-center">
                        <div className="text-green-300 text-3xl animate-bounce">✅</div>
                        <div className="text-green-200 text-sm">Completed!</div>
                      </div>
                    ) : (
                      <button
                        onClick={() => completeHabit(habit.id)}
                        className="btn-success"
                      >
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Coach Tab */}
        {activeTab === 'ai-coach' && (
          <div className="space-y-6">
            <div className="ai-message">
              <div className="flex items-center space-x-4 mb-6">
                <div className="text-4xl">🤖</div>
                <div>
                  <h2 className="text-2xl font-bold text-white">AI Coach</h2>
                  <p className="text-blue-100">Personalized guidance for your habit journey</p>
                </div>
              </div>
              
              {dashboard && dashboard.ai_message && (
                <div className="bg-white bg-opacity-10 rounded-lg p-6 mb-6">
                  <p className="text-white text-lg leading-relaxed">{dashboard.ai_message}</p>
                </div>
              )}
            </div>

            {/* AI Suggestions */}
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-white">AI Habit Suggestions</h3>
                <button
                  onClick={loadSuggestions}
                  className="btn-primary"
                >
                  Get Suggestions
                </button>
              </div>
              
              {suggestions.length > 0 ? (
                <div className="space-y-4">
                  {suggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-card">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl">{getCategoryIcon(suggestion.category)}</div>
                        <div className="flex-1">
                          <h4 className="text-white font-medium">{suggestion.name}</h4>
                          <p className="text-purple-100 text-sm">{suggestion.description}</p>
                          <span className={`inline-block category-badge mt-1 ${getCategoryColor(suggestion.category)}`}>
                            {suggestion.category}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => addSuggestedHabit(suggestion)}
                        className="btn-success"
                      >
                        Add Habit
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-purple-100 mb-4">Click "Get Suggestions" to receive AI-powered habit recommendations!</div>
                  <div className="text-6xl">🎯</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Achievements Tab */}
        {activeTab === 'achievements' && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-2">🏆 Achievements</h2>
              <p className="text-purple-100">Unlock badges by completing challenges!</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {achievements.map((achievement) => (
                <div 
                  key={achievement.id} 
                  className={`card transition-all duration-300 ${
                    achievement.unlocked 
                      ? 'bg-gradient-to-br from-yellow-400 to-orange-500 transform hover:scale-105' 
                      : 'bg-white bg-opacity-10 hover:bg-opacity-20'
                  }`}
                >
                  <div className="text-center">
                    <div className={`text-6xl mb-4 ${achievement.unlocked ? 'animate-bounce' : 'opacity-50'}`}>
                      {achievement.icon}
                    </div>
                    <h3 className={`font-bold text-lg mb-2 ${achievement.unlocked ? 'text-white' : 'text-purple-200'}`}>
                      {achievement.name}
                    </h3>
                    <p className={`text-sm mb-4 ${achievement.unlocked ? 'text-orange-100' : 'text-purple-300'}`}>
                      {achievement.description}
                    </p>
                    
                    {achievement.unlocked ? (
                      <div className="bg-white bg-opacity-20 rounded-lg p-2">
                        <span className="text-white text-sm font-medium">✨ UNLOCKED ✨</span>
                      </div>
                    ) : (
                      <div className="bg-white bg-opacity-10 rounded-lg p-2">
                        <span className="text-purple-200 text-sm">
                          {achievement.requirement.type === 'habit_completions' && `Complete ${achievement.requirement.count} habits`}
                          {achievement.requirement.type === 'streak' && `Reach ${achievement.requirement.count}-day streak`}
                          {achievement.requirement.type === 'habit_count' && `Create ${achievement.requirement.count} habits`}
                          {achievement.requirement.type === 'total_xp' && `Earn ${achievement.requirement.count} total XP`}
                          {achievement.requirement.type === 'mood_entries' && `Log mood ${achievement.requirement.count} times`}
                          {achievement.requirement.type === 'level' && `Reach level ${achievement.requirement.count}`}
                        </span>
                      </div>
                    )}
                    
                    {achievement.reward_xp > 0 && (
                      <div className="mt-2">
                        <span className="text-yellow-300 text-sm font-medium">+{achievement.reward_xp} XP</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-2">📊 Analytics</h2>
              <p className="text-purple-100">Track your progress and insights</p>
            </div>

            {analytics ? (
              <>
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="stat-card">
                    <div className="stat-number">{analytics.total_completions}</div>
                    <div className="stat-label">Total Completions</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{analytics.total_xp}</div>
                    <div className="stat-label">Total XP</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{analytics.current_streak}</div>
                    <div className="stat-label">Current Streak</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{Math.round(analytics.avg_mood * 10) / 10}</div>
                    <div className="stat-label">Avg Mood</div>
                  </div>
                </div>

                {/* Progress Chart */}
                <div className="card">
                  <h3 className="text-xl font-bold text-white mb-4">30-Day Progress</h3>
                  <div className="mb-4">
                    <div className="text-purple-100 text-sm mb-2">Daily habit completions</div>
                    {renderProgressChart()}
                  </div>
                  <div className="text-purple-200 text-sm">
                    Hover over bars to see details
                  </div>
                </div>

                {/* Mood & Energy Trends */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="card">
                    <h3 className="text-xl font-bold text-white mb-4">Mood Trend</h3>
                    <div className="flex items-end space-x-1 h-32">
                      {analytics.daily_data.slice(-14).map((day, index) => (
                        <div key={day.date} className="flex-1 flex flex-col justify-end">
                          <div 
                            className="bg-blue-400 rounded-t transition-all duration-300 hover:bg-blue-300"
                            style={{ height: `${(day.mood || 3) * 20}%` }}
                            title={`${day.date}: Mood ${day.mood || 'N/A'}`}
                          />
                        </div>
                      ))}
                    </div>
                    <div className="text-purple-200 text-sm mt-2">Last 14 days</div>
                  </div>

                  <div className="card">
                    <h3 className="text-xl font-bold text-white mb-4">Energy Trend</h3>
                    <div className="flex items-end space-x-1 h-32">
                      {analytics.daily_data.slice(-14).map((day, index) => (
                        <div key={day.date} className="flex-1 flex flex-col justify-end">
                          <div 
                            className="bg-green-400 rounded-t transition-all duration-300 hover:bg-green-300"
                            style={{ height: `${(day.energy || 3) * 20}%` }}
                            title={`${day.date}: Energy ${day.energy || 'N/A'}`}
                          />
                        </div>
                      ))}
                    </div>
                    <div className="text-purple-200 text-sm mt-2">Last 14 days</div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <div className="text-purple-100 mb-4">Loading analytics...</div>
                <div className="loading-spinner mx-auto"></div>
              </div>
            )}
          </div>
        )}

        {/* Mood Tab */}
        {activeTab === 'mood' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-2xl font-bold text-white mb-6">Daily Mood & Energy</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-white text-sm font-medium mb-3">How are you feeling today?</label>
                  <div className="flex space-x-4">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => setMoodEntry({...moodEntry, mood_rating: rating})}
                        className={`mood-selector ${
                          moodEntry.mood_rating === rating ? 'active' : ''
                        }`}
                      >
                        {rating === 1 ? '😢' : rating === 2 ? '😕' : rating === 3 ? '😐' : rating === 4 ? '😊' : '😄'}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-white text-sm font-medium mb-3">Energy Level</label>
                  <div className="flex space-x-4">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <button
                        key={level}
                        onClick={() => setMoodEntry({...moodEntry, energy_level: level})}
                        className={`mood-selector ${
                          moodEntry.energy_level === level ? 'active' : ''
                        }`}
                      >
                        {level <= 2 ? '🔋' : '⚡'}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-white text-sm font-medium mb-2">Notes (Optional)</label>
                  <textarea
                    value={moodEntry.notes}
                    onChange={(e) => setMoodEntry({...moodEntry, notes: e.target.value})}
                    className="input-glass"
                    placeholder="How are you feeling? Any thoughts to share?"
                    rows="3"
                  />
                </div>

                <button
                  onClick={logMood}
                  className="btn-primary"
                >
                  Log Mood & Energy
                </button>
              </div>
            </div>

            {/* Recent Mood Display */}
            {dashboard && dashboard.recent_mood && (
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">Recent Mood</h3>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-3xl mb-2">
                      {dashboard.recent_mood.mood_rating === 1 ? '😢' : 
                       dashboard.recent_mood.mood_rating === 2 ? '😕' : 
                       dashboard.recent_mood.mood_rating === 3 ? '😐' : 
                       dashboard.recent_mood.mood_rating === 4 ? '😊' : '😄'}
                    </div>
                    <div className="text-white text-sm">Mood</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl mb-2">
                      {dashboard.recent_mood.energy_level <= 2 ? '🔋' : '⚡'}
                    </div>
                    <div className="text-white text-sm">Energy</div>
                  </div>
                  {dashboard.recent_mood.notes && (
                    <div className="flex-1">
                      <div className="bg-white bg-opacity-10 rounded-lg p-3">
                        <p className="text-white text-sm">{dashboard.recent_mood.notes}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;