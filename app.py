import streamlit as st
from PIL import Image
import opena
from reportlab.pdfgen import canvas

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer

load_dotenv()

st.set_page_config(
    page_title="MistakeMentor AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Styling ---
st.markdown("""
<style>
 .stApp {background: linear-gradient(180deg, #0F1117 0%, #1A1D24 100%); color: white;}


 .stButton>button:hover {transform: scale(1.02);}
 .concept-tag {background: #7C3AED; padding: 6px 12px; border-radius: 20px; display: inline-block; font-size: 12px;}
 .difficulty-easy {color: #10B981;}.difficulty-med {color: #F59E0B;}.difficulty-hard {color: #EF4444;}
 .streak-fire {font-size: 48px; text-align: center;}</style>
""", unsafe_allow_html=True)

# --- Clients ---
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

# --- Session State ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'practice_qs' not in st.session_state:
    st.session_state.practice_qs = []
if 'practice_idx' not in st.session_state:
    st.session_state.practice_idx = 0

# --- Helpers ---
def get_user_profile(user_id):
    if not supabase: return None

def update_streak(user_id):
    if not supabase: return 0
    profile = get_user_profile(user_i
            'id': user_id,
            'streak': 1,
            'last_checkin': today.isoformat()
        }).execute()
        return 1

    last_checkin = datetime.date.fromisoformat(profile['last_checkin']) if profile['last_checkin'] else None

    if last_checkin == today:
        return profile['streak']
    elif last_checkin == today - datetime.timedelta(days=1):
        new_streak = profile['streak'] + 1        supabase.table('profiles').update({
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
    return profile['streak'] if profile else 0

def sm2_interval(repetitions, interval, ease_factor, quality):
    if quality < 3:        repetitions = 0; interval = 1
    else:
        if repetitions == 0: interval = 1
        elif repetitions == 1: interval = 6
        else: interval = int(interval * ease_factor)
        repetitions += 1
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_review = datetime.date.today() + datetime.timedelta(days=interval)
    return repetitions, interval, ease_factor, next_review

def get_user_mistakes(user_id):
    if not supabase: return []
    res = supabase.table('mistakes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
    return res.data

def add_mistake(user_id, data):
    if not supabase: return
    supabase.table('mistakes').insert({
        'user_id': user_id,
        'image_url': data.get('image_url'),
        'question_text': data.get('question_text'),
        'explanation': data.get('explanation'),
        'concept': data.get('concept'),
        'difficulty': data.get('difficulty', 'medium'),
        'repetitions': 0,
        'interval': 1,
        'ease_factor': 2.5,
        'next_review': datetime.date.today().isoformat()
    }).execute()

def update_review(mistake_id, quality):
    if not supabase: return
    mistake = supabase.table('mistakes').select('*').eq('id', mistake_id).single().execute().data
    reps, interval, ef, next_review = sm2_interval(
        mistake['repetitio
    

