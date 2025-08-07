from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import csv
from io import StringIO

app = Flask(__name__)

CORS(app, 
     origins=[
         "http://localhost:5173",
         "https://nexfull-frontend-ery2.vercel.app",
         "https://nexfull-frontend-ery2-1g22qmpfp-jehu-zachary-sedillos-projects.vercel.app",
         "https://nexfull-frontend-h4iu.vercel.app",
         "https://nexfull-frontend.vercel.app"
     ],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin', 'X-Requested-With'],
     supports_credentials=True
)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"

def get_google_sheets_data():
    try:
        creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_NAME
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Google Sheets access error: {str(e)}")
        return None

@app.route("/most_recent_leads_with_hyperlinks.csv", methods=["GET"])
def get_csv():
    try:
        sheets_data = get_google_sheets_data()
        if not sheets_data:
            sheets_data = [["Name", "Email", "Company", "Phone", "Status"],
                           ["John Doe", "john@example.com", "Example Corp", "123-456-7890", "New"],
                           ["Jane Smith", "jane@company.com", "Company Inc", "987-654-3210", "Contacted"]]

        output = StringIO()
        writer = csv.writer(output)
        for row in sheets_data:
            writer.writerow(row)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=most_recent_leads_with_hyperlinks.csv",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate CSV: {str(e)}"}), 500

@app.route("/generate-leads", methods=["GET"])
def generate_leads():
    try:
        sheets_data = get_google_sheets_data()
        if sheets_data:
            return jsonify({
                "message": "Leads generated successfully",
                "count": len(sheets_data) - 1 if len(sheets_data) > 1 else 0
            }), 200
        else:
            return jsonify({
                "message": "Could not access Google Sheets. Please check credentials and permissions."
            }), 500
    except Exception as e:
        return jsonify({"message": "Failed to generate leads", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Backend is running"}), 200

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,Origin,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,POST,OPTIONS")
        return response
