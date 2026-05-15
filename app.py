import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import openai
import os
import json
import base64
import datetime
import io
import random
from dotenv import load_dotenv
from supabase import create_client
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.units import inch
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
import numpy as np
from datetime import timedelta
import calendar
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from streamlit_timeline import timeline
import pydeck as pdk

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="MistakeMentor AI Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #0d1117 100%);
        color: #e1e1e6;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(124, 58, 237, 0.2);
        border: 1px solid rgba(124, 58, 237, 0.3);
    }
    
    /* Gradient Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
        background: linear-gradient(135deg, #8B5CF6 0%, #4F46E5 100%);
    }
    
    /* Animated Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #7C3AED, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: gradient-shift 3s ease infinite;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #7C3AED, #3B82F6);
        border-radius: 10px;
    }
    
    /* Floating Animation */
    .floating {
        animation: floating 3s ease-in-out infinite;
    }
    
    @keyframes floating {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* Pulse Animation */
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.4); }
        70% { box-shadow: 0 0 0 20px rgba(124, 58, 237, 0); }
        100% { box-shadow: 0 0 0 0 rgba(124, 58, 237, 0); }
    }
    
    /* Stats Card */
    .stat-card {
        background: rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        background: rgba(124, 58, 237, 0.2);
        transform: scale(1.05);
    }
    
    /* Tags */
    .concept-tag {
        background: linear-gradient(135deg, #7C3AED, #5B21B6);
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 10px rgba(124, 58, 237, 0.3);
    }
    
    .difficulty-easy { color: #10B981; font-weight: 600; }
    .difficulty-medium { color: #F59E0B; font-weight: 600; }
    .difficulty-hard { color: #EF4444; font-weight: 600; }
    
    /* Progress Bar */
    .progress-bar {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        height: 12px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 20px;
        transition: width 0.5s ease;
        background: linear-gradient(90deg, #7C3AED, #3B82F6);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(15, 17, 23, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background: rgba(124, 58, 237, 0.9);
        color: white;
        text-align: center;
        padding: 5px 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        white-space: nowrap;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Clients
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# Enhanced Session State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'practice_qs' not in st.session_state:
    st.session_state.practice_qs = []
if 'practice_idx' not in st.session_state:
    st.session_state.practice_idx = 0
if 'achievements' not in st.session_state:
    st.session_state.achievements = []
if 'daily_goal' not in st.session_state:
    st.session_state.daily_goal = 5
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'ai_tutor_enabled' not in st.session_state:
    st.session_state.ai_tutor_enabled = True

# Lottie Animations
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_study = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_sqpjokhc.json")
lottie_success = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_jbrw3hcz.json")
lottie_brain = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_dpcx1tgu.json")

# Enhanced Database Functions
def get_user_profile(user_id):
    if not supabase: return None
    try:
        res = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        return res.data if res.data else None
    except:
        return None

def create_user_profile(user_id, email):
    if not supabase: return
    try:
        supabase.table('profiles').insert({
            'id': user_id,
            'email': email,
            'streak': 0,
            'last_checkin': None,
            'total_mistakes': 0,
            'total_reviews': 0,
            'xp_points': 0,
            'level': 1,
            'created_at': datetime.datetime.now().isoformat()
        }).execute()
    except:
        pass

def update_streak(user_id):
    if not supabase: return 0
    profile = get_user_profile(user_id)
    today = datetime.date.today()
    
    if not profile:
        create_user_profile(user_id, "")
        profile = get_user_profile(user_id)
    
    last_checkin = datetime.date.fromisoformat(profile['last_checkin']) if profile.get('last_checkin') else None
    
    if last_checkin == today:
        return profile.get('streak', 0)
    elif last_checkin == today - datetime.timedelta(days=1):
        new_streak = profile.get('streak', 0) + 1
        xp_bonus = 10 * new_streak  # Bonus XP for longer streaks
        supabase.table('profiles').update({
            'streak': new_streak,
            'last_checkin': today.isoformat(),
            'xp_points': profile.get('xp_points', 0) + xp_bonus
        }).eq('id', user_id).execute()
        check_achievements(user_id, new_streak)
        return new_streak
    else:
        supabase.table('profiles').update({
            'streak': 1,
            'last_checkin': today.isoformat()
        }).eq('id', user_id).execute()
        return 1

def get_streak(user_id):
    profile = get_user_profile(user_id)
    return profile.get('streak', 0) if profile else 0

def add_xp(user_id, points):
    if not supabase: return
    profile = get_user_profile(user_id)
    if profile:
        new_xp = profile.get('xp_points', 0) + points
        new_level = new_xp // 100 + 1
        supabase.table('profiles').update({
            'xp_points': new_xp,
            'level': new_level
        }).eq('id', user_id).execute()

def check_achievements(user_id, streak):
    achievements = []
    if streak >= 7:
        achievements.append("Weekly Warrior")
    if streak >= 30:
        achievements.append("Monthly Master")
    if streak >= 100:
        achievements.append("Century Streak")
    
    profile = get_user_profile(user_id)
    if profile and profile.get('total_mistakes', 0) >= 50:
        achievements.append("Mistake Collector")
    if profile and profile.get('total_reviews', 0) >= 100:
        achievements.append("Review Champion")
    
    return achievements

def sm2_interval(repetitions, interval, ease_factor, quality):
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        repetitions += 1
    
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_review = datetime.date.today() + datetime.timedelta(days=interval)
    return repetitions, interval, ease_factor, next_review

def get_user_mistakes(user_id):
    if not supabase: return []
    try:
        res = supabase.table('mistakes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return res.data if res.data else []
    except:
        return []

def add_mistake(user_id, data):
    if not supabase: return
    try:
        supabase.table('mistakes').insert({
            'user_id': user_id,
            'image_url': data.get('image_url', ''),
            'question_text': data.get('question_text', ''),
            'explanation': data.get('explanation', ''),
            'concept': data.get('concept', ''),
            'difficulty': data.get('difficulty', 'medium'),
            'repetitions': 0,
            'interval': 1,
            'ease_factor': 2.5,
            'next_review': datetime.date.today().isoformat(),
            'created_at': datetime.datetime.now().isoformat()
        }).execute()
        
        # Update profile stats
        profile = get_user_profile(user_id)
        if profile:
            supabase.table('profiles').update({
                'total_mistakes': profile.get('total_mistakes', 0) + 1
            }).eq('id', user_id).execute()
            add_xp(user_id, 20)  # XP for adding a mistake
    except:
        pass

def update_review(mistake_id, quality):
    if not supabase: return
    try:
        mistake = supabase.table('mistakes').select('*').eq('id', mistake_id).single().execute().data
        reps, interval, ef, next_review = sm2_interval(
            mistake['repetitions'], mistake['interval'], mistake['ease_factor'], quality
        )
        supabase.table('mistakes').update({
            'repetitions': reps,
            'interval': interval,
            'ease_factor': ef,
            'next_review': next_review.isoformat()
        }).eq('id', mistake_id).execute()
        
        # Update profile stats
        user_id = mistake['user_id']
        profile = get_user_profile(user_id)
        if profile:
            supabase.table('profiles').update({
                'total_reviews': profile.get('total_reviews', 0) + 1
            }).eq('id', user_id).execute()
            add_xp(user_id, 15 * quality)  # XP based on review quality
    except:
        pass

def get_due_reviews(user_id):
    if not supabase: return []
    try:
        today = datetime.date.today().isoformat()
        res = supabase.table('mistakes').select('*').eq('user_id', user_id).lte('next_review', today).execute()
        return res.data if res.data else []
    except:
        return []

# AI Tutor Function
def get_ai_tutor_response(question, context=""):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "You are an expert AI tutor. Provide detailed, encouraging explanations. Break down complex concepts. Use analogies and examples."
            }, {
                "role": "user",
                "content": f"Context: {context}\nQuestion: {question}"
            }],
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return "AI Tutor is currently unavailable. Please try again later."

def generate_practice_questions(concept, difficulty, count=5):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Generate {count} {difficulty} multiple choice questions for concept '{concept}'. Include detailed explanations. Return JSON with key 'questions' containing array of objects with keys: question, options (array of 4), answer (exact match to one option), explanation"
            }],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)['questions']
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

# Enhanced PDF Generation
def generate_enhanced_pdf(mistakes, user_email=""):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    
    # Header
    c.setFillColor(colors.HexColor('#7C3AED'))
    c.rect(0, height - 100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 60, "MistakeMentor AI Pro Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if user_email:
        c.drawString(50, height - 95, f"User: {user_email}")
    
    y = height - 130
    
    # Statistics Summary
    concepts_count = {}
    difficulties = {'easy': 0, 'medium': 0, 'hard': 0}
    for m in mistakes:
        concepts_count[m['concept']] = concepts_count.get(m['concept'], 0) + 1
        difficulties[m.get('difficulty', 'medium')] = difficulties.get(m.get('difficulty', 'medium'), 0) + 1
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Summary Statistics")
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Total Mistakes: {len(mistakes)} | Top Concept: {max(concepts_count, key=concepts_count.get) if concepts_count else 'N/A'}")
    y -= 30
    
    # Mistakes List
    styles = getSampleStyleSheet()
    for i, m in enumerate(mistakes[:50], 1):
        if y < 150:
            c.showPage()
            y = height - 50
        
        # Mistake card background
        c.setFillColor(colors.HexColor('#F3F4F6'))
        c.roundRect(40, y - 80, width - 80, 75, 10, fill=1)
        c.setFillColor(colors.black)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 15, f"{i}. {m['concept']}")
        y -= 20
        
        c.setFont("Helvetica", 9)
        p = Paragraph(m['explanation'][:200], styles['Normal'])
        p.wrapOn(c, width - 120, 50)
        p.drawOn(c, 50, y - 15)
        y -= p.height + 10
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, y - 15, f"Difficulty: {m.get('difficulty', 'N/A')} | Created: {m.get('created_at', 'N/A')[:10]}")
        y -= 30
    
    c.save()
    buffer.seek(0)
    return buffer

# Word Cloud Generator
def generate_wordcloud(text_data):
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='rgba(0,0,0,0)',
        colormap='viridis',
        mode='RGBA'
    ).generate(text_data)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

# Learning Insights
def generate_learning_insights(mistakes):
    if not mistakes:
        return "No data available for insights."
    
    concepts = [m['concept'] for m in mistakes]
    concept_freq = pd.Series(concepts).value_counts()
    
    insights = []
    insights.append(f"📊 Your most challenging concept is **{concept_freq.index[0]}** with {concept_freq.values[0]} mistakes.")
    
    if len(concept_freq) > 1:
        insights.append(f"💡 Focus on **{concept_freq.index[1]}** as your second weakest area.")
    
    difficulties = [m.get('difficulty', 'medium') for m in mistakes]
    if difficulties.count('hard') > len(difficulties) * 0.5:
        insights.append("🎯 You're tackling mostly hard problems - great for growth!")
    
    return "\n\n".join(insights)

# Authentication UI
def login_signup():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Animated header
        st.markdown("""
        <div style='text-align: center;' class='floating'>
            <h1 style='font-size: 48px; font-weight: 800;'>
                <span class='gradient-text'>MistakeMentor AI Pro</span>
            </h1>
            <p style='color: #9CA3AF; font-size: 18px; margin-top: -10px;'>
                Transform Your Mistakes into Mastery
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if lottie_brain:
            st_lottie(lottie_brain, height=200, key="brain_anim")
        
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    submitted = st.form_submit_button("🚀 Login to Continue", use_container_width=True)
                with col_b:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<p style="text-align: center; color: #9CA3AF;">or</p>', unsafe_allow_html=True)
                
                if submitted:
                    try:
                        if supabase:
                            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            # Authentication UI
def login_signup():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Animated header
        st.markdown("""
        <div style='text-align: center;' class='floating'>
            <h1 style='font-size: 48px; font-weight: 800;'>
                <span class='gradient-text'>MistakeMentor AI Pro</span>
            </h1>
            <p style='color: #9CA3AF; font-size: 18px; margin-top: -10px;'>
                Transform Your Mistakes into Mastery
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if lottie_brain:
            st_lottie(lottie_brain, height=200, key="brain_anim")
        
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••")
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    submitted = st.form_submit_button("🚀 Login to Continue", use_container_width=True)
                
                if submitted:
                    try:
                        if supabase:
                            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = user.user
                            update_streak(user.user.id)
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Supabase not connected. Add SUPABASE_URL and SUPABASE_KEY in secrets.")
                    except Exception as e:
                        st.error(f"Login failed: {e}")

        with tab2:
            with st.form("signup_form"):
                email = st.text_input("📧 Email", placeholder="you@example.com", key="signup_email")
                password = st.text_input("🔒 Password", type="password", placeholder="••••", key="signup_pass")
                submitted = st.form_submit_button("✨ Create Account", use_container_width=True)
                
                if submitted:
                    try:
                        if supabase:
                            user = supabase.auth.sign_up({"email": email, "password": password})
                            st.success("Account created! Check your email to verify, then login.")
                        else:
                            st.error("Supabase not connected. Add SUPABASE_URL and SUPABASE_KEY in secrets.")
                    except Exception as e:
                        st.error(f"Signup failed: {e}")
