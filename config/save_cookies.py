import pickle
import time

# Replace this with your actual LinkedIn session cookie
linkedin_session_cookie = {
    "name": "li_at",
    "value": "AQEFARABAAAAABTmNB4AAAGV47nCiwAAAZYHxlTyTgAAs3VybjpsaTplbnRlcnByaXNlQXV0aFRva2VuOmVKeGpaQUFDTmpzakZSRE4rZnlkSUlpVy84VTRpeEhFS0QrZW5BQm1SQXR0YkdCZ0JBQ2FuZ2ZoXnVybjpsaTplbnRlcnByaXNlUHJvZmlsZToodXJuOmxpOmVudGVycHJpc2VBY2NvdW50OjEwNDczOTM2NCwxNjYxOTQ3MDUpXnVybjpsaTptZW1iZXI6ODk1NTQyMjMxQtu6uC1VUumMpN1nkeqI3V_9co9PsDxdeDfHJRwVOi7tiS9x54V7cBiYDQFenINDp1i36KzBMe1Gjo8oRBmEjchnf1flOFCBjou9dnGPMQuDz_F7tWOJFNYOj4Ppp0uNq2EGHkjw2whP9TMUSRcduSh--O9RU8jDdqY0amkP9ZXg7IZFHbLjp-E1RPasXGQmry7UAw",
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