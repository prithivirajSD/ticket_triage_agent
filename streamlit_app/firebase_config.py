"""Firebase web configuration used by the Streamlit UI."""

import json
import os
from textwrap import dedent

FIREBASE_WEB_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
}


def firebase_analytics_snippet() -> str:
    """Return the JS snippet needed to initialize Firebase Analytics."""
    config_json = json.dumps(FIREBASE_WEB_CONFIG)
    return dedent(
        f"""
        <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-analytics-compat.js"></script>
        <script>
          const firebaseConfig = {config_json};
          if (!window.firebaseAppsInitialized) {{
            const app = firebase.initializeApp(firebaseConfig);
            firebase.analytics(app);
            window.firebaseAppsInitialized = true;
          }}
        </script>
        """
    ).strip()
