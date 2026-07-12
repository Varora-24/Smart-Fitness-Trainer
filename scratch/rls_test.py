import random
import string
from supabase import create_client, Client

def get_secret(key):
    # Try to read from .env if available
    with open(".env", "r") as f:
        for line in f:
            if line.startswith(key + "="):
                return line.strip().split("=", 1)[1].strip("'\"")
    return None

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_test():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Could not load Supabase credentials.")
        return
        
    clientA: Client = create_client(url, key)
    clientB: Client = create_client(url, key)
    
    email_a = f"user_{random_string()}@gmail.com"
    email_b = f"user_{random_string()}@gmail.com"
    password = "TestPassword123!"
    
    print(f"Signing up User A: {email_a}")
    res_a = clientA.auth.sign_up({"email": email_a, "password": password})
    print(f"Session A: {res_a.session}")
    user_a_id = res_a.user.id
    
    print(f"User A ID: {user_a_id}")
    
    print("Logging workout data for User A...")
    # Insert session for user A
    session_res = clientA.table("sessions").insert({
        "user_id": user_a_id,
        "exercise": "squats",
        "total_reps": 10,
        "clean_reps": 8,
        "started_at": "2026-07-10T12:00:00Z"
    }).execute()
    
    session_id = session_res.data[0]['id']
    print(f"Created Session ID {session_id} for User A")
    
    # Insert reps for user A
    clientA.table("reps").insert([{
        "session_id": session_id,
        "exercise": "squats",
        "rep_score": 90.0,
        "rep_label": "good_rep",
        "created_at": "2026-07-10T12:01:00Z"
    }]).execute()
    print("Inserted 1 rep for User A")
    
    print(f"Signing up User B: {email_b}")
    res_b = clientB.auth.sign_up({"email": email_b, "password": password})
    user_b_id = res_b.user.id
    print(f"User B ID: {user_b_id}")
    
    print("Querying History as User B...")
    b_sessions = clientB.table("sessions").select("*").execute()
    b_reps = clientB.table("reps").select("*").execute()
    
    print(f"Sessions visible to User B: {len(b_sessions.data)}")
    print(f"Reps visible to User B: {len(b_reps.data)}")
    
    if len(b_sessions.data) == 0 and len(b_reps.data) == 0:
        print("SUCCESS: RLS is working perfectly. User B sees 0 of User A's data.")
    else:
        print("FAIL: User B can see other users' data!")

if __name__ == "__main__":
    run_test()
