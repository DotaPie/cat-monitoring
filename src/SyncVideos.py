import os
import os.path
from enum import Enum
from datetime import date
import time
import ftplib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ENUMS #
class UploadTarget(Enum):
    GOOGLE_DRIVE = 1
    FTP = 2

# GLOBALS #
fileManager = {}

'''
Example of file manager state:

-----------------------------------------------------
| absolute file path | timestamp | size (B) | ready |
-----------------------------------------------------
| /home/test1.txt    | 8.0000000 | 4        | True  |
| /home/test2.txt    | 24.000000 | 8        | False |
| /home/test3.txt    | 39.950000 | 128      | False |
-----------------------------------------------------

Whole file manager is simple map.
Description of parameters from table:
    - absolute file path: key of the map (with value as the list that consists of timestamp, size and ready)
    - timestampe: timestamp of the last increment of the file size
    - size: size of the file in bytes
    - ready: if "syncAvailableTimeoutSeconds" seconds has passed without being written into, file is flagged as true in this value and ready for sync

What is happening with 3 files?
Assume current timestamp is 40.000000 (CPU uptime).
File test1.txt was not written into for more than "syncAvailableTimeoutSeconds" seconds, so it has been flagged to sync.
File test2.txt was written into 16 seconds ago, which most likely means it is ready to sync, but "syncAvailableTimeoutSeconds" seconds has not passed yet.
File test3.txt was written into only couple of miliseconds ago, which most likely means it is actively being written into.  
'''

# CONF - GENERAL #
uploadTarget = UploadTarget.FTP
syncAvailableTimeoutSeconds = 30 # how many seconds file must not be written into to be flagged as ready to sync

# CONF - FTP #
HOSTNAME = "192.168.1.175"
USERNAME = "ftp-general"
PASSWORD = "sa)7@}do" 
targetFtpPath = "CatMonitoring/CatMonitoring" # note: if FTP is running on windows, you might want "\\" instead of '/'

# PATHS - LOCAL #
credentialsAndTokenPath = "/home/dotapie/CatMonitoring"
videosPath = "/home/dotapie/CatMonitoring/Videos"

def initGoogleDriveAndSyncFile(fileName = ""):
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    fullFilePath = f"{videosPath}/{fileName}"
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

        folder = service.files().create(body=file_metadata, fields="id").execute()

        folder_id = folder.get('id')
    else:
        folder_id = response['files'][0]['id']

    if not fileName == "":
        file_metadata = {
            "name": fileName,
            "parents": [folder_id]
        }

        media = MediaFileUpload(fullFilePath)
        upload_file = service.files().create(body=file_metadata,
                                            media_body = media,
                                            fields="id").execute()
        
        print(fullFilePath + " synced")

def fileManagerHandle():
    for fileName in os.listdir(videosPath):
        if not fileName.endswith(".filepart"):
            fullFilePath = f"{videosPath}/{fileName}"

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
    for fileName in os.listdir(videosPath):
        if not fileName.endswith(".filepart"):
            fullFilePath = f"{videosPath}/{fileName}"

            if fileManager[fullFilePath][2] == True:
                if uploadTarget == UploadTarget.GOOGLE_DRIVE:
                    try:
                        # just to check if google drive connection can be initiated (verifies creation of token.json, etc...)
                        initGoogleDriveAndSyncFile(fileName)
                    except Exception as e:
                        print("Google drive connection failed (" + repr(e) + ")")
                elif uploadTarget == UploadTarget.FTP:
                    try:
                        initFtpAndSyncFile(fileName)
                    except Exception as e:
                        print("FTP connection failed (" + repr(e) + ")") 

                # remove file from file manager
                fileManager.pop(fullFilePath)
                print(fullFilePath + " removed from file manager")
                
                os.remove(fullFilePath)
                print(fullFilePath + " deleted")
 
def getYYMMDD():
    return date.today().strftime("%Y%m%d")[2:]

def verifyDir(ftpServer):
    try:
        ftpResponse = ftpServer.mkd(f"{targetFtpPath}/{getYYMMDD()}")
        print("Creating directory")
    except:
        pass

def initFtpAndSyncFile(fileName = ""):
    fullFilePath = f"{videosPath}/{fileName}"

    ftpServer = ftplib.FTP(HOSTNAME, USERNAME, PASSWORD)
    ftpServer.encoding = "utf-8"

    verifyDir(ftpServer)

    if(fileName != ""):
        with open(fullFilePath, "rb") as file:
            ftpServer.storbinary(f"STOR {targetFtpPath}/{getYYMMDD()}/{fileName}", file) # note: if FTP is running on windows, you might want "\\" instead of '/'
            print(fullFilePath + " synced")

    ftpServer.quit()

def main(): 
    if uploadTarget == UploadTarget.GOOGLE_DRIVE:
        try:
            # just to check if google drive connection can be initiated (verifies creation of token.json, etc...)
            initGoogleDriveAndSyncFile()
            print("Google drive connection verified")
        except Exception as e:
            print("Google drive connection failed (" + repr(e) + ")")
    elif uploadTarget == UploadTarget.FTP:
        try:
            initFtpAndSyncFile()
            print("FTP connection verified")
        except Exception as e:
            print("FTP connection failed (" + repr(e) + ")") 

    while 1:
        # add new file to file manager, update timestamp if size changed, flag as available to sync if enaugh time without size change passes
        fileManagerHandle()

        # sync all available files to sync, delete file from file manager and delete file from system
        syncAndDeleteAvailableFiles()
                
        time.sleep(1)   

if __name__=="__main__": 
    main()       