import os
from supabase import create_client

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    client1 = create_client(url, key)
    client2 = create_client(url, key)
    
    # 1. Sign up test account A
    import uuid
    email_a = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res_a = client1.auth.sign_up({"email": email_a, "password": "Password123!"})
    print(f"1. Signed up User A: {res_a.user.email} (ID: {res_a.user.id})")
    
    # Insert profile for A
    client1.table("profiles").insert({"id": res_a.user.id, "display_name": "User A"}).execute()
    
    # Log workout data for A
    session_res = client1.table("sessions").insert({"user_id": res_a.user.id, "start_time": "2026-07-12T10:00:00"}).execute()
    session_id = session_res.data[0]["id"]
    client1.table("reps").insert({"session_id": session_id, "exercise_name": "squat", "rep_count": 10}).execute()
    print(f"2. Logged workout data for User A. Session ID: {session_id}")
    
    # Sign up test account B
    email_b = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res_b = client2.auth.sign_up({"email": email_b, "password": "Password123!"})
    print(f"3. Signed up User B: {res_b.user.email} (ID: {res_b.user.id})")
    client2.table("profiles").insert({"id": res_b.user.id, "display_name": "User B"}).execute()
    
    # Check B's history
    print("\n--- Checking User B's View ---")
    b_sessions = client2.table("sessions").select("*").execute()
    b_reps = client2.table("reps").select("*").execute()
    print(f"Sessions visible to User B: {len(b_sessions.data)}")
    print(f"Reps visible to User B: {len(b_reps.data)}")
    
    # Clean up (using service role or we just leave them since it's a test DB)

if __name__ == "__main__":
    main()
