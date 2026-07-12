import os, random, string
from dotenv import load_dotenv
load_dotenv('.env')
import auth
import db
from unittest.mock import patch

def run():
    client = auth.get_supabase_client()
    r1 = ''.join(random.choices(string.ascii_lowercase, k=6))
    r2 = ''.join(random.choices(string.ascii_lowercase, k=6))
    e1 = f'{r1}@gmail.com'
    e2 = f'{r2}@gmail.com'
    
    try:
        res1 = client.auth.sign_up({'email': e1, 'password': 'Password123!'})
        res2 = client.auth.sign_up({'email': e2, 'password': 'Password123!'})
    except Exception as e:
        print(f"API Rate limit hit: {e}")
        return

    print('User A logging workout...')
    with patch.dict('auth.st.session_state', {'supabase_session': res1.session, 'user_id': res1.user.id}):
        session_id = db.save_session({}, 'squat', res1.user.id)
        db.save_rep(session_id, {'exercise': 'squat'})
        db.update_session(session_id, {"total_reps": 1})
        print(f'User A history count: {len(db.get_history())}')

    print('User B checking history...')
    with patch.dict('auth.st.session_state', {'supabase_session': res2.session, 'user_id': res2.user.id}):
        print(f'User B history count: {len(db.get_history())}')

if __name__ == '__main__':
    run()
