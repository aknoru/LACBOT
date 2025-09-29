"""
Volunteer Dashboard - Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

# Page configuration
st.set_page_config(
    page_title="LACBOT - Volunteer Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #059669 0%, #10b981 100%);
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
        border-left: 4px solid #10b981;
    }
    .priority-high {
        border-left-color: #ef4444;
    }
    .priority-medium {
        border-left-color: #f59e0b;
    }
    .priority-low {
        border-left-color: #10b981;
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
        st.title("🔐 Volunteer Login")
        
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
                        if data.get("role") in ["volunteer", "superuser"]:
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.authenticated = True
                            st.session_state.user_info = data
                            st.rerun()
                        else:
                            st.error("Access denied. Volunteer privileges required.")
                    else:
                        st.error("Invalid credentials")
                        
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
        
        st.stop()

def get_flagged_messages():
    """Get messages requiring human intervention"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/messages/flagged", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch flagged messages: {str(e)}")
        return None

def get_conversations():
    """Get conversations"""
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

def get_feedback():
    """Get user feedback"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/admin/feedback", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to fetch feedback: {str(e)}")
        return None

def main():
    """Main dashboard function"""
    authenticate()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👥 LACBOT - Volunteer Dashboard</h1>
        <p>Monitor conversations and provide human support</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        page = st.selectbox(
            "Select Page",
            ["🚨 Flagged Messages", "💬 All Conversations", "📝 Feedback Review", "📊 My Activity", "🔧 Settings"]
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
    if page == "🚨 Flagged Messages":
        show_flagged_messages()
    elif page == "💬 All Conversations":
        show_conversations()
    elif page == "📝 Feedback Review":
        show_feedback_review()
    elif page == "📊 My Activity":
        show_activity_stats()
    elif page == "🔧 Settings":
        show_settings()

def show_flagged_messages():
    """Show messages requiring human intervention"""
    st.header("🚨 Messages Requiring Human Support")
    
    flagged_data = get_flagged_messages()
    
    if flagged_data and flagged_data['messages']:
        messages = flagged_data['messages']
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Flagged", len(messages))
        
        with col2:
            high_priority = len([m for m in messages if m.get('confidence_score', 0) < 0.3])
            st.metric("High Priority", high_priority, delta=None)
        
        with col3:
            recent_count = len([m for m in messages if 
                              datetime.fromisoformat(m['created_at'].replace('Z', '+00:00')) > 
                              datetime.now() - timedelta(hours=24)])
            st.metric("Last 24h", recent_count)
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            priority_filter = st.selectbox("Priority Filter", ["All", "High", "Medium", "Low"])
        
        with col2:
            language_filter = st.selectbox("Language Filter", ["All"] + 
                                         list(set([m.get('language', 'unknown') for m in messages])))
        
        with col3:
            time_filter = st.selectbox("Time Filter", ["All", "Last Hour", "Last 24h", "Last Week"])
        
        # Display flagged messages
        for idx, message in enumerate(messages):
            # Apply filters
            confidence = message.get('confidence_score', 0)
            
            if priority_filter == "High" and confidence >= 0.3:
                continue
            elif priority_filter == "Medium" and (confidence < 0.3 or confidence >= 0.7):
                continue
            elif priority_filter == "Low" and confidence < 0.7:
                continue
            
            if language_filter != "All" and message.get('language') != language_filter:
                continue
            
            # Time filter logic would go here
            
            # Priority color
            priority_class = "priority-high" if confidence < 0.3 else "priority-medium" if confidence < 0.7 else "priority-low"
            
            with st.expander(f"Message {idx + 1} - Confidence: {confidence:.1%} - {message.get('language', 'unknown')}"):
                st.markdown(f"""
                <div class="metric-card {priority_class}">
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**User Message:** {message['user_message']}")
                    st.write(f"**Bot Response:** {message['bot_response']}")
                    st.write(f"**Language:** {message.get('language', 'Unknown')}")
                    st.write(f"**Timestamp:** {message['created_at']}")
                    
                    if 'conversations' in message:
                        conv_info = message['conversations']
                        if 'users' in conv_info:
                            st.write(f"**User:** {conv_info['users'].get('username', 'Unknown')}")
                
                with col2:
                    st.write(f"**Confidence:** {confidence:.1%}")
                    
                    if st.button("Take Action", key=f"action_{message['id']}"):
                        show_message_action_modal(message)
                    
                    if st.button("Mark Resolved", key=f"resolve_{message['id']}"):
                        # Implement resolve functionality
                        st.success("Message marked as resolved!")
    
    else:
        st.success("🎉 No messages requiring human intervention!")
        st.info("All conversations are being handled successfully by the chatbot.")

def show_message_action_modal(message):
    """Show modal for taking action on a message"""
    st.subheader("Take Action on Message")
    
    with st.form(f"action_form_{message['id']}"):
        action_type = st.selectbox("Action Type", [
            "Provide Better Response",
            "Escalate to Supervisor",
            "Add to FAQ",
            "Update Knowledge Base",
            "Mark as Resolved"
        ])
        
        response_text = st.text_area("Your Response", height=100)
        
        notes = st.text_area("Internal Notes", height=80)
        
        submit = st.form_submit_button("Submit Action")
        
        if submit:
            # Implement action submission
            st.success("Action submitted successfully!")

def show_conversations():
    """Show all conversations"""
    st.header("💬 All Conversations")
    
    conversations_data = get_conversations()
    
    if conversations_data:
        conversations = conversations_data['conversations']
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Conversations", len(conversations))
        
        with col2:
            active_convos = len([c for c in conversations if 
                               datetime.fromisoformat(c['created_at'].replace('Z', '+00:00')) > 
                               datetime.now() - timedelta(hours=24)])
            st.metric("Active (24h)", active_convos)
        
        with col3:
            languages = set([c.get('language', 'unknown') for c in conversations])
            st.metric("Languages Used", len(languages))
        
        with col4:
            avg_messages = sum([c.get('message_count', 1) for c in conversations]) / len(conversations)
            st.metric("Avg Messages/Conv", f"{avg_messages:.1f}")
        
        # Search and filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search conversations")
        
        with col2:
            language_filter = st.selectbox("Language", ["All"] + list(languages))
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Most Recent", "Oldest", "Most Messages"])
        
        # Display conversations
        for idx, conv in enumerate(conversations[:20]):  # Limit to 20 for performance
            with st.expander(f"Conversation {conv['id'][:8]} - {conv.get('language', 'unknown')}"):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**Session ID:** {conv['session_id']}")
                    st.write(f"**Language:** {conv['language']}")
                    st.write(f"**Created:** {conv['created_at']}")
                    st.write(f"**Last Updated:** {conv['updated_at']}")
                    
                    if 'users' in conv:
                        st.write(f"**User:** {conv['users'].get('username', 'Unknown')}")
                
                with col2:
                    if st.button("View Details", key=f"view_conv_{conv['id']}"):
                        show_conversation_details(conv)
                    
                    if st.button("Take Over", key=f"takeover_{conv['id']}"):
                        st.info("Human takeover initiated (implement)")

def show_conversation_details(conversation):
    """Show detailed conversation view"""
    st.subheader(f"Conversation Details - {conversation['id'][:8]}")
    
    # Mock conversation messages
    messages = [
        {"type": "user", "message": "Hello, I need help with my fee payment", "timestamp": "2024-01-01T10:00:00Z"},
        {"type": "bot", "message": "I'd be happy to help you with fee payment. What specific information do you need?", "timestamp": "2024-01-01T10:00:05Z"},
        {"type": "user", "message": "When is the deadline for semester fees?", "timestamp": "2024-01-01T10:00:30Z"},
        {"type": "bot", "message": "The deadline for semester fees is March 15, 2024. You can pay online through the student portal.", "timestamp": "2024-01-01T10:00:35Z"},
    ]
    
    for msg in messages:
        if msg["type"] == "user":
            st.markdown(f"**👤 User:** {msg['message']}")
        else:
            st.markdown(f"**🤖 Bot:** {msg['message']}")
        
        st.caption(msg['timestamp'])
        st.markdown("---")

def show_feedback_review():
    """Show user feedback for review"""
    st.header("📝 Feedback Review")
    
    feedback_data = get_feedback()
    
    if feedback_data and feedback_data['feedback']:
        feedbacks = feedback_data['feedback']
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        avg_rating = sum([f.get('rating', 0) for f in feedbacks]) / len(feedbacks)
        
        with col1:
            st.metric("Total Feedback", len(feedbacks))
        
        with col2:
            st.metric("Average Rating", f"{avg_rating:.1f}/5")
        
        with col3:
            positive = len([f for f in feedbacks if f.get('rating', 0) >= 4])
            st.metric("Positive (4+ stars)", positive)
        
        with col4:
            negative = len([f for f in feedbacks if f.get('rating', 0) <= 2])
            st.metric("Negative (≤2 stars)", negative)
        
        # Rating distribution
        ratings = [f.get('rating', 0) for f in feedbacks]
        rating_df = pd.DataFrame({'Rating': ratings})
        
        fig = px.histogram(rating_df, x='Rating', bins=5, title="Rating Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Display feedback
        st.subheader("Recent Feedback")
        
        for idx, feedback in enumerate(feedbacks[:10]):
            with st.expander(f"Rating: {'⭐' * feedback.get('rating', 0)} - {feedback.get('created_at', 'Unknown date')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if 'messages' in feedback:
                        msg = feedback['messages']
                        st.write(f"**Original Query:** {msg.get('user_message', 'N/A')}")
                        st.write(f"**Bot Response:** {msg.get('bot_response', 'N/A')}")
                    
                    if feedback.get('feedback_text'):
                        st.write(f"**User Feedback:** {feedback['feedback_text']}")
                    
                    if 'users' in feedback:
                        st.write(f"**User:** {feedback['users'].get('username', 'Anonymous')}")
                
                with col2:
                    rating = feedback.get('rating', 0)
                    st.write(f"**Rating:** {'⭐' * rating}")
                    st.write(f"**Date:** {feedback.get('created_at', 'N/A')}")
                    
                    if st.button("Respond", key=f"respond_{feedback['id']}"):
                        show_feedback_response_modal(feedback)
    
    else:
        st.info("No feedback available for review.")

def show_feedback_response_modal(feedback):
    """Show modal for responding to feedback"""
    st.subheader("Respond to Feedback")
    
    with st.form(f"response_form_{feedback['id']}"):
        response_type = st.selectbox("Response Type", [
            "Thank you for feedback",
            "Apologize for issue",
            "Explain bot limitation",
            "Offer human support",
            "No response needed"
        ])
        
        response_text = st.text_area("Response Message", height=100)
        
        internal_notes = st.text_area("Internal Notes", height=80)
        
        submit = st.form_submit_button("Send Response")
        
        if submit:
            # Implement response sending
            st.success("Response sent successfully!")

def show_activity_stats():
    """Show volunteer activity statistics"""
    st.header("📊 My Activity Statistics")
    
    # Mock data for demonstration
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Messages Resolved", 45, delta=5)
    
    with col2:
        st.metric("Hours Active Today", 3.5, delta=0.5)
    
    with col3:
        st.metric("Average Response Time", "2.3 min", delta="-0.5 min")
    
    with col4:
        st.metric("User Satisfaction", "4.2/5", delta=0.3)
    
    # Activity chart
    st.subheader("Daily Activity")
    
    # Mock activity data
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
    activity_data = pd.DataFrame({
        'Date': dates,
        'Messages Resolved': [5, 8, 3, 12, 7, 9, 6],
        'Hours Active': [2, 3, 1.5, 4, 2.5, 3.5, 2]
    })
    
    fig = px.bar(activity_data, x='Date', y=['Messages Resolved', 'Hours Active'], 
                title="Daily Activity", barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Resolution Rate", "94%", delta="2%")
        st.metric("User Rating", "4.2/5", delta="0.3")
    
    with col2:
        st.metric("Avg Resolution Time", "2.3 min", delta="-0.5 min")
        st.metric("Escalation Rate", "6%", delta="-1%")

def show_settings():
    """Show volunteer settings"""
    st.header("🔧 Settings")
    
    # Notification preferences
    with st.expander("🔔 Notification Preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("High Priority Alerts", value=True)
            st.checkbox("New Feedback Notifications", value=True)
            st.checkbox("System Updates", value=True)
        
        with col2:
            st.checkbox("Email Notifications", value=True)
            st.checkbox("Push Notifications", value=False)
            st.checkbox("WhatsApp Notifications", value=False)
    
    # Working hours
    with st.expander("⏰ Working Hours"):
        col1, col2 = st.columns(2)
        
        with col1:
            start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            timezone = st.selectbox("Timezone", ["UTC", "IST", "EST", "PST"])
        
        with col2:
            end_time = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())
            max_messages = st.number_input("Max Messages per Day", value=50)
    
    # Language preferences
    with st.expander("🌍 Language Preferences"):
        languages = st.multiselect(
            "Languages you can support",
            ["English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati"],
            default=["English", "Hindi"]
        )
        
        primary_language = st.selectbox("Primary Language", languages)
    
    # Availability status
    with st.expander("📊 Availability Status"):
        current_status = st.selectbox("Current Status", [
            "Available",
            "Busy",
            "Away",
            "Offline"
        ])
        
        auto_status = st.checkbox("Auto-update status based on activity")
        
        status_message = st.text_area("Status Message", placeholder="e.g., Available for urgent queries only")
    
    # Save settings
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
