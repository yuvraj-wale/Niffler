import os
import shutil
import pymongo
import pydicom
import csv
import json
import requests

def read_system_config():
    with open("system.json", "r") as file:
        return json.load(file)

def read_filter_criteria_csv(csv_file_path):
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def create_subset_folder(source_folder, subset_folder, mongo_uri, filter_criteria):
    client = pymongo.MongoClient(mongo_uri)
    db = client.dicom_metadata_db
    collection = db.metadata

    filtered_metadata = collection.find(filter_criteria)

    if not os.path.exists(subset_folder):
        os.makedirs(subset_folder)

    for metadata in filtered_metadata:
        study_instance_uid = metadata.get("StudyInstanceUID")

        for root, dirs, files in os.walk(source_folder):
            for filename in files:
                if filename.endswith('.dcm'):
                    dicom_file_path = os.path.join(root, filename)
                    if pydicom.read_file(dicom_file_path).StudyInstanceUID == study_instance_uid:
                        destination_folder = os.path.join(subset_folder, os.path.relpath(os.path.dirname(dicom_file_path), source_folder))

                        if not os.path.exists(destination_folder):
                            os.makedirs(destination_folder)

                        shutil.copy(dicom_file_path, destination_folder)
                        print(f"Copied: {dicom_file_path} to {destination_folder}")

def authenticate(kheops_url):
    url = f"{kheops_url}/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        access_token = json_data["access_token"]
        return access_token
    elif response.status_code == 400:
        json_data = response.json()
        error = json_data.get("error")
        error_description = json_data.get("error_description")
        raise Exception(f"Error: {error}, Description: {error_description}")
    else:
        raise Exception("Unexpected response from the server.")

if __name__ == "__main__":
    system_config = read_system_config()
    filter_criteria_list = read_filter_criteria_csv("filter_criteria.csv")

    source_folder = system_config["dicom_folder_location"]
    subset_folder = system_config["subset_folder_location"]
    mongo_uri = system_config["mongo_uri"]
    kheops_url = system_config["kheops_url"]

    for filter_criteria in filter_criteria_list:
        create_subset_folder(source_folder, subset_folder, mongo_uri, filter_criteria)