"""
Test script for AdPulseAI system
Run this to verify all components are working correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_login():
    print_section("Testing Login")
    
    # Test merchant login
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": "merchant1", "password": "user123"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   Token: {data['access_token'][:20]}...")
        print(f"   Role: {data['role']}")
        return data['access_token']
    else:
        print("❌ Login failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_ad_generation(token):
    print_section("Testing Ad Generation")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "product_info": "Wireless Earbuds Pro - Noise-cancelling, 30hr battery, ₹2,999",
        "voice": "Professional"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Ad generation successful!")
        print(f"   Status: {data['status']}")
        print(f"   Content preview: {data['content'][:100]}...")
        return True
    else:
        print("❌ Ad generation failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_get_customers(token):
    print_section("Testing Get Customers")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/customers",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Get customers successful!")
        print(f"   Total customers: {len(data['customers'])}")
        for customer in data['customers'][:3]:
            print(f"   - {customer['name']} ({customer['phone']})")
        return data['customers']
    else:
        print("❌ Get customers failed!")
        print(f"   Status: {response.status_code}")
        return []

def test_sms_campaign(token, customers):
    print_section("Testing SMS Campaign (Preview Only)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    customer_ids = [c['id'] for c in customers[:2]]  # Select first 2 customers
    
    payload = {
        "product_info": "Wireless Earbuds Pro - ₹2,999",
        "voice": "Professional",
        "customer_ids": customer_ids,
        "send_immediately": False  # Preview only
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sms/campaign",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SMS campaign generation successful!")
        print(f"   Campaign ID: {data['campaign_id']}")
        print(f"   Messages generated: {data['messages_generated']}")
        print(f"   Status: {'Sent' if data['messages_sent'] else 'Preview Only'}")
        print("\n   Message previews:")
        for msg in data['preview']:
            print(f"   - {msg['name']}: {msg['message'][:60]}...")
        return True
    else:
        print("❌ SMS campaign failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_cost_estimate(token):
    print_section("Testing SMS Cost Estimation")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/sms/cost-estimate?num_messages=100&region=India",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Cost estimation successful!")
        print(f"   Messages: {data['num_messages']}")
        print(f"   Region: {data['region']}")
        print(f"   Cost per SMS: ${data['cost_per_sms_usd']}")
        print(f"   Total cost: ${data['total_cost_usd']} (₹{data['total_cost_inr']})")
        return True
    else:
        print("❌ Cost estimation failed!")
        print(f"   Status: {response.status_code}")
        return False

def test_history(token):
    print_section("Testing History Retrieval")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/history",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ History retrieval successful!")
        print(f"   Total records: {len(data)}")
        if data:
            print(f"   Latest: {data[0].get('target_user', 'N/A')} at {data[0].get('timestamp', 'N/A')}")
        return True
    else:
        print("❌ History retrieval failed!")
        print(f"   Status: {response.status_code}")
        return False

def main():
    print("\n" + "🚀 "*20)
    print("   AdPulseAI System Test Suite")
    print("🚀 "*20)
    
    print("\n📋 Prerequisites:")
    print("   - Server running on http://localhost:8000")
    print("   - ENV_MODE=test in .env file")
    print("   - Sample data loaded in db.json")
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without valid token")
        return
    
    test_ad_generation(token)
    customers = test_get_customers(token)
    
    if customers:
        test_sms_campaign(token, customers)
    
    test_cost_estimate(token)
    test_history(token)
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests completed!")
    print("\n📝 Next steps:")
    print("   1. Open http://localhost:8000 in your browser")
    print("   2. Login with: merchant1 / user123")
    print("   3. Try generating ads and SMS campaigns")
    print("   4. Check the history sidebar")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   python -m uvicorn main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
