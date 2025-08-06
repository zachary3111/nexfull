from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import re

app = Flask(__name__)

# Wide CORS config to debug Render issues
CORS(app, supports_credentials=True)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"

@app.route("/generate-leads", methods=["GET"])
@cross_origin(origin='https://nexfull-frontend-ery2.vercel.app', credentials=True)
def generate_leads():
    try:
        creds = None
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, includeGridData=True).execute()

        return jsonify({"message": "Leads generated successfully"}), 200

    except Exception as e:
        return jsonify({"message": "Failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
@cross_origin(origin='https://nexfull-frontend-ery2.vercel.app', credentials=True)
def root():
    return jsonify({"message": "Backend is running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
