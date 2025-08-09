from flask import Flask, jsonify, Response
from flask_cors import CORS
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os, json, logging, csv
from io import StringIO

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CORS(app, origins=[
    "http://localhost:5173",
    "https://nexfull-frontend.vercel.app",
    "https://nexfull-frontend-h4iu.vercel.app",
    "https://nexfull-frontend-ery2.vercel.app"
], supports_credentials=True)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI')
SHEET_NAME = os.getenv('SHEET_NAME', "Real-Time Leads (Dup Checker)")

def build_sheets_service():
    token_env = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")
    if not token_env:
        raise RuntimeError("Missing GOOGLE_OAUTH_TOKEN_JSON env var (paste your full token.json here)")

    info = json.loads(token_env)
    # quick sanity check for OAuth token shape
    required = {"token_uri", "client_id", "client_secret"}
    if not required.issubset(info.keys()):
        raise RuntimeError("GOOGLE_OAUTH_TOKEN_JSON looks wrong (missing token_uri/client_id/client_secret).")

    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return build('sheets', 'v4', credentials=creds)

def get_google_sheets_data():
    try:
        service = build_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:Z"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        app.logger.exception("Google Sheets access error")
        return None

@app.route("/generate-leads", methods=["GET"])
def generate_leads():
    data = get_google_sheets_data()
    if data is None:
        return jsonify({"message": "Failed to fetch data"}), 500
    count = max(len(data) - 1, 0)  # minus header
    return jsonify({"message": "Leads generated successfully", "count": count}), 200

@app.route("/most_recent_leads_with_hyperlinks.csv", methods=["GET"])
def download_csv():
    data = get_google_sheets_data()
    if data is None:
        return jsonify({"error": "Unable to fetch Google Sheet data"}), 500

    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for row in data:
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=most_recent_leads_with_hyperlinks.csv"}
    )

@app.route("/_whoami")
def whoami():
    try:
        # identify which Gmail the token belongs to
        token_env = json.loads(os.environ["GOOGLE_OAUTH_TOKEN_JSON"])
        creds = Credentials.from_authorized_user_info(token_env, SCOPES)
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
        me = build('oauth2','v2', credentials=creds).userinfo().get().execute()
        return {"mode": "oauth_user", "email": me.get("email")}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Backend is running"}), 200
