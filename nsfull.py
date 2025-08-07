from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5173",
    "https://nexfull-frontend-ery2.vercel.app",
    "https://nexfull-frontend-ery2-1g22qmpfp-jehu-zachary-sedillos-projects.vercel.app",
    "https://nexfull-frontend-h4iu.vercel.app"
])

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"

@app.route("/generate-leads", methods=["GET"])
def generate_leads():
    try:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise Exception("Missing credentials.json on server.")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_console()  # ✅ Use console instead of browser
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, includeGridData=True).execute()

        return jsonify({"message": "Leads generated successfully"}), 200

    except Exception as e:
        return jsonify({"message": "Failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Backend is running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
