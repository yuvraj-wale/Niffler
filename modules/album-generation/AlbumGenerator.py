import csv
import json
import os
import shutil
import requests
import pydicom
import pymongo
import logging

from urllib3 import encode_multipart_formdata

def read_system_config():
    """
    Read the system configuration from the "system.json" file.
    """
    with open("config.json", "r") as file:
        return json.load(file)

def read_filter_criteria_csv(csv_file_path):
    """
    Read the filter criteria from the specified CSV file.
    """
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]
    
# [TO DO:]
# METADATA QUERYING AND SUBSET CREATION/IDENTIFICATION FUNCTIONALITY (PROGRESS : NOT YET IMPLEMENTED) =>

# def create_subset_folder(source_folder, subset_folder, mongo_uri, filter_criteria):
#     """
#     Perform metadata querying and identify the subset of files to be copied to the subset folder.
#     """
#     client = pymongo.MongoClient(mongo_uri)
#     db = client.dicom_metadata_db
#     collection = db.metadata

#     filtered_metadata = collection.find(filter_criteria)

#     if not os.path.exists(subset_folder):
#         os.makedirs(subset_folder)

#     for metadata in filtered_metadata:
#         study_instance_uid = metadata.get("StudyInstanceUID")

#         for root, dirs, files in os.walk(source_folder):
#             for filename in files:
#                 if filename.endswith('.dcm'):
#                     dicom_file_path = os.path.join(root, filename)
#                     if pydicom.read_file(dicom_file_path).StudyInstanceUID == study_instance_uid:
#                         destination_folder = os.path.join(
#                             subset_folder,
#                             os.path.relpath(os.path.dirname(dicom_file_path), source_folder)
#                         )

#                         if not os.path.exists(destination_folder):
#                             os.makedirs(destination_folder)

#                         shutil.copy(dicom_file_path, destination_folder)
#                         logging.info(f"Copied: {dicom_file_path} to {destination_folder}")


def authenticate(keycloak_url, realm_name, client_id, username, password):
    """
    Authenticate and generate an access token from the KHEOPS server.
    """
    token_url = f'{keycloak_url}/auth/realms/{realm_name}/protocol/openid-connect/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'password',
        'client_id': client_id,
        'username': username,
        'password': password,
        'scope': 'kheops'
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()  # Raise an exception if the response status is an error code
        response_data = response.json()
        access_token = response_data['access_token']
        return access_token
    except requests.exceptions.RequestException as e:
        raise Exception(f'Authentication failed, {str(e)}.')
    
def create_album(kheops_url, kheops_access_token, name, description=''):
    """
    Create a new album on the KHEOPS server.
    """
    url = f"{kheops_url}/api/albums"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'name': name[:255],
        'description': description[:2048],
    }
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()

    album=response.json()
    album_id = album.get("album_id")
    name = album.get("name")
    description = album.get("description")
    album_data=f""" Album created succesfully!             
           - Album ID: {album_id}
           - Name: {name}
           - Description: {description}"""

    if response.status_code == 201:
        logging.info("-" * 80)
        logging.info(album_data)
        logging.info("-" * 80)
        return album.get("album_id")
    elif response.status_code == 404:
        raise Exception('Album creation failed, User not found.')
    else:
        raise Exception('Album creation failed.')

def generate_album_shareable_link(kheops_url, album_id, kheops_access_token):
    """
    Generate a shareable link to an album by creating a capability token.
    """
    url = f"{kheops_url}/api/capabilities"
    headers = {
            "Authorization": f"Bearer {kheops_access_token}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
            "title": "title",
            "scope_type": "album",
            "album": album_id,
            "read_permission": "true",
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 201:
            json_data = response.json()
            capability_token = json_data["secret"]
            shareable_link = f"{kheops_url}/view/{capability_token}"
            logging.info("-" * 80)
            logging.info(" Shareable link generated!")
            logging.info(" NOTE: the link expires in 3 days")
            logging.info(" Shareable link: %s", shareable_link)
            logging.info("-" * 80)
    elif response.status_code == 400:
        raise Exception("Failed to generate shareable album link, Invalid parameters.")
    elif response.status_code == 401:
        raise Exception("Failed to generate shareable album link, User is not authorized as an admin of the album.")
    elif response.status_code == 404:
        raise Exception("Failed to generate shareable album link, Album not found.")
    else:
        raise Exception("Failed to generate shareable album link.")

def get_album_list(kheops_url, kheops_access_token):
    """
    Get a list of available albums.
    """
    url = f"{kheops_url}/api/albums"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    # Check the response status code.
    if response.status_code == 200:
            albums = response.json()
            logging.info(" List of Albums to choose from : ")
            logging.info("-" * 80)
            logging.info("| Index | Name | Album ID |")
            logging.info("-" * 80)
            for index, album in enumerate(albums, 1):
                album_id = album.get("album_id")
                name = album.get("name")
                description = album.get("description")
                created_time = album.get("created_time")
                modalities = album.get("modalities")

                # Format the album data for display
                album_data = f"| {index} | {name} | {album_id} |"

                # Display the album data in a pleasing format
                logging.info(album_data)
            logging.info("-" * 80)
    elif response.status_code == 400:
            raise Exception("Failed to retrieve the album list, Invalid parameters.")
    elif response.status_code == 404:
            raise Exception("Failed to retrieve the album list, Album not found.")
    else:
            raise Exception("Failed to retrieve the album list.")

def get_detailed_album_list(kheops_url, kheops_access_token):
    """
    Get a list of available albums.
    """
    url = f"{kheops_url}/api/albums"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
            albums = response.json()
            logging.info("List of Albums created : ")
            logging.info("-" * 80)
            for index, album in enumerate(albums, 1):
                album_id = album.get("album_id")
                name = album.get("name")
                description = album.get("description")
                created_time = album.get("created_time")
                modalities = album.get("modalities")
                no_of_users = album.get("number_of_users")
                no_of_comments = album.get("number_of_comments")
                no_of_atudies = album.get("number_of_studies")
                no_of_series = album.get("number_of_series")

                # Format the album data for display
                album_data = f"""{index}] Album ID: {album_id}                            
             Name: {name}
             Description: {description}
             Created Time: {created_time}
             Modalities: {modalities}
             Number of Users: {no_of_users}
             Number of Comments: {no_of_comments}
             Number of Studies: {no_of_atudies}
             Number of Series: {no_of_series}"""

                # Display the album data in a pleasing format
                logging.info(album_data)
                logging.info("-" * 80)
    elif response.status_code == 400:
            raise Exception("Failed to retrieve the album list, Invalid parameters.")
    elif response.status_code == 404:
            raise Exception("Failed to retrieve the album list, Album not found.")
    else:
            raise Exception("Failed to retrieve the album list.")

def delete_album(kheops_url, album_id, kheops_access_token):
    """
    Delete an album.
    """
    url = f"{kheops_url}/api/albums/{album_id}"
    headers = {
        'Authorization': f"Bearer {kheops_access_token}"
    }
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        logging.info(" Album deleted successfully!")
        logging.info("-" * 80)
    elif response.status_code == 403:
        raise Exception("Failed to delete album, User is not an admin.")
    elif response.status_code == 404:
        raise Exception("Failed to delete the album, User not found or album not found.")
    else:
        raise Exception("Failed to delete the album.")
    
def get_album_details(kheops_url, album_id, kheops_access_token):
    """
    Get album details for a specific album.
    """
    url = f"{kheops_url}/api/albums/{album_id}"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        album_data = response.json()

        # Extract the necessary details from the album_data
        album_details_ = {
            "album_id": album_data.get("album_id"),
            "name": album_data.get("name"),
            "description": album_data.get("description"),
            "created_time": album_data.get("created_time"),
            "last_event_time": album_data.get("last_event_time"),
            "number_of_users": album_data.get("number_of_users"),
            "modalities": album_data.get("modalities"),
            "number_of_comments": album_data.get("number_of_comments"),
            "number_of_studies": album_data.get("number_of_studies"),
            "number_of_series": album_data.get("number_of_series"),
            "add_user": album_data.get("add_user"),
            "download_series": album_data.get("download_series"),
            "send_series": album_data.get("send_series"),
            "delete_series": album_data.get("delete_series"),
            "add_series": album_data.get("add_series"),
            "write_comments": album_data.get("write_comments"),
            "is_favorite": album_data.get("is_favorite"),
            "notification_new_series": album_data.get("notification_new_series"),
            "notification_new_comment": album_data.get("notification_new_comment"),
            "is_admin": album_data.get("is_admin")
        }
        album_data = f"""Here are the album details! :
          - Album ID: {album_details_["album_id"]}
          - Name: {album_details_["name"]}
          - Description: {album_details_["description"]}
          - Created Time: {album_details_["created_time"]}
          - Last Event Time: {album_details_["last_event_time"]}
          - Number of Users: {album_details_["number_of_users"]}
          - Modalities: {album_details_["modalities"]}
          - Number of Comments: {album_details_["number_of_comments"]}
          - Number of Studies: {album_details_["number_of_studies"]}
          - Number of Series: {album_details_["number_of_series"]}
          - Add User: {album_details_["add_user"]}
          - Download Series: {album_details_["download_series"]}
          - Send Series: {album_details_["send_series"]}
          - Delete Series: {album_details_["delete_series"]}
          - Add Series: {album_details_["add_series"]}
          - Write Comments: {album_details_["write_comments"]}
          - Is Favorite: {album_details_["is_favorite"]}
          - Notification New Series: {album_details_["notification_new_series"]}
          - Notification New Comment: {album_details_["notification_new_comment"]}
          - Is Admin: {album_details_["is_admin"]}"""
        logging.info("-" * 80)
        logging.info(album_data)
        logging.info("-" * 80)
    elif response.status_code == 400:
        raise Exception("Failed to fetch the album details, Bad Request. Incorrect query parameters.")
    elif response.status_code == 403:
        raise Exception("Failed to fetch the album details, Forbidden. User can't see the users list.")
    elif response.status_code == 404:
        raise Exception("Failed to fetch the album details, User not found, album not found, or user is not a member of the album.")
    else:
        raise Exception("Failed to fetch the album details.")

def edit_album_settings(kheops_url, album_id, kheops_access_token, **kwargs): # name="",description="",add_user='',download_series='',send_series='',delete_series='',add_series='',write_comments='',notification_new_series='',notification_new_comment=''):
    """
    Edit an album with the provided parameters.
    """
    url = f"{kheops_url}/api/albums/{album_id}"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {}
    for key, value in kwargs.items():
        if value is not None:
            payload[key] = str(value).lower()
    logging.info(payload)
    response = requests.patch(url, headers=headers, data=payload)

    if response.status_code == 200:
        logging.info("reached")
        album_data_ = response.json()
        logging.info(album_data_)
        # Extract the necessary details from the album_data
        album_details_ = {
            "album_id": album_data_.get("album_id"),
            "name": album_data_.get("name"),
            "description": album_data_.get("description"),
            "created_time": album_data_.get("created_time"),
            "last_event_time": album_data_.get("last_event_time"),
            "number_of_users": album_data_.get("number_of_users"),
            "number_of_comments": album_data_.get("number_of_comments"),
            "number_of_studies": album_data_.get("number_of_studies"),
            "add_user": album_data_.get("add_user"),
            "download_series": album_data_.get("download_series"),
            "send_series": album_data_.get("send_series"),
            "delete_series": album_data_.get("delete_series"),
            "add_series": album_data_.get("add_series"),
            "write_comments": album_data_.get("write_comments"),
            "is_favorite": album_data_.get("is_favorite"),
            "notification_new_series": album_data_.get("notification_new_series"),
            "notification_new_comment": album_data_.get("notification_new_comment"),
            "is_admin": album_data_.get("is_admin")
        }
        # Format the album data for display
        display_data = f"""
          - Album ID: {album_details_["album_id"]}
          - Name: {album_details_["name"]}
          - Description: {album_details_["description"]}
          - Created Time: {album_details_["created_time"]}
          - Last Event Time: {album_details_["last_event_time"]}
          - Number of Users: {album_details_["number_of_users"]}
          - Number of Comments: {album_details_["number_of_comments"]}
          - Number of Studies: {album_details_["number_of_studies"]}
          - Add User: {album_details_["add_user"]}
          - Download Series: {album_details_["download_series"]}
          - Send Series: {album_details_["send_series"]}
          - Delete Series: {album_details_["delete_series"]}
          - Add Series: {album_details_["add_series"]}
          - Write Comments: {album_details_["write_comments"]}
          - Is Favorite: {album_details_["is_favorite"]}
          - Notification New Series: {album_details_["notification_new_series"]}
          - Notification New Comment: {album_details_["notification_new_comment"]}
          - Is Admin: {album_details_["is_admin"]}"""
        logging.info("-" * 80)
        logging.info("Album details updated successfully!")
        logging.info(display_data)
        logging.info("-" * 80)
    elif response.status_code == 403:
        raise Exception("Failed to edit the album, Forbidden. Only admins can edit albums.")
    elif response.status_code == 404:
        raise Exception("Failed to edit the album, Not Found. User not found, album not found, or user is not a member of the album.")
    else:
        raise Exception("Failed to edit the album.")
    
# [TO DO:]
# ADD STUDIES/SERIES FUNCTIONALITY (PROGRESS : DEBUGGING ISSUES) =>

# def add_studies_to_album(kheops_url, album_id, subset_folder_location, kheops_access_token):
#     """
#     Add studies to an album.
#     """
#     try:
#         study_instance_uid = get_study_instance_uid(subset_folder_location)
#         logging.info(study_instance_uid)
#         url = f"{kheops_url}/api/studies/{study_instance_uid}/albums/{album_id}"

#         series_files = []
#         for root, _, files in os.walk(subset_folder_location):
#             for file_name in files:
#                 file_path = os.path.join(root, file_name)
#                 if is_dicom_file(file_path):
#                     with open(file_path, 'rb') as file:
#                         file_data = file.read()
#                         series_files.append(('file', (file_name, file_data, 'application/dicom')))
#                     # logging.info("checkpoint 3")
#                     # series_files.append(('file', (file_name, open(file_path, 'rb'), 'application/dicom')))
#         logging.info("checkpoint 4")

#         body, content_type = encode_multipart_related(series_files)

#         headers = {
#             "Authorization": f"Bearer {kheops_access_token}",
#             "Accept": "application/dicom+json",
#             "Content-Type": content_type
#         }
        
#         response = requests.put(url, data=body, headers=headers)
#         logging.info(response.status_code)
#         response.raise_for_status()

#         if response.status_code == 201:
#             print("Study added to album successfully.")
#         elif response.status_code == 403:
#             print("User is not authorized to add series to the album.")
#         elif response.status_code == 404:
#             print("User not found, album not found, or study not present in the source.")
#         else:
#             print("Failed to add study to album.")    
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")

# def add_series(kheops_url, kheops_access_token, series_folder, study_instance_uid, series_instance_uid, album_id):
#     """
#     Add series to an album.
#     """
#     url = f"{kheops_url}/api/studies/{study_instance_uid}/series/{series_instance_uid}/albums/{album_id}"
#     headers = {
#         "Authorization": f"Bearer {kheops_access_token}",
#         # "X-Authorization-Source": f"Bearer {token}"  # Optional: Use this header if sending the series from another album
#     }

#     series_files = []
#     for root, _, files in os.walk(series_folder):
#         for file_name in files:
#             file_path = os.path.join(root, file_name)
#             if is_dicom_file(file_path):
#                 series_files.append(('file', (file_name, open(file_path, 'rb'))))

#     response = requests.put(url, headers=headers, files=series_files)

#     if response.status_code == 201:
#         print("Series added successfully.")
#     elif response.status_code == 403:
#         print("Access forbidden. User is not an admin or does not have 'addSeries' permission.")
#     elif response.status_code == 404:
#         print("Not found. User not found, album ID does not exist, user is not a member of the album, or series is not present.")
#     else:
#         print("An error occurred while adding the series.")

# def extract_study_instance_uid(dicom_file_path):
#     """
#     Extract the Study Instance UID from a DICOM file.
#     """
#     logging.info("checking 1")
#     ds = pydicom.dcmread(dicom_file_path)
#     study_instance_uid = ds.StudyInstanceUID
#     return study_instance_uid

# def get_study_instance_uid(study_folder_location):
#     """
#     Get the Study Instance UID from the study folder.
#     """
#     # Assuming the study folder contains DICOM files and the Study Instance UID is present in the DICOM metadata
#     logging.info("checking 2")
#     for root, _, files in os.walk(study_folder_location):
#         for filename in files:
#             dicom_file_path = os.path.join(root, filename)
#             if is_dicom_file(dicom_file_path):
#                 study_instance_uid = extract_study_instance_uid(dicom_file_path)
#                 return study_instance_uid

#     raise Exception("Study Instance UID not found in the study folder.")

# def is_dicom_file(file_path):
#     try:
#         dicom_file = pydicom.dcmread(file_path)
#         return True
#     except pydicom.errors.InvalidDicomError:
#         return False

# def encode_multipart_related(fields, boundary=None):
#     # if boundary is None:
#     #     boundary = choose_boundary()
#     logging.info("checkpoint 5")
#     body, _ = encode_multipart_formdata(fields, boundary)
#     content_type = str('multipart/related; boundary=%s' % boundary)

#     return body, content_type

def get_boolean_value(prompt):
    """
    Get a boolean value from the user.
    """
    while True:
        value = input(prompt).lower()
        if value in ("true", "1"):
            return True
        elif value in ("false", "0"):
            return False
        elif value == '':
             return None
        else:
            raise Exception("Please enter a valid boolean value.")

def get_input_value(prompt):
    """
    Get a input value from the user else return None.
    """
    while True:
        value = input(prompt).lower()
        if value == '':
            return None
        else:
            return value
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = read_system_config()

    KHEOPS_URL = config["kheops_url"]
    KEYCLOAK_URL = config["keycloak_url"]
    CLIENT_ID = config["client_id"]
    REALM_NAME = config["realm_name"]
    USERNAME = config["kheops_username"]
    PASSWORD = config["kheops_password"]
    
    try:
        # User Authentication
        access_token = authenticate(KEYCLOAK_URL,REALM_NAME,CLIENT_ID,USERNAME,PASSWORD,)
        
        import sys

        if len(sys.argv) > 1:

## individual function implementation to be used seperately (not through main workflow)

            if sys.argv[1] == "--show_album_list":
                # Print the list of albums created
                get_detailed_album_list(KHEOPS_URL, access_token)
            elif sys.argv[1] == "--generate_album_link":
                # Generate and display the shareable link
                get_album_list(KHEOPS_URL, access_token)
                album_id = input("Please enter the album id: ")
                generate_album_shareable_link(KHEOPS_URL, album_id, access_token)
            elif sys.argv[1] == "--delete_album":
                # Delete an album
                get_album_list(KHEOPS_URL, access_token)
                album_id = input("Please enter the album id: ")
                delete_album(KHEOPS_URL,album_id,access_token)
            elif sys.argv[1] == "--create_album":
                # Create an album
                name = input("Enter the album name : ")
                description = input("Enter the album description (optional): ")
                create_album(KHEOPS_URL,access_token,name,description)
            elif sys.argv[1] == "--show_album":
                # show details about an album
                get_album_list(KHEOPS_URL, access_token)
                album_id = input("Please enter the album id: ")
                get_album_details(KHEOPS_URL,album_id,access_token)
            elif sys.argv[1] == "--edit_album":
                # edit an album
                get_album_list(KHEOPS_URL, access_token)
                album_id = input("Please enter the album id: ")
                logging.info("Album details to be edited : ")
                get_album_details(KHEOPS_URL,album_id,access_token)
                name = get_input_value("Enter new name (leave empty to keep current name): ")
                description = get_input_value("Enter new description (leave empty to keep current description): ")
                add_user = get_boolean_value("Allow adding users (true/false): ")
                download_series = get_boolean_value("Allow downloading series (true/false): ")
                send_series = get_boolean_value("Allow sending series (true/false): ")
                delete_series = get_boolean_value("Allow deleting series (true/false): ")
                add_series = get_boolean_value("Allow adding series (true/false): ")
                write_comments = get_boolean_value("Allow writing comments (true/false): ")
                notification_new_series = get_boolean_value("Enable new series notifications (true/false): ")
                notification_new_comment = get_boolean_value("Enable new comment notifications (true/false): ")
                kwargs= {
                            "name": name,
                            "description": description,
                            "addUser": add_user,
                            "downloadSeries": download_series,
                            "sendSeries": send_series,
                            "deleteSeries": delete_series,
                            "addSeries": add_series,
                            "writeComments": write_comments,
                            "notificationNewSeries": notification_new_series,
                            "notificationNewComment": notification_new_comment
                }
                edit_album_settings(KHEOPS_URL, album_id, access_token, **kwargs)# name,description, add_user, download_series, send_series, delete_series, add_series, write_comments, notification_new_series, notification_new_comment)

            # [TO DO:]
            # add series, add study, delete series, delete study functionalities [yet to be implemnted]
            # elif sys.argv[1] == "--add_study":
            #      # add studies 
            #      pass
            # elif sys.argv[1] == "--add_series":
            #      # add series
            #      pass
            # elif sys.argv[1] == "--delete_study":
            #      # delete study
            #      pass
            # elif sys.argv[1] == "--delete_series":
            #      # delete series
            #      pass

            else:
                print("Invalid command-line argument.")
        else:

            # logging.info("TEST ACCESS TOKEN")
            # print(access_token)

## Main Workflow for [subset identification -> album creation -> study/series upload -> link generation]

            name = input("Enter the album name: ")
            description = input("Enter the album description (optional): ")
            
            # [TO DO:]
            # Metadata querying and subset creation function (yet to be implemented)
            #    pass
        
            # Create the album using user input
            album_data = create_album(KHEOPS_URL, name, description)
            album_id = album_data["album_id"]
            
            # [TO DO:]
            # Add studies/series to the album function  (yet to be implemented)
            #    add_studies_to_album(kheops_url, album_id, subset_folder, kheops_access_token)

            # Generate and display the shareable link
            generate_album_shareable_link(KHEOPS_URL, album_id, access_token)

    except Exception as e:
        logging.error(f"ERROR : {e}")
