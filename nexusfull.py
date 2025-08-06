from flask import Flask, jsonify
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"

@app.route("/generate-leads", methods=["GET"])
def generate_leads():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

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

    sheet = next((s for s in spreadsheet['sheets'] if s['properties']['title'] == SHEET_NAME), None)
    if not sheet:
        return jsonify({"error": f"Sheet '{SHEET_NAME}' not found."}), 404

    rows = sheet['data'][0].get('rowData', [])
    headers = [cell.get('formattedValue', '') for cell in rows[0].get('values', [])]
    all_data = []

    for row in rows[1:]:
        row_values = []
        for cell in row.get('values', []):
            value = cell.get('formattedValue', '')
            hyperlink = None
            if 'textFormatRuns' in cell:
                for run in cell['textFormatRuns']:
                    if 'format' in run and 'link' in run['format'] and 'uri' in run['format']['link']:
                        hyperlink = run['format']['link']['uri']
                        break
            elif 'hyperlink' in cell:
                hyperlink = cell['hyperlink']

            row_values.append(f"{value} ({hyperlink})" if hyperlink else value)

        while len(row_values) < len(headers):
            row_values.append('')
        all_data.append(row_values[:len(headers)])

    df = pd.DataFrame(all_data, columns=headers)
    df.to_csv("public/most_recent_leads_with_hyperlinks.csv", index=False)

    return jsonify({"message": "CSV generated successfully", "rows": len(df)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
