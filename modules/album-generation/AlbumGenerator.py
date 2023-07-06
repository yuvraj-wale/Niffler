import csv
import json
import os
import shutil
import requests
import pydicom
import pymongo
import logging

def read_system_config():
    """
    Read the system configuration from the "system.json" file.
    """
    with open("system.json", "r") as file:
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

# def authenticate(kheops_url):
#     """
#     Authenticate and generate an access token from the KHEOPS server.
#     """
#     url = f"{kheops_url}/api/token"

#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded"
#     }

#     response = requests.post(url, headers=headers)

#     if response.status_code == 200:
#         json_data = response.json()
#         access_token = json_data["access_token"]
#         return access_token
#     elif response.status_code == 400:
#         json_data = response.json()
#         error = json_data.get("error")
#         error_description = json_data.get("error_description")
#         raise Exception(f"Error: {error}, Description: {error_description}")
#     else:
#         raise Exception("Unexpected response from the server.")

def create_album(kheops_url, name, description=''):
    """
    Create a new album on the KHEOPS server.
    """
    url = f"{kheops_url}/api/albums"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'name': name[:255],
        'description': description[:2048],
    }
    response = requests.post(url, headers=headers, data=payload)
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
        return album
    elif response.status_code == 404:
        raise Exception('User not found')
    else:
        raise Exception('Album creation failed')

def generate_album_shareable_link(kheops_url, album_id, title, kheops_access_token):
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
            "title": title,
            "scope_type": "album",
            "album": album_id,
            "read_permission": "true",
            "download_permission": "true"
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 201:
            json_data = response.json()
            capability_token = json_data["secret"]
            shareable_link = f"{kheops_url}/view/{capability_token}"
            logging.info("Shareable linke generated!")
            logging.info("NOTE: the link expires in 3 days")
            logging.info("Shareable link:", shareable_link)
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
        "Authorization": kheops_access_token,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        albums = response.json()

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

def extract_study_instance_uid(dicom_file_path):
    """
    Extract the Study Instance UID from a DICOM file.
    """
    ds = pydicom.dcmread(dicom_file_path)
    study_instance_uid = ds.StudyInstanceUID
    return study_instance_uid

def get_study_instance_uid(study_folder_location):
    """
    Get the Study Instance UID from the study folder.
    """
    # Assuming the study folder contains DICOM files and the Study Instance UID is present in the DICOM metadata

    for root, dirs, files in os.walk(study_folder_location):
        for filename in files:
            if filename.endswith('.dcm'):
                dicom_file_path = os.path.join(root, filename)
                # Extract the Study Instance UID from the DICOM file
                study_instance_uid = extract_study_instance_uid(dicom_file_path)
                return study_instance_uid

    raise Exception("Study Instance UID not found in the study folder.")
   
def add_studies_to_album(kheops_url, album_id, subset_folder_location, kheops_access_token):
    """
    Add studies to an album.
    """
    try:
        study_instance_uid = get_study_instance_uid(subset_folder_location)
        url = f"{kheops_url}/api/studies/{study_instance_uid}/albums/{album_id}"

        headers = {
            "Authorization": f"Bearer {kheops_access_token}",
            "X-Authorization-Source": "Bearer album_capability_token"
        }

        response = requests.put(url, headers=headers)

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

def add_series():
    """
    Add series to an album.
    """
    pass


def delete_album():
    """
    Delete an album.
    """
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    system_config = read_system_config()
    # filter_criteria_list = read_filter_criteria_csv("filter_criteria.csv")
    # mongo_uri = system_config["mongo_uri"]
    kheops_url = system_config["kheops_url"]
    kheops_access_token = system_config["kheops_access_token"]
    source_folder = system_config["dicom_folder_location"]
    subset_folder = system_config["subset_folder_location"]

    # Check if additional command-line arguments are provided
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "show_album_list":
            # Print the list of album details
            get_album_list(kheops_url, kheops_access_token)
        elif sys.argv[1] == "generate_album_link":
            # Generate and display the shareable link
            album_id = input("Enter Album Id")
            generate_album_shareable_link(kheops_url, album_id, "Shareable Link" , kheops_access_token)
        else:
            print("Invalid command-line argument.")
    else:
        name = input("Enter the album name: ")
        description = input("Enter the album description (optional): ")

        # Create the album using user input
        album_data = create_album(kheops_url, name, description)
        album_id = album_data["album_id"]

        # Add studies to the album
        add_studies_to_album(kheops_url, album_id, subset_folder, kheops_access_token)

        # Generate and display the shareable link
        generate_album_shareable_link(kheops_url, album_id, "Shareable Link", kheops_access_token)

