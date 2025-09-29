import React from 'react';

function App() {
  return (
    <div className="demo-container">
      <h1>🎓 LACBOT</h1>
      <p>Campus Multilingual Chatbot - Demo Page</p>
      
      <div className="demo-features">
        <div className="feature-card">
          <h3>🌍 Multilingual Support</h3>
          <p>Supports Hindi, English, Tamil, Telugu, Bengali, Marathi, and Gujarati</p>
        </div>
        
        <div className="feature-card">
          <h3>🤖 AI-Powered</h3>
          <p>RAG-based implementation with 99% accuracy for student queries</p>
        </div>
        
        <div className="feature-card">
          <h3>📱 Multi-Platform</h3>
          <p>Available on website widget and WhatsApp for maximum accessibility</p>
        </div>
        
        <div className="feature-card">
          <h3>🔒 Secure & Private</h3>
          <p>End-to-end encryption with Supabase for data protection</p>
        </div>
        
        <div className="feature-card">
          <h3>👥 Role-Based Access</h3>
          <p>Separate dashboards for super users, volunteers, and students</p>
        </div>
        
        <div className="feature-card">
          <h3>📊 Analytics & Insights</h3>
          <p>Comprehensive analytics for continuous improvement</p>
        </div>
      </div>
      
      <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '8px' }}>
        <p><strong>Try the chatbot!</strong> Click the chat button in the bottom-right corner to start a conversation.</p>
        <p style={{ fontSize: '0.9rem', opacity: '0.8' }}>
          The chatbot can help with fee deadlines, scholarship forms, timetable changes, and other campus-related queries.
        </p>
      </div>
    </div>
  );
}

export default App;
