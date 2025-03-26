import pickle
import time

# Replace this with your actual LinkedIn session cookie
linkedin_session_cookie = {
    "name": "li_at",
    "value": "your_session_cookie_value",
    "domain": ".linkedin.com",
    "path": "/",  # Set the path to '/'
    "secure": True,
    "httpOnly": True,
    "expiry": int(time.time()) + 60 * 60 * 24 * 365  # Set expiry to 1 year from now
}

# Save the cookie to the specified file
cookie_file = "cookies.pkl"
with open(cookie_file, "wb") as file:
    pickle.dump([linkedin_session_cookie], file)

print(f"Session cookie saved to {cookie_file}")