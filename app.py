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
        width: 100%;
    }

   .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5);
        background: linear-gradient(135deg, #8B5CF6 0%, #4F46E5 100%);
    }

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

   .floating {
        animation: floating 3s ease-in-out infinite;
    }

    @keyframes floating {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

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

   .stat-card {
        background: rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
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

# Session State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'practice_qs' not in st.session_state:
    st.session_state.practice_qs = []
if 'practice_idx' not in st.session_state:
    st.session_state.practice_idx = 0
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# Lottie Animations
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code!= 200:
            return None
        return r.json()
    except:
        return None

lottie_brain = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_dpcx1tgu.json")

# Database Functions
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
        supabase.table('profiles').update({
            'streak': new_streak,
            'last_checkin': today.isoformat()
        }).eq('id', user_id).execute()
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

def generate_practice_questions(concept, difficulty, count=5):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Generate {count} {difficulty} multiple choice questions for concept '{concept}'. Return JSON with key 'questions' containing array of objects with keys: question, options, answer, explanation"
            }],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)['questions']
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

# Authentication UI
def login_signup():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

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

# Pages
def home_page():
    st.title("MistakeMentor AI Pro")

    streak = get_streak(st.session_state.user.id)
    due_count = len(get_due_reviews(st.session_state.user.id))
    mistakes = get_user_mistakes(st.session_state.user.id)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='stat-card'>
            <h2 style='color: #7C3AED;'>🔥 {streak}</h2>
            <p>Day Streak</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='stat-card'>
            <h2 style='color: #3B82F6;'>📅 {due_count}</h2>
            <p>Due Reviews</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='stat-card'>
            <h2 style='color: #10B981;'>📚 {len(mistakes)}</h2>
            <p>Total Mistakes</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Scan Mistake"):
            st.session_state.page = "Scan"
            st.rerun()
    with col2:
        if st.button("Review Due Mistakes"):
            st.session_state.page = "Review"
            st.rerun()

def scan_page():
    st.title("Scan Your Mistake")
    uploaded_file = st.camera_input("Take a photo of the wrong answer")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Scanned Question", use_column_width=True)

        if st.button("Analyze with AI"):
            with st.spinner("AI is analyzing..."):
                try:
                    buffered = uploaded_file.getvalue()
                    img_b64 = base64.b64encode(buffered).decode()

                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Explain why this answer is wrong in 2 lines, name the concept, and return JSON with keys: explanation, concept, difficulty"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                        }],
                        max_tokens=300
                    )

                    result = json.loads(response.choices[0].message.content)

                    st.markdown(f"""
                    <div class='glass-card'>
                        <p style='color: #9CA3AF;'>AI Explanation</p>
                        <p>{result['explanation']}</p>
                        <span class='concept-tag'>Concept: {result['concept']}</span>
                        <span class='difficulty-{result['difficulty']}'> {result['difficulty'].title()}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Save Mistake"):
                        add_mistake(st.session_state.user.id, {
                            'image_url': uploaded_file.name,
                            'question_text': 'Scanned from image',
                            'explanation': result['explanation'],
                            'concept': result['concept'],
                            'difficulty': result['difficulty']
                        })
                        st.success("Saved! Added to your review queue.")
                        update_streak(st.session_state.user.id)
                        st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Add OPENAI_API_KEY in secrets to enable AI")

def dashboard_page():
    st.title("Weak Spot Map")
    mistakes = get_user_mistakes(st.session_state.user.id)

    if not mistakes:
        st.info("No mistakes yet. Start scanning!")
        return

    concepts = {}
    for m in mistakes:
        c = m['concept']
        concepts[c] = concepts.get(c, 0) + 1

    fig = go.Figure(data=[go.Pie(labels=list(concepts.keys()), values=list(concepts.values()),
                                 hole=.3, marker_colors=['#7C3AED', '#3B82F6', '#EF4444', '#F59E0B', '#10B981'])])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)

def review_page():
    st.title("Spaced Repetition Reviews")
    due_mistakes = get_due_reviews(st.session_state.user.id)

    if not due_mistakes:
        st.success("No reviews due today! 🎉")
        return

    st.info(f"You have {len(due_mistakes)} reviews due. Implement review logic here.")

# Main App Router
if not st.session_state.user and supabase:
    login_signup()
else:
    if not supabase:
        st.warning("Running in demo mode. Add SUPABASE_URL and SUPABASE_KEY to enable persistence.")

    with st.sidebar:
        st.title("📚 MistakeMentor AI")
        if st.session_state.user:
            streak = get_streak(st.session_state.user.id)
            st.write(f"Logged in as: {st.session_state.user.email}")
            st.write(f"🔥 Streak: {streak} days")
            if st.button("Logout"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

        page = option_menu(
            "Navigation",
            ["Home", "Scan", "Dashboard", "Review"],
            icons=['house', 'camera', 'bar-chart', 'repeat'],
            menu_icon="cast",
            default_index=0,
        )
        st.session_state.page = page

    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Scan":
        scan_page()
    elif st.session_state.page == "Dashboard":
        dashboard_page()
    elif st.session_state.page == "Review":
        review_page()
