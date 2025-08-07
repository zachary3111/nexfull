from flask import Flask, jsonify, Response
from flask_cors import CORS
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv
from io import StringIO

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5173",
    "https://nexfull-frontend.vercel.app",
    "https://nexfull-frontend-h4iu.vercel.app",
    "https://nexfull-frontend-ery2.vercel.app"
], supports_credentials=True)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"

def get_google_sheets_data():
    try:
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_NAME
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Google Sheets access error: {str(e)}")
        return None

@app.route("/generate-leads", methods=["GET"])
def generate_leads():
    data = get_google_sheets_data()
    if data:
        return jsonify({"message": "Leads generated successfully", "count": len(data)-1}), 200
    return jsonify({"message": "Failed to fetch data"}), 500

@app.route("/most_recent_leads_with_hyperlinks.csv", methods=["GET"])
def download_csv():
    data = get_google_sheets_data()
    if not data:
        return jsonify({"error": "Unable to fetch Google Sheet data"}), 500

    output = StringIO()
    writer = csv.writer(output)
    for row in data:
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=most_recent_leads_with_hyperlinks.csv"}
    )

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Backend is running"}), 200
