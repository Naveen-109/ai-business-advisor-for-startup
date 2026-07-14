#!/usr/bin/env python3
"""
Test Admin System - Verify admin login and dashboard functionality
"""

import requests
import json
from datetime import datetime

def test_admin_system():
    """Test the admin system functionality"""
    base_url = "http://localhost:5000"
    
    print("🔐 Testing Admin System")
    print("=" * 50)
    
    # Test 1: Admin login page access
    print("\n1. Testing admin login page access...")
    try:
        response = requests.get(f"{base_url}/admin/login")
        if response.status_code == 200:
            print("✅ Admin login page accessible")
        else:
            print(f"❌ Admin login page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing admin login: {e}")
    
    # Test 2: Test admin login with correct credentials
    print("\n2. Testing admin login with credentials...")
    session = requests.Session()
    
    try:
        # Get login page first (for CSRF if needed)
        login_page = session.get(f"{base_url}/admin/login")
        
        # Attempt login
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post(f"{base_url}/admin/login", data=login_data)
        
        if login_response.status_code == 200 or login_response.status_code == 302:
            print("✅ Admin login successful")
            
            # Test 3: Access admin dashboard
            print("\n3. Testing admin dashboard access...")
            dashboard_response = session.get(f"{base_url}/admin/dashboard")
            
            if dashboard_response.status_code == 200:
                print("✅ Admin dashboard accessible")
                
                # Check if dashboard contains expected content
                if "Admin Dashboard" in dashboard_response.text:
                    print("✅ Dashboard content loaded correctly")
                else:
                    print("⚠️ Dashboard content may be incomplete")
            else:
                print(f"❌ Admin dashboard failed: {dashboard_response.status_code}")
        else:
            print(f"❌ Admin login failed: {login_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error during admin login test: {e}")
    
    # Test 4: Test unauthorized access
    print("\n4. Testing unauthorized dashboard access...")
    try:
        unauthorized_session = requests.Session()
        dashboard_response = unauthorized_session.get(f"{base_url}/admin/dashboard")
        
        if dashboard_response.status_code == 302:  # Should redirect to login
            print("✅ Unauthorized access properly blocked")
        else:
            print(f"⚠️ Unauthorized access response: {dashboard_response.status_code}")
    except Exception as e:
        print(f"❌ Error testing unauthorized access: {e}")
    
    # Test 5: Check main site admin link
    print("\n5. Testing main site admin link...")
    try:
        main_page = requests.get(f"{base_url}/")
        if "Admin Access" in main_page.text:
            print("✅ Admin access link present on main site")
        else:
            print("⚠️ Admin access link not found on main site")
    except Exception as e:
        print(f"❌ Error checking main site: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Admin System Test Complete!")
    print("\n📋 Admin Access Information:")
    print(f"   • Admin Login URL: {base_url}/admin/login")
    print(f"   • Admin Dashboard: {base_url}/admin/dashboard")
    print(f"   • Default Username: admin")
    print(f"   • Default Password: admin123")
    print(f"   • Main Site: {base_url}/")
    
    print("\n🔧 To change admin credentials:")
    print("   Set environment variables:")
    print("   • ADMIN_USERNAME=your_admin_username")
    print("   • ADMIN_PASSWORD=your_secure_password")

if __name__ == "__main__":
    test_admin_system()