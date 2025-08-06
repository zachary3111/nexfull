import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import re

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SPREADSHEET_ID = '1IPoBslhi_eYLm-myOlOxUQGHXCHpxxJ66WZAK-BlxPI'
SHEET_NAME = "Real-Time Leads (Dup Checker)"  # Your sheet tab name

def main():
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

    # Get full spreadsheet with grid data for cell metadata
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, includeGridData=True).execute()

    # Find the target sheet
    sheet = None
    for s in spreadsheet['sheets']:
        if s['properties']['title'] == SHEET_NAME:
            sheet = s
            break

    if not sheet:
        print(f"Sheet '{SHEET_NAME}' not found.")
        return

    rows = sheet['data'][0].get('rowData', [])

    # Extract headers from first row
    headers = []
    if rows:
        first_row = rows[0].get('values', [])
        for cell in first_row:
            headers.append(cell.get('formattedValue', ''))

    # Extract all rows with cell values and hyperlinks
    all_data = []
    for row in rows[1:]:
        row_values = []
        for cell in row.get('values', []):
            value = cell.get('formattedValue', '')
            hyperlink = None

            # Check for hyperlinks in textFormatRuns (rich text)
            if 'textFormatRuns' in cell:
                for run in cell['textFormatRuns']:
                    if 'format' in run and 'link' in run['format'] and 'uri' in run['format']['link']:
                        hyperlink = run['format']['link']['uri']
                        break
            # Fallback to hyperlink field
            elif 'hyperlink' in cell:
                hyperlink = cell['hyperlink']

            if hyperlink:
                # Format value with hyperlink appended
                row_values.append(f"{value} ({hyperlink})")
            else:
                row_values.append(value)

        # Normalize row length to headers length
        while len(row_values) < len(headers):
            row_values.append('')
        if len(row_values) > len(headers):
            row_values = row_values[:len(headers)]

        all_data.append(row_values)

    df = pd.DataFrame(all_data, columns=headers)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns (with hyperlinks if present).")

    csv_filename = "most_recent_leads_with_hyperlinks.csv"
    df.to_csv(csv_filename, index=False)
    print(f"Saved data with hyperlinks to '{csv_filename}'.")

if __name__ == '__main__':
    main()
