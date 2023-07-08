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

# def read_filter_criteria_csv(csv_file_path):
#     """
#     Read the filter criteria from the specified CSV file.
#     """
#     with open(csv_file_path, "r") as file:
#         reader = csv.DictReader(file)
#         return [row for row in reader]


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

def authenticate(keycloak_url, client_id, username, password):
    """
    Authenticate and generate an access token from the KHEOPS server.
    """
    token_url = f'{keycloak_url}/auth/realms/kheops/protocol/openid-connect/token'
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
        raise Exception(f'Error: {str(e)}')
    
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
    album_data=f"""
                                 Album ID: {album_id}
                                 Name: {name}
                                 Description: {description}
    """

    if response.status_code == 201:
        logging.info("Album created succesfully!")
        logging.info(album_data)
        return album.get("album_id")
    elif response.status_code == 404:
        raise Exception('User not found')
    else:
        raise Exception('Album creation failed')

def generate_album_shareable_link(kheops_url, album_id, kheops_access_token):
    """
    Generate a shareable link to an album by creating a capability token.
    """
    try:
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
            logging.info("Shareable linke generated!")
            logging.info("NOTE: the link expires in 3 days")
            logging.info("Shareable link: %s", shareable_link)
        elif response.status_code == 400:
            logging.info("Invalid parameters.")
        elif response.status_code == 401:
            logging.info("User is not authorized as an admin of the album.")
        elif response.status_code == 404:
            logging.info("Album not found.")
        else:
            logging.info("Failed to generate shareable link.")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

def get_album_list(kheops_url, kheops_access_token):
    """
    Get a list of available albums.
    """
    url = f"{kheops_url}/api/albums"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        albums = response.json()
        
        logging.info("List of Albums created : ")
        for album in albums:
            album_id = album.get("album_id")
            name = album.get("name")
            description = album.get("description")
            created_time = album.get("created_time")
            modalities = album.get("modalities")

            # Format the album data for display
            album_data = f"""
                                 Album ID: {album_id}
                                 Name: {name}
                                 Description: {description}
                                 Created Time: {created_time}
                                 Modalities: {modalities}
            """

            # Display the album data in a pleasing format
            logging.info(album_data)

    except requests.exceptions.RequestException as e:
        logging.error("Failed to retrieve album list: %s", str(e))

def delete_album(kheops_url, album_id, kheops_access_token):
    """
    Delete an album.
    """
    url = f"{kheops_url}/api/albums/{album_id}"
    headers = {
        'Authorization': f"Bearer {kheops_access_token}"
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    if response.status_code == 204:
        print("Album deleted successfully!")
    elif response.status_code == 403:
        raise Exception("User is not an admin")
    elif response.status_code == 404:
        raise Exception("User not found or album not found")
    else:
        raise Exception("Failed to delete album")
    
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
        album_details = {
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
        logging.info(album_details)
    elif response.status_code == 400:
        print("Bad Request. Incorrect query parameters.")
    elif response.status_code == 403:
        print("Forbidden. User can't see the users list.")
    elif response.status_code == 404:
        print("Not Found. User not found, album not found, or user is not a member of the album.")
    else:
        print("An error occurred while fetching album details.")

def edit_album_settings(kheops_url, album_id, kheops_access_token, **kwargs):
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

    response = requests.patch(url, headers=headers, data=payload)

    if response.status_code == 200:
        album_data = response.json()

        # Extract the necessary details from the album_data
        album_details = {
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
        logging.info("Album Updated Successfully!, here are the new album settings : ")
        logging.info(album_details)
    elif response.status_code == 403:
        logging.error("Forbidden. Only admins can edit albums.")
    elif response.status_code == 404:
        logging.error("Not Found. User not found, album not found, or user is not a member of the album.")
    else:
        logging.error("An error occurred while editing the album.")
   
def add_studies_to_album(kheops_url, album_id, subset_folder_location, kheops_access_token):
    """
    Add studies to an album.
    """
    try:
        study_instance_uid = get_study_instance_uid(subset_folder_location)
        logging.info(study_instance_uid)
        url = f"{kheops_url}/api/studies/{study_instance_uid}/albums/{album_id}"

        series_files = []
        for root, _, files in os.walk(subset_folder_location):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if is_dicom_file(file_path):
                    with open(file_path, 'rb') as file:
                        file_data = file.read()
                        series_files.append(('file', (file_name, file_data, 'application/dicom')))
                    # logging.info("checkpoint 3")
                    # series_files.append(('file', (file_name, open(file_path, 'rb'), 'application/dicom')))
        logging.info("checkpoint 4")

        body, content_type = encode_multipart_related(series_files)

        headers = {
            "Authorization": f"Bearer {kheops_access_token}",
            "Accept": "application/dicom+json",
            "Content-Type": content_type
        }
        
        response = requests.put(url, data=body, headers=headers)
        logging.info(response.status_code)
        response.raise_for_status()

        if response.status_code == 201:
            print("Study added to album successfully.")
        elif response.status_code == 403:
            print("User is not authorized to add series to the album.")
        elif response.status_code == 404:
            print("User not found, album not found, or study not present in the source.")
        else:
            print("Failed to add study to album.")    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def add_series(kheops_url, kheops_access_token, series_folder, study_instance_uid, series_instance_uid, album_id):
    """
    Add series to an album.
    """
    url = f"{kheops_url}/api/studies/{study_instance_uid}/series/{series_instance_uid}/albums/{album_id}"
    headers = {
        "Authorization": f"Bearer {kheops_access_token}",
        # "X-Authorization-Source": f"Bearer {token}"  # Optional: Use this header if sending the series from another album
    }

    series_files = []
    for root, _, files in os.walk(series_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if is_dicom_file(file_path):
                series_files.append(('file', (file_name, open(file_path, 'rb'))))

    response = requests.put(url, headers=headers, files=series_files)

    if response.status_code == 201:
        print("Series added successfully.")
    elif response.status_code == 403:
        print("Access forbidden. User is not an admin or does not have 'addSeries' permission.")
    elif response.status_code == 404:
        print("Not found. User not found, album ID does not exist, user is not a member of the album, or series is not present.")
    else:
        print("An error occurred while adding the series.")

def extract_study_instance_uid(dicom_file_path):
    """
    Extract the Study Instance UID from a DICOM file.
    """
    logging.info("checking 1")
    ds = pydicom.dcmread(dicom_file_path)
    study_instance_uid = ds.StudyInstanceUID
    return study_instance_uid

def get_study_instance_uid(study_folder_location):
    """
    Get the Study Instance UID from the study folder.
    """
    # Assuming the study folder contains DICOM files and the Study Instance UID is present in the DICOM metadata
    logging.info("checking 2")
    for root, _, files in os.walk(study_folder_location):
        for filename in files:
            dicom_file_path = os.path.join(root, filename)
            if is_dicom_file(dicom_file_path):
                study_instance_uid = extract_study_instance_uid(dicom_file_path)
                return study_instance_uid

    raise Exception("Study Instance UID not found in the study folder.")

def is_dicom_file(file_path):
    try:
        dicom_file = pydicom.dcmread(file_path)
        return True
    except pydicom.errors.InvalidDicomError:
        return False

def encode_multipart_related(fields, boundary=None):
    # if boundary is None:
    #     boundary = choose_boundary()
    logging.info("checkpoint 5")
    body, _ = encode_multipart_formdata(fields, boundary)
    content_type = str('multipart/related; boundary=%s' % boundary)

    return body, content_type

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    url="http://127.0.0.1"
    keycloak_url="http://127.0.0.1:8080"

    #authenticate
    logging.info("TEST AUTHENTICATE")
    name=input("Enter Username or Email ID : ")
    password=input("Enter Password : ")
    token=authenticate(keycloak_url,"loginConnect",name,password)
    logging.info(token)
    
    #create album
    logging.info("TEST CREATE ALBUM")
    album_id = create_album(url,token,"xyz","no description")
    
    #generate album link
    logging.info("TEST GENERATE ALBUM LINK")
    generate_album_shareable_link(url,album_id,token)
    
    #get list of albums
    logging.info("TESTS GET ALBUM LIST")
    get_album_list("http://127.0.0.1",token)
    
    #delete album
    logging.info("TEST DELETE ALBUM")
    delete_album_id=input("enter album id to delete : ")
    delete_album(url,delete_album_id,token)
    
    #get album metadata
    logging.info("TEST GET ALBUM DETAILS")
    get_album_details(url, album_id, token)

    #edit album details
    logging.info("TEST EDIT ALBUM DETAILS")
    name = input("Enter new name (leave empty to keep current name): ")
    description = input("Enter new description (leave empty to keep current description): ")
    add_user = input("Allow adding users (true/false): ")
    download_series = input("Allow downloading series (true/false): ")
    send_series = input("Allow sending series (true/false): ")
    delete_series = input("Allow deleting series (true/false): ")
    add_series = input("Allow adding series (true/false): ")
    write_comments = input("Allow writing comments (true/false): ")
    notification_new_series = input("Enable new series notifications (true/false): ")
    notification_new_comment = input("Enable new comment notifications (true/false): ")  
    edit_album_settings(url, album_id,token,name=name,description=description,add_user=add_user,download_series=download_series,send_series=send_series,delete_series=delete_series,add_series=add_series,write_comments=write_comments,notification_new_series=notification_new_series,notification_new_comment=notification_new_comment)
    # add_studies_to_album(url,"0fByVrfZfc","/home/yuraj/Downloads/DICOM",token )
    # album_id=input("enter album id : ")
    # delete_album(url,album_id,token)
    # create_album(url,token,'create album test','hmmm')
    # logging.info(token)
    # # system_config = read_system_config()
    # # filter_criteria_list = read_filter_criteria_csv("filter_criteria.csv")
    # # mongo_uri = system_config["mongo_uri"]
    # # kheops_url = system_config["kheops_url"]
    # # kheops_access_token = system_config["kheops_access_token"]
    # # source_folder = system_config["dicom_folder_location"]
    # # subset_folder = system_config["subset_folder_location"]
    # kheops_access_token= "SuB9swhVTYQyCMYP27TDOe"
    # kheops_url= "http://127.0.0.1"
    # subset_folder= "/home/yuraj/Downloads/DICOM"
    # # Check if additional command-line arguments are provided
    # import sys

    # if len(sys.argv) > 1:
    #     if sys.argv[1] == "show_album_list":
    #         # Print the list of album details
    #         get_album_list(kheops_url, kheops_access_token)
    #     elif sys.argv[1] == "generate_album_link":
    #         # Generate and display the shareable link
    #         album_id = input("Please enter the album id: ")
    #         generate_album_shareable_link(kheops_url, album_id, "Shareable Link" , kheops_access_token)
    #     else:
    #         print("Invalid command-line argument.")
    # else:
    #     name = input("Enter the album name: ")
    #     description = input("Enter the album description (optional): ")

    #     # Create the album using user input
    #     album_data = create_album(kheops_url, name, description)
    #     album_id = album_data["album_id"]

    #     # Add studies to the album
    #     add_studies_to_album(kheops_url, album_id, subset_folder, kheops_access_token)

    #     # Generate and display the shareable link
    #     generate_album_shareable_link(kheops_url, album_id, "Shareable Link", kheops_access_token)

