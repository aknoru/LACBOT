"""
Super User Dashboard - Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Page configuration
st.set_page_config(
    page_title="LACBOT - Super User Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    .success-card {
        border-left-color: #10b981;
    }
    .warning-card {
        border-left-color: #f59e0b;
    }
    .error-card {
        border-left-color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

def get_auth_headers():
    """Get authentication headers"""
    token = st.session_state.get('auth_token')
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

def authenticate():
    """Authentication function"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Super User Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/auth/login",
                        json={"email": email, "password": password}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("role") == "superuser":
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.authenticated = True
                            st.session_state.user_info = data
                            st.rerun()
                        else:
                            st.error("Access denied. Superuser privileges required.")
                    else:
                        st.error("Invalid credentials")
                        
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
        
        st.stop()

def get_system_stats():
    """Get system statistics"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/stats", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch stats: {str(e)}")
        return None

def get_users():
    """Get all users"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/users", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch users: {str(e)}")
        return None

def get_conversations():
    """Get all conversations"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/conversations", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch conversations: {str(e)}")
        return None

def get_faqs():
    """Get all FAQs"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/faqs", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch FAQs: {str(e)}")
        return None

def main():
    """Main dashboard function"""
    authenticate()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 LACBOT - Super User Dashboard</h1>
        <p>Comprehensive system management and analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        page = st.selectbox(
            "Select Page",
            ["📊 Overview", "👥 User Management", "💬 Conversations", "❓ FAQ Management", "📈 Analytics", "🔧 System Settings"]
        )
        
        st.markdown("---")
        
        # User info
        if 'user_info' in st.session_state:
            st.markdown(f"**Logged in as:** {st.session_state.user_info.get('email', 'Unknown')}")
            
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on selected page
    if page == "📊 Overview":
        show_overview()
    elif page == "👥 User Management":
        show_user_management()
    elif page == "💬 Conversations":
        show_conversations()
    elif page == "❓ FAQ Management":
        show_faq_management()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "🔧 System Settings":
        show_system_settings()

def show_overview():
    """Show overview dashboard"""
    st.header("📊 System Overview")
    
    # Get system stats
    stats = get_system_stats()
    
    if stats:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card success-card">
                <h3>👥 Total Users</h3>
                <h2>{total_users}</h2>
            </div>
            """.format(total_users=stats['total_users']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>💬 Total Conversations</h3>
                <h2>{total_conversations}</h2>
            </div>
            """.format(total_conversations=stats['total_conversations']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>📝 Total Messages</h3>
                <h2>{total_messages}</h2>
            </div>
            """.format(total_messages=stats['total_messages']), unsafe_allow_html=True)
        
        with col4:
            confidence_color = "success-card" if stats['avg_confidence_score'] > 0.7 else "warning-card"
            st.markdown(f"""
            <div class="metric-card {confidence_color}">
                <h3>🎯 Avg Confidence</h3>
                <h2>{stats['avg_confidence_score']:.1%}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Language distribution
        st.subheader("🌍 Language Usage")
        if stats['active_languages']:
            lang_df = pd.DataFrame(list(stats['active_languages'].items()), 
                                 columns=['Language', 'Count'])
            
            fig = px.pie(lang_df, values='Count', names='Language', 
                        title="Conversations by Language")
            st.plotly_chart(fig, use_container_width=True)
        
        # Human intervention rate
        st.subheader("🤖 Automation Status")
        intervention_rate = stats['human_intervention_rate']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = (1 - intervention_rate) * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Automation Rate (%)"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("Human Intervention Rate", f"{intervention_rate:.1%}")
            st.metric("Automation Rate", f"{(1 - intervention_rate):.1%}")
    
    else:
        st.error("Failed to load system statistics")

def show_user_management():
    """Show user management interface"""
    st.header("👥 User Management")
    
    # Get users
    users_data = get_users()
    
    if users_data:
        users_df = pd.DataFrame(users_data['users'])
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            role_filter = st.selectbox("Filter by Role", ["All"] + list(users_df['role'].unique()))
        
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
        
        with col3:
            language_filter = st.selectbox("Filter by Language", ["All"] + list(users_df['language_preference'].unique()))
        
        # Apply filters
        filtered_df = users_df.copy()
        
        if role_filter != "All":
            filtered_df = filtered_df[filtered_df['role'] == role_filter]
        
        if status_filter != "All":
            active_filter = status_filter == "Active"
            filtered_df = filtered_df[filtered_df['is_active'] == active_filter]
        
        if language_filter != "All":
            filtered_df = filtered_df[filtered_df['language_preference'] == language_filter]
        
        # Display users
        st.subheader(f"Users ({len(filtered_df)} total)")
        
        # User actions
        selected_users = st.multiselect("Select users for bulk actions", filtered_df['id'].tolist())
        
        if selected_users:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Activate Selected"):
                    # Implement bulk activation
                    st.success(f"Activated {len(selected_users)} users")
            
            with col2:
                if st.button("Deactivate Selected"):
                    # Implement bulk deactivation
                    st.success(f"Deactivated {len(selected_users)} users")
            
            with col3:
                new_role = st.selectbox("Change Role", ["user", "volunteer", "superuser"])
                if st.button("Update Role"):
                    # Implement bulk role update
                    st.success(f"Updated role for {len(selected_users)} users")
        
        # Users table
        st.dataframe(
            filtered_df[['username', 'email', 'full_name', 'role', 'language_preference', 'is_active', 'created_at']],
            use_container_width=True
        )
    
    else:
        st.error("Failed to load users")

def show_conversations():
    """Show conversation management"""
    st.header("💬 Conversation Management")
    
    # Get conversations
    conversations_data = get_conversations()
    
    if conversations_data:
        conversations_df = pd.DataFrame(conversations_data['conversations'])
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            language_filter = st.selectbox("Filter by Language", ["All"] + list(conversations_df['language'].unique()))
        
        with col2:
            date_filter = st.date_input("Filter by Date", value=None)
        
        # Display conversations
        st.subheader("Recent Conversations")
        
        for idx, conv in conversations_df.head(10).iterrows():
            with st.expander(f"Conversation {conv['id'][:8]} - {conv['language']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**User:** {conv.get('users', {}).get('username', 'Unknown')}")
                    st.write(f"**Language:** {conv['language']}")
                    st.write(f"**Created:** {conv['created_at']}")
                
                with col2:
                    if st.button("View Details", key=f"view_{conv['id']}"):
                        st.info("View conversation details (implement)")
    
    else:
        st.error("Failed to load conversations")

def show_faq_management():
    """Show FAQ management interface"""
    st.header("❓ FAQ Management")
    
    # Create new FAQ
    with st.expander("➕ Create New FAQ"):
        with st.form("create_faq"):
            col1, col2 = st.columns(2)
            
            with col1:
                question = st.text_area("Question", height=100)
                category = st.text_input("Category")
            
            with col2:
                answer = st.text_area("Answer", height=100)
                language = st.selectbox("Language", ["en", "hi", "ta", "te", "bn", "mr", "gu"])
            
            priority = st.slider("Priority", 1, 5, 1)
            
            if st.form_submit_button("Create FAQ"):
                # Implement FAQ creation
                st.success("FAQ created successfully!")
    
    # Manage existing FAQs
    faqs_data = get_faqs()
    
    if faqs_data:
        faqs_df = pd.DataFrame(faqs_data['faqs'])
        
        # FAQ filters
        col1, col2 = st.columns(2)
        
        with col1:
            category_filter = st.selectbox("Filter by Category", ["All"] + list(faqs_df['category'].unique()))
        
        with col2:
            language_filter = st.selectbox("Filter by Language", ["All"] + list(faqs_df['language'].unique()))
        
        # Display FAQs
        st.subheader("Existing FAQs")
        
        for idx, faq in faqs_df.iterrows():
            with st.expander(f"{faq['question'][:50]}... - {faq['language']}"):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**Question:** {faq['question']}")
                    st.write(f"**Answer:** {faq['answer']}")
                    st.write(f"**Category:** {faq['category']} | **Priority:** {faq['priority']}")
                
                with col2:
                    if st.button("Edit", key=f"edit_{faq['id']}"):
                        st.info("Edit FAQ (implement)")
                    if st.button("Delete", key=f"delete_{faq['id']}"):
                        st.warning("Delete FAQ (implement)")
    
    else:
        st.error("Failed to load FAQs")

def show_analytics():
    """Show analytics dashboard"""
    st.header("📈 Analytics & Reports")
    
    # Time period selection
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Usage Trends", "🌍 Language Analysis", "🎯 Performance", "📱 Platform Stats"])
    
    with tab1:
        st.subheader("Usage Trends")
        
        # Mock data for demonstration
        dates = pd.date_range(start_date, end_date, freq='D')
        usage_data = pd.DataFrame({
            'Date': dates,
            'Conversations': [10 + i*2 + (i%7)*5 for i in range(len(dates))],
            'Messages': [25 + i*5 + (i%7)*10 for i in range(len(dates))]
        })
        
        fig = px.line(usage_data, x='Date', y=['Conversations', 'Messages'], 
                     title="Daily Usage Trends")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Language Analysis")
        
        # Mock language data
        lang_data = pd.DataFrame({
            'Language': ['English', 'Hindi', 'Tamil', 'Telugu', 'Bengali', 'Marathi', 'Gujarati'],
            'Usage': [45, 25, 12, 8, 5, 3, 2]
        })
        
        fig = px.bar(lang_data, x='Language', y='Usage', 
                    title="Language Usage Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time chart
            response_times = [0.5, 0.8, 1.2, 0.9, 1.1, 0.7, 0.6, 0.8, 1.0, 0.9]
            fig = px.line(y=response_times, title="Average Response Time (seconds)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Confidence scores
            confidence_scores = [0.85, 0.92, 0.78, 0.88, 0.91, 0.83, 0.89, 0.87, 0.90, 0.86]
            fig = px.bar(y=confidence_scores, title="Confidence Scores")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Platform Statistics")
        
        platform_data = pd.DataFrame({
            'Platform': ['Website Widget', 'WhatsApp', 'Mobile App'],
            'Users': [150, 89, 45],
            'Messages': [1250, 890, 340]
        })
        
        fig = px.bar(platform_data, x='Platform', y=['Users', 'Messages'], 
                    title="Usage by Platform", barmode='group')
        st.plotly_chart(fig, use_container_width=True)

def show_system_settings():
    """Show system settings"""
    st.header("🔧 System Settings")
    
    # System configuration
    with st.expander("⚙️ General Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("System Name", value="LACBOT")
            st.text_input("Default Language", value="en")
            st.number_input("Max Message Length", value=1000)
        
        with col2:
            st.number_input("Session Timeout (minutes)", value=30)
            st.number_input("Max Conversations per User", value=100)
            st.selectbox("Default AI Model", ["Mistral-7B", "GPT-3.5", "Custom"])
    
    # Notification settings
    with st.expander("🔔 Notification Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Enable Email Notifications", value=True)
            st.checkbox("Enable WhatsApp Notifications", value=True)
            st.checkbox("Enable Push Notifications", value=False)
        
        with col2:
            st.text_input("Admin Email", value="admin@college.edu")
            st.text_input("WhatsApp Number", value="+1234567890")
            st.number_input("Notification Batch Size", value=100)
    
    # Security settings
    with st.expander("🔒 Security Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Enable Two-Factor Authentication", value=False)
            st.checkbox("Require Strong Passwords", value=True)
            st.checkbox("Enable Rate Limiting", value=True)
        
        with col2:
            st.number_input("Rate Limit (requests/minute)", value=60)
            st.number_input("Session Timeout (minutes)", value=30)
            st.selectbox("Encryption Level", ["AES-256", "AES-128"])
    
    # Save settings
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
