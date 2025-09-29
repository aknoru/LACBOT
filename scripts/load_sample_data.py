#!/usr/bin/env python3
"""
Script to load sample FAQs and documents into the LACBOT system
"""

import json
import os
import sys
import requests
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_supabase_client
from app.core.config import settings

def load_sample_faqs():
    """Load sample FAQs from JSON file"""
    print("📚 Loading sample FAQs...")
    
    try:
        # Load FAQs from JSON file
        faqs_file = Path(__file__).parent.parent / "data" / "sample_faqs.json"
        
        if not faqs_file.exists():
            print(f"❌ FAQ file not found: {faqs_file}")
            return False
        
        with open(faqs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        supabase = get_supabase_client()
        
        # Insert FAQs
        for faq in data['faqs']:
            try:
                result = supabase.table('faqs').insert({
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'category': faq['category'],
                    'language': faq['language'],
                    'priority': faq['priority'],
                    'is_active': True
                }).execute()
                
                print(f"✅ Added FAQ: {faq['question'][:50]}...")
                
            except Exception as e:
                print(f"❌ Failed to add FAQ: {e}")
                continue
        
        print(f"✅ Successfully loaded {len(data['faqs'])} FAQs")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load FAQs: {e}")
        return False

def load_sample_documents():
    """Load sample documents"""
    print("📄 Loading sample documents...")
    
    try:
        supabase = get_supabase_client()
        
        # Sample documents
        sample_docs = [
            {
                'title': 'Academic Calendar 2024',
                'content': 'The academic calendar for 2024 includes important dates for semester start, exams, holidays, and fee payment deadlines. First semester begins on July 15, 2024. Mid-semester exams are scheduled for September 15-30, 2024. End semester exams are from November 15-30, 2024. Winter vacation is from December 20, 2024 to January 5, 2025.',
                'language': 'en',
                'document_type': 'academic_calendar'
            },
            {
                'title': 'Fee Structure 2024',
                'content': 'Fee structure for academic year 2024-25: Tuition fee: ₹50,000 per semester. Library fee: ₹2,000 per year. Laboratory fee: ₹5,000 per semester (for science students). Hostel fee: ₹15,000 per semester (single room), ₹12,000 per semester (double room). Mess charges: ₹3,000 per month. Late fee penalty: ₹500 per week after due date.',
                'language': 'en',
                'document_type': 'fee_structure'
            },
            {
                'title': 'Scholarship Guidelines',
                'content': 'Scholarship guidelines for students: Merit scholarships are available for top 10% students based on previous semester performance. Need-based scholarships require income certificate below ₹5 lakhs annually. Application deadline is April 30, 2024. Documents required: Mark sheet, income certificate, caste certificate (if applicable), bank account details.',
                'language': 'en',
                'document_type': 'scholarship'
            },
            {
                'title': 'Library Rules and Regulations',
                'content': 'Library rules: Students can borrow up to 5 books for 15 days. Reference books cannot be borrowed. Late return charges: ₹10 per day per book. Library hours: 8 AM to 8 PM (Monday to Friday), 9 AM to 5 PM (Saturday), Closed on Sunday. Students must maintain silence in the library. Mobile phones should be switched off.',
                'language': 'en',
                'document_type': 'library_rules'
            },
            {
                'title': 'Hostel Rules and Regulations',
                'content': 'Hostel rules: Curfew time is 10 PM for all students. Visitors are not allowed in rooms after 8 PM. Students must maintain cleanliness in rooms and common areas. Cooking is not allowed in rooms. Students must inform warden before going out overnight. Hostel fees must be paid on time to avoid penalties.',
                'language': 'en',
                'document_type': 'hostel_rules'
            }
        ]
        
        for doc in sample_docs:
            try:
                result = supabase.table('documents').insert({
                    'title': doc['title'],
                    'content': doc['content'],
                    'language': doc['language'],
                    'document_type': doc['document_type'],
                    'created_by': 'system'
                }).execute()
                
                print(f"✅ Added document: {doc['title']}")
                
            except Exception as e:
                print(f"❌ Failed to add document: {e}")
                continue
        
        print(f"✅ Successfully loaded {len(sample_docs)} documents")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load documents: {e}")
        return False

def create_sample_users():
    """Create sample users for testing"""
    print("👥 Creating sample users...")
    
    try:
        supabase = get_supabase_client()
        
        # Sample users
        sample_users = [
            {
                'email': 'admin@college.edu',
                'username': 'admin',
                'full_name': 'System Administrator',
                'role': 'superuser',
                'language_preference': 'en',
                'is_active': True
            },
            {
                'email': 'volunteer1@college.edu',
                'username': 'volunteer1',
                'full_name': 'John Doe',
                'role': 'volunteer',
                'language_preference': 'en',
                'is_active': True
            },
            {
                'email': 'volunteer2@college.edu',
                'username': 'volunteer2',
                'full_name': 'Priya Sharma',
                'role': 'volunteer',
                'language_preference': 'hi',
                'is_active': True
            },
            {
                'email': 'student1@college.edu',
                'username': 'student1',
                'full_name': 'Alice Johnson',
                'role': 'user',
                'language_preference': 'en',
                'is_active': True
            },
            {
                'email': 'student2@college.edu',
                'username': 'student2',
                'full_name': 'Raj Patel',
                'role': 'user',
                'language_preference': 'hi',
                'is_active': True
            }
        ]
        
        for user in sample_users:
            try:
                # Check if user already exists
                existing = supabase.table('users').select('id').eq('email', user['email']).execute()
                
                if existing.data:
                    print(f"⚠️ User already exists: {user['email']}")
                    continue
                
                # Create user (without password for demo)
                result = supabase.table('users').insert(user).execute()
                
                print(f"✅ Created user: {user['full_name']} ({user['role']})")
                
            except Exception as e:
                print(f"❌ Failed to create user: {e}")
                continue
        
        print(f"✅ Successfully created sample users")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create users: {e}")
        return False

def main():
    """Main function to load all sample data"""
    print("🎓 LACBOT Sample Data Loader")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Please run setup.py first.")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    success_count = 0
    total_tasks = 3
    
    # Load sample data
    if load_sample_faqs():
        success_count += 1
    
    if load_sample_documents():
        success_count += 1
    
    if create_sample_users():
        success_count += 1
    
    print("\n" + "=" * 40)
    print(f"✅ Completed {success_count}/{total_tasks} tasks successfully")
    
    if success_count == total_tasks:
        print("🎉 All sample data loaded successfully!")
        print("\nNext steps:")
        print("1. Start the application: python start_dev.py")
        print("2. Access the dashboards:")
        print("   - Super User: http://localhost:8501")
        print("   - Volunteer: http://localhost:8502")
        print("3. Test the chatbot at: http://localhost:3000")
    else:
        print("⚠️ Some tasks failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
