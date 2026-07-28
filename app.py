import streamlit as st
import streamlit.components.v1 as components
import os
import uuid
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. CONFIGURATION & STYLING ---
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

st.set_page_config(
    page_title="SearchMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.sidebar_open else "collapsed"
)

# Premium UI Styling & Glassmorphic Space-Theme CSS
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Global Body Overrides */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif !important;
        background: linear-gradient(135deg, #090615 0%, #0d0922 40%, #04020a 100%) !important;
        color: #f3f4f6 !important;
    }

    /* Header Container - transparent and pinned at top left */
    header[data-testid="stHeader"],
    .stAppHeader {
        background: transparent !important;
        background-color: transparent !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        height: 3.5rem !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        z-index: 99999999 !important;
        pointer-events: none !important;
    }

    header[data-testid="stHeader"] * {
        pointer-events: auto !important;
    }

    /* Hide ONLY Unnecessary Streamlit Chrome, Menus, Footers & Manage App Toolbar */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    div[data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stElementToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stAppViewerToolbar"] {display: none !important; visibility: hidden !important; height: 0 !important; width: 0 !important; opacity: 0 !important; pointer-events: none !important;}
    [data-testid="stManageAppButton"] {display: none !important; visibility: hidden !important; height: 0 !important; width: 0 !important; opacity: 0 !important; pointer-events: none !important;}
    div[class*="stAppViewerToolbar"] {display: none !important; visibility: hidden !important;}
    div[class*="manageApp"] {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    button[title="View app in Streamlit"] {display: none !important;}
    div[data-testid="stToolbarActions"] {display: none !important;}

    /* Hide Streamlit default small collapse/expand arrow buttons to use custom toggle */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarExpandButton"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Fix Bottom Bar Background (Removes white container strip) */
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    div[class*="stBottom"] {
        background: transparent !important;
        background-color: transparent !important;
        border-top: none !important;
    }
    
    /* Scrollbars customization */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(124, 58, 237, 0.3);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 58, 237, 0.5);
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
    }

    /* Mobile Responsiveness & Touch Optimization (< 768px) */
    @media screen and (max-width: 768px) {
        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 4.5rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }

        .hero-container {
            padding: 1.25rem 0.85rem !important;
            margin-bottom: 1.25rem !important;
            border-radius: 16px !important;
        }

        .hero-title {
            font-size: 1.85rem !important;
        }

        .hero-subtitle {
            font-size: 0.9rem !important;
        }

        .hero-badge {
            font-size: 0.75rem !important;
            padding: 4px 12px !important;
        }

        section[data-testid="stSidebar"] {
            width: 88vw !important;
            max-width: 320px !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            gap: 6px !important;
        }

        div[data-testid="stChatMessage"] {
            padding: 0.85rem !important;
            margin-bottom: 1rem !important;
            border-radius: 14px !important;
        }

        .stMarkdown p, .stMarkdown li {
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }

        /* Ensure main top nav button is full width on small mobile screens */
        button[key="main_top_nav_btn"] {
            width: 100% !important;
            margin-bottom: 0.75rem !important;
        }
    }

    /* Expander card styling & horizontal row locking for mobile history */
    div[data-testid="stExpander"] {
        background: rgba(15, 12, 30, 0.85) !important;
        border: 1px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        margin-bottom: 1.5rem !important;
    }

    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 8px !important;
        margin-bottom: 6px !important;
    }

    div[data-testid="stExpander"] div[data-testid="column"]:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    div[data-testid="stExpander"] div[data-testid="column"]:last-child {
        flex: 0 0 46px !important;
        min-width: 46px !important;
    }

    div[data-testid="stExpander"] div[data-testid="column"] button {
        width: 100% !important;
        margin-top: 0 !important;
    }

    /* Title Block Header */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2.5rem 1.5rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        background-image: radial-gradient(circle at 10% 20%, rgba(124, 58, 237, 0.12), transparent 40%),
                          radial-gradient(circle at 90% 80%, rgba(244, 114, 182, 0.08), transparent 45%);
        text-align: center;
    }

    .hero-badge {
        background: linear-gradient(90deg, rgba(124, 58, 237, 0.2), rgba(244, 114, 182, 0.2));
        border: 1px solid rgba(124, 58, 237, 0.4);
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #c084fc;
        margin-bottom: 1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: inline-block;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #c084fc 10%, #818cf8 50%, #f472b6 90%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .hero-subtitle {
        color: #9ca3af;
        font-size: 1.1rem;
        font-weight: 400;
        max-width: 600px;
        line-height: 1.5;
    }

    /* Sidebar Navigation Overrides */
    section[data-testid="stSidebar"] {
        background-color: #05030d !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    .sidebar-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.25rem;
        margin-top: 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .sidebar-title {
        font-size: 1rem;
        font-weight: 700;
        color: #c084fc;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Button designs */
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        width: 100%;
        margin-top: 10px;
    }

    button[data-testid="baseButton-secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.6) !important;
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    }

    /* Custom Thread ID display card */
    .thread-id-display {
        font-family: monospace;
        background: rgba(0, 0, 0, 0.4);
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #a78bfa;
        font-size: 0.85rem;
        word-break: break-all;
        margin-top: 0.5rem;
    }

    /* Chat message base layout */
    div[data-testid="stChatMessage"] {
        border-radius: 20px !important;
        padding: 1.25rem !important;
        margin-bottom: 1.5rem !important;
        transition: all 0.25s ease;
    }

    /* User Chat Message - Indigo/Violet styled bubble */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(124, 58, 237, 0.12) 100%) !important;
        border: 1px solid rgba(124, 58, 237, 0.3) !important;
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.08) !important;
    }

    /* Assistant Chat Message - Sleek Dark Glass card */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3) !important;
    }

    /* Hover effects for visual responsiveness */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]):hover {
        border-color: rgba(124, 58, 237, 0.5) !important;
        box-shadow: 0 10px 35px rgba(124, 58, 237, 0.18) !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]):hover {
        border-color: rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 10px 35px rgba(124, 58, 237, 0.05) !important;
    }

    /* Message typography & spacing */
    .stMarkdown p {
        line-height: 1.75 !important;
        font-size: 1.05rem !important;
        color: #e5e7eb !important;
        margin-bottom: 1.25rem !important;
    }

    .stMarkdown li {
        line-height: 1.7 !important;
        font-size: 1.05rem !important;
        color: #e5e7eb !important;
        margin-bottom: 0.75rem !important;
    }

    /* Floating Chat input field styling */
    div[data-testid="stChatInput"] {
        background: rgba(15, 12, 30, 0.8) !important;
        border: 1px solid rgba(124, 58, 237, 0.2) !important;
        border-radius: 18px !important;
        backdrop-filter: blur(20px) !important;
        padding: 6px !important;
        box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.4), 0 10px 30px rgba(0, 0, 0, 0.4) !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: rgba(124, 58, 237, 0.5) !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.25) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: #f3f4f6 !important;
        font-size: 1.05rem !important;
    }

    /* Avatar styling overrides */
    div[data-testid="chatAvatarIcon-user"] {
        background-color: #3b82f6 !important;
    }
    div[data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
    }

    /* Style select chat buttons in sidebar */
    section[data-testid="stSidebar"] button {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* Style select chat buttons inside columns */
    section[data-testid="stSidebar"] div[data-testid="column"]:nth-child(1) button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #e5e7eb !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 10px !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="column"]:nth-child(1) button:hover {
        background: rgba(124, 58, 237, 0.1) !important;
        border-color: rgba(124, 58, 237, 0.4) !important;
        color: #a78bfa !important;
    }

    /* Style delete button specifically */
    section[data-testid="stSidebar"] div[data-testid="column"]:nth-child(2) button {
        background: transparent !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        color: #ef4444 !important;
        padding: 5px 8px !important;
        box-shadow: none !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    section[data-testid="stSidebar"] div[data-testid="column"]:nth-child(2) button:hover {
        background: rgba(239, 68, 68, 0.15) !important;
        border-color: #ef4444 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables (Local .env & Streamlit Cloud Secrets)
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# Sync Streamlit Cloud secrets into os.environ if present
try:
    if hasattr(st, "secrets"):
        if "GOOGLE_API_KEY" in st.secrets and not os.getenv("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        if "SERPER_API_KEY" in st.secrets and not os.getenv("SERPER_API_KEY"):
            os.environ["SERPER_API_KEY"] = st.secrets["SERPER_API_KEY"]
except Exception:
    pass

# --- 2. STATE INITIALIZATION ---
# LangGraph memory saver checkpoint (persists in Streamlit's session state)
if "memory" not in st.session_state:
    st.session_state.memory = MemorySaver()

# Unique thread ID for the current chat session
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Initialize chat counter and name for user-friendly display
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 1

if "chat_name" not in st.session_state:
    st.session_state.chat_name = f"Chat Session #{st.session_state.chat_counter}"

# Dictionary of all active chat sessions: {thread_id: chat_name}
if "chats" not in st.session_state:
    st.session_state.chats = {st.session_state.thread_id: st.session_state.chat_name}

# Toggle visibility of chat history list
if "show_history" not in st.session_state:
    st.session_state.show_history = True

# --- 3. AGENT SETUP ---
# Re-instantiate agent on each run using the session checkpointer
def get_agent():
    # Verify keys
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("SERPER_API_KEY"):
        st.error("⚠️ Missing API Keys! Please configure GOOGLE_API_KEY and SERPER_API_KEY in your .env file or Streamlit Cloud Secrets.")
        st.stop()

    search = GoogleSerperAPIWrapper()
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    return create_agent(
        model=llm,
        tools=[search.run],
        system_prompt=(
            "You are a helpful, professional chatbot assistant.\n\n"
            "Formatting Rules:\n"
            "1. ALWAYS structure your answers cleanly and clearly.\n"
            "2. Separate different topics, stories, or items with two newlines (a double enter) to create clear visual spacing.\n"
            "3. Use bold bulleted list formats (e.g. '* **Item Title**: Description text') for lists.\n"
            "4. Keep paragraphs short and concise so they are extremely readable.\n"
            "5. You have access to a Google Search tool. Search if you need up-to-date factual information."
        ),
        checkpointer=st.session_state.memory
    )

agent = get_agent()

# --- 4. SIDEBAR NAVIGATION ---
col_title, col_hide = st.sidebar.columns([3, 2])
with col_title:
    st.markdown("""<h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #f3f4f6;">🧠 SearchMind</h3>""", unsafe_allow_html=True)
with col_hide:
    if st.button("Hide", key="sidebar_hide_btn"):
        st.session_state.sidebar_open = False
        st.rerun()

# "New Chat" button
if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_counter += 1
    new_thread_id = str(uuid.uuid4())
    new_chat_name = f"Chat Session #{st.session_state.chat_counter}"
    st.session_state.chats[new_thread_id] = new_chat_name
    st.session_state.thread_id = new_thread_id
    st.session_state.chat_name = new_chat_name
    st.rerun()

st.sidebar.markdown("<hr style='border-color: rgba(255, 255, 255, 0.08); margin: 0.85rem 0;'>", unsafe_allow_html=True)

# Render active chats list
st.sidebar.markdown("<div class='sidebar-title'>💬 Chat History</div>", unsafe_allow_html=True)

for t_id, name in list(st.session_state.chats.items()):
    col1, col2 = st.sidebar.columns([4, 1])
    is_active = (t_id == st.session_state.thread_id)
    
    # Active session visual indicator
    display_label = f"💬 {name}" + (" 📍" if is_active else "")
    
    # Select Chat
    if col1.button(display_label, key=f"select_{t_id}"):
        st.session_state.thread_id = t_id
        st.session_state.chat_name = name
        st.rerun()
        
    # Delete Chat
    if col2.button("🗑️", key=f"del_{t_id}"):
        # Delete from session dict
        del st.session_state.chats[t_id]
        
        # If we deleted the active chat, switch to the first remaining one
        if st.session_state.thread_id == t_id:
            if st.session_state.chats:
                first_t_id = list(st.session_state.chats.keys())[0]
                st.session_state.thread_id = first_t_id
                st.session_state.chat_name = st.session_state.chats[first_t_id]
            else:
                # No chats left, generate a fresh one
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.chat_counter = 1
                st.session_state.chat_name = "Chat Session #1"
                st.session_state.chats = {st.session_state.thread_id: st.session_state.chat_name}
        st.rerun()

st.sidebar.markdown("""
<div class="sidebar-card" style="margin-top: 1.5rem;">
    <div class="sidebar-title">✨ About SearchMind</div>
    <p style="color: #9ca3af; font-size: 0.88rem; line-height: 1.5; margin: 0;">
        An intelligent AI companion powered by real-time web search and conversational memory.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 5. MAIN INTERFACE ---
col_nav, _ = st.columns([2, 3])
with col_nav:
    nav_btn_label = "Hide History" if st.session_state.sidebar_open else "See History"
    if st.button(nav_btn_label, key="main_top_nav_btn"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()

# Responsive In-Page History Drawer (Guarantees 100% working History on Mobile Screens)
if st.session_state.sidebar_open:
    with st.expander("💬 Saved Chat Sessions & History", expanded=True):
        col_h_new, col_h_space = st.columns([1, 2])
        with col_h_new:
            if st.button("➕ New Chat", key="main_history_new_chat_btn"):
                st.session_state.chat_counter += 1
                new_thread_id = str(uuid.uuid4())
                new_chat_name = f"Chat Session #{st.session_state.chat_counter}"
                st.session_state.chats[new_thread_id] = new_chat_name
                st.session_state.thread_id = new_thread_id
                st.session_state.chat_name = new_chat_name
                st.rerun()
                
        for t_id, name in list(st.session_state.chats.items()):
            hc1, hc2 = st.columns([5, 1])
            is_active = (t_id == st.session_state.thread_id)
            display_label = f"💬 {name}" + (" 📍 (Active)" if is_active else "")
            
            if hc1.button(display_label, key=f"main_select_session_{t_id}"):
                st.session_state.thread_id = t_id
                st.session_state.chat_name = name
                st.rerun()
            if hc2.button("🗑️", key=f"main_del_session_{t_id}"):
                del st.session_state.chats[t_id]
                if st.session_state.thread_id == t_id:
                    if st.session_state.chats:
                        first_t_id = list(st.session_state.chats.keys())[0]
                        st.session_state.thread_id = first_t_id
                        st.session_state.chat_name = st.session_state.chats[first_t_id]
                    else:
                        st.session_state.thread_id = str(uuid.uuid4())
                        st.session_state.chat_counter = 1
                        st.session_state.chat_name = "Chat Session #1"
                        st.session_state.chats = {st.session_state.thread_id: st.session_state.chat_name}
                st.rerun()

st.markdown("""
<div class="hero-container">
    <div class="hero-badge">🧠 SearchMind AI</div>
    <div class="hero-title">SearchMind</div>
    <div class="hero-subtitle">
        Your intelligent AI search assistant for real-time web answers and smart conversations.
    </div>
</div>
""", unsafe_allow_html=True)

# Helper function to clean custom block outputs from gemini-3.5-flash-lite
def clean_content(content):
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            else:
                text_parts.append(str(block))
        return "".join(text_parts)
    return str(content)

# Retrieve current messages list from LangGraph memory checkpoint for the active thread
config = {"configurable": {"thread_id": st.session_state.thread_id}}
state = agent.get_state(config)
history = state.values.get("messages", [])

# Render conversation history using string type checking to resolve module scope conflicts
for msg in history:
    msg_type = getattr(msg, "type", None)
    if msg_type == "human":
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif msg_type == "ai":
        cleaned = clean_content(msg.content)
        if cleaned.strip():  # Skip empty assistant tool-call state updates
            with st.chat_message("assistant"):
                st.markdown(cleaned)

# --- 6. USER INPUT HANDLING ---
if user_input := st.chat_input("Ask me anything..."):
    # Security: Sanitize user prompt and prevent prompt flood vulnerabilities
    sanitized_input = user_input.strip()[:4000]
    
    # Immediately render user prompt on screen
    with st.chat_message("user"):
        st.markdown(sanitized_input)
    
    # Process through Agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking & searching..."):
            try:
                # Invoke the agent. It retrieves the thread's history automatically.
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": sanitized_input}]},
                    config
                )
                final_reply = clean_content(response["messages"][-1].content)
                st.markdown(final_reply)
            except Exception:
                # Secure Error Handling: Do not leak stack traces or internal environment variables
                st.error("⚠️ An unexpected error occurred while processing your request. Please try again.")
                
    # Refresh to update the messages list and state
    st.rerun()
