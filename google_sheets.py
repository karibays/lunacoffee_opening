import os.path
import json
import requests
from loguru import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

class GoogleAPI:
    # Authenticates with Google and returns credentials
    def google_authenticate(self):
        creds = None
        if os.path.exists("jsons/token.json"):
            creds = Credentials.from_authorized_user_file("jsons/token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "jsons/credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("jsons/token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    # Refreshes the access token using the refresh token
    def refresh_token(self):
        creds = self.google_authenticate()
        if creds and creds.refresh_token:
            creds.refresh(Request())
            # Save the refreshed credentials
            with open("jsons/token.json", "w") as token:
                token.write(creds.to_json())
            logger.success("Token has been successfully refreshed.")
        else:
            logger.error("Failed to refresh token.")

    # addings new rows to google sheets
    def append_values(self, spreadsheet_id, range_name, value_input_option, values):
        creds = self.google_authenticate()
        try:
            service = build("sheets", "v4", credentials=creds)
            body = {"values": values}
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
            logger.success(
                f"{(result.get('updates').get('updatedCells'))} cells appended."
            )
            return result

        except HttpError as error:
            logger.error("Failed to append values to the sheet!!!")
            return error

    def get_column_values(self, spreadsheet_id, range_name):
        creds = self.google_authenticate()
        try:
            service = build("sheets", "v4", credentials=creds)
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result
        except HttpError as error:
            logger.error("Failed to get columns values")
            return error

    def check_id(self, user_id, spreadsheet_id):
        result = self.get_column_values(
            spreadsheet_id=spreadsheet_id,
            range_name='A2:A'
        )
        ids = [int(uid[0]) for uid in result['values']]  # type: ignore
        return int(user_id) in ids

    def is_token_expired(self):
        with open('jsons/token.json', 'r') as file:
            json_file = json.load(file)
            try:
                token = json_file['access_token']
            except:
                try:
                    token = json_file['token']
                except:
                    logger.error("Failed to read token.json. Check it out!")
                    return

            URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"
            params = {
                "access_token": token
            }

            response = requests.post(URL, data=params)
            try:
                expiricy = int(response.json()['expires_in'])
            except:
                expiricy = 0

            if expiricy < 60:
                return True
            return False

    def check_token_expicicy_and_refresh(self):
        is_expired = self.is_token_expired()
        if not is_expired:
            logger.info(f"Token's current state: {not is_expired}")
            return
        for i in range(5):
            if self.is_token_expired():
                logger.warning(f"Token has expired. Attempt: {i} to refresh it")
                self.refresh_token()
            else:
                logger.success('Token has been succesfully refreshed')
                break
        return self.is_token_expired()


# runs the script
if __name__ == "__main__":
    import time

    # for i in range(100):
    #     print('index:', i)
    #     print(GoogleAPI().refresh_token())
    #     time.sleep(2)

    GoogleAPI().append_values(
        spreadsheet_id="1zPZ0yC5iqtNpfFtmV_YJx2bEdvRcnukhplb3DQFUTqI",
        range_name='A:Z',
        value_input_option="USER_ENTERED",
        values=[[1,2,3,4]],
    ) # type: ignore
