import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import time

SCOPES = ["https://www.googleapis.com/auth/drive"]

# CONF #
syncAvailableTimeoutSeconds = 300 # how many seconds file must not be written into to be flagged as ready to sync

# PATHS #
credentialsAndTokenPath = "/home/dotapie/CatMonitoring"
videosPath = "/home/dotapie/CatMonitoring/Videos"

fileManager = {}

def initGoogleDriveAndSyncFile(file = ""):
    fullFilePath = f"{videosPath}/{file}"
    creds = None

    if os.path.exists(credentialsAndTokenPath + "/token.json"):
        creds = Credentials.from_authorized_user_file(credentialsAndTokenPath + "/token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentialsAndTokenPath + "/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(credentialsAndTokenPath + '/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        response = service.files().list(
            q="name='CatMonitoring' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute()

        if not response['files']:
            file_metadata = {
                "name": "CatMonitoring",
                "mimeType": "application/vnd.google-apps.folder"
            }

            file = service.files().create(body=file_metadata, fields="id").execute()

            folder_id = file.get('id')
        else:
            folder_id = response['files'][0]['id']

        if not file == "":
            file_metadata = {
                "name": file,
                "parents": [folder_id]
            }

            media = MediaFileUpload(fullFilePath)
            upload_file = service.files().create(body=file_metadata,
                                                media_body = media,
                                                fields="id").execute()
            
            print(fullFilePath + " synced")
            
    except HttpError as e:
        print("Error: " + str(e))

def fileManagerHandle():
    for file in os.listdir(videosPath):
        if not file.endswith(".filepart"):
            fullFilePath = f"{videosPath}/{file}"

            # add file
            if not fullFilePath in fileManager:
                fileManager[fullFilePath] = [time.time(), os.path.getsize(fullFilePath), False]
                print(fullFilePath + " added to file manager")

            # update time if file was written into
            size = os.path.getsize(fullFilePath)

            if size > fileManager[fullFilePath][1]:
                fileManager[fullFilePath][0] = time.time()
                fileManager[fullFilePath][1] = size
                print(fullFilePath + " was written into")
                
            # flag file as ready to sync if enaugh seconds elapsed
            if time.time() - fileManager[fullFilePath][0] > syncAvailableTimeoutSeconds and fileManager[fullFilePath][2] == False:
                fileManager[fullFilePath][2] = True  
                print(fullFilePath + " flagged as available") 

def syncAndDeleteAvailableFiles():
    # sync files that are flagged to sync
    for file in os.listdir(videosPath):
        if not file.endswith(".filepart"):
            fullFilePath = f"{videosPath}/{file}"

            if fileManager[fullFilePath][2] == True:
                initGoogleDriveAndSyncFile(file)

                # remove file from file manager
                fileManager.pop(fullFilePath)
                print(fullFilePath + " removed from file manager")
                
                os.remove(fullFilePath)
                print(fullFilePath + " deleted")
 
def main(): 
    # just to check if google drive connection can be initiated (verifies creation of token.json, etc...)
    initGoogleDriveAndSyncFile()
    print("Google drive connection verified")

    while 1:
        # add new file to file manager, update timestamp if size changed, flag as available to sync if enaugh time without size change passes
        fileManagerHandle()

        # sync all available files to sync, delete file from file manager and delete file from system
        syncAndDeleteAvailableFiles()
                
        time.sleep(1)   

if __name__=="__main__": 
    main()       