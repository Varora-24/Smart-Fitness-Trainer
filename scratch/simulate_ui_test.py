import os
from dotenv import load_dotenv
load_dotenv('.env')

import streamlit as st
from unittest.mock import patch
import db
import auth

def test():
    client = auth.get_supabase_client()
    
    # Generate random emails
    import random, string
    r1 = ''.join(random.choices(string.ascii_lowercase, k=6))
    r2 = ''.join(random.choices(string.ascii_lowercase, k=6))
    email_a = f"{r1}@test.com"
    email_b = f"{r2}@test.com"
    
    print(f"Signing up User A: {email_a}")
    res_a = client.auth.sign_up({"email": email_a, "password": "Password123!"})
    user_a_id = res_a.user.id
    print(f"User A ID: {user_a_id}")
    
    print(f"Signing up User B: {email_b}")
    res_b = client.auth.sign_up({"email": email_b, "password": "Password123!"})
    user_b_id = res_b.user.id
    print(f"User B ID: {user_b_id}")
    
    print("Simulating User A UI Login...")
    with patch.dict("auth.st.session_state", {"supabase_session": res_a.session, "user_id": user_a_id}):
        print("User A logging a workout session...")
        session_id = db.save_session({}, "squat", user_id=user_a_id)
        print(f"User A started session ID: {session_id}")
        db.save_rep(session_id, {"exercise": "squat", "rep_score": 95})
        print("User A saved 1 rep.")
        db.update_session(session_id, {"total_reps": 1, "clean_reps": 1})
        
        history_a = db.get_history()
        print(f"User A history count: {len(history_a)}")
            
    print("Simulating User B UI Login...")
    with patch.dict("auth.st.session_state", {"supabase_session": res_b.session, "user_id": user_b_id}):
        history_b = db.get_history()
        print(f"User B history count: {len(history_b)}")
        if len(history_b) == 0:
            print("SUCCESS: User B cannot see User A's data via db.py clients!")
        else:
            print("FAIL: User B saw data!")

if __name__ == "__main__":
    test()
