import os
import shutil
import pymongo
import json
import csv
import requests
import sys

def read_system_config():
    with open("system.json", "r") as file:
        return json.load(file)

def read_filter_criteria_csv(csv_file_path):
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def get_albums(kheops_url, kheops_access_token):
    url = f"{kheops_url}/albums"
    headers = {"Authorization": f"Bearer {kheops_access_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        albums = response.json()
        for album in albums:
            print(f"Album Name: {album['name']}, Album ID: {album['id']}")
    else:
        print(f"Error getting albums: {response.text}")

def delete_album(kheops_url, kheops_access_token, album_id):
    url = f"{kheops_url}/albums/{album_id}"
    headers = {"Authorization": f"Bearer {kheops_access_token}"}

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"Album {album_id} deleted successfully")
    else:
        print(f"Error deleting album: {response.text}")

def add_study_to_album(kheops_url, kheops_access_token, album_id, study_path):
    url = f"{kheops_url}/albums/{album_id}/items"
    headers = {"Authorization": f"Bearer {kheops_access_token}"}

    with open(study_path, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)

        if response.status_code == 201:
            print(f"Study {study_path} added to album {album_id}")
        else:
            print(f"Error adding study: {response.text}")

def generate_album_link(kheops_url, kheops_access_token, album_id):
    url = f"{kheops_url}/album/{album_id}/link"
    headers = {"Authorization": f"Bearer {kheops_access_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        album_link = response.json()["url"]
        print(f"Album link: {album_link}")
    else:
        print(f"Error generating album link: {response.text}")

def search_albums(kheops_url, kheops_access_token, search_criteria):
    url = f"{kheops_url}/albums?query={search_criteria}"
    headers = {"Authorization": f"Bearer {kheops_access_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        albums = response.json()
        for album in albums:
            print(f"Album Name: {album['name']}, Album ID: {album['id']}")
    else:
        print(f"Error searching albums: {response.text}")

def delete_study_from_album(kheops_url, kheops_access_token, album_id, study_instance_uid):
    url = f"{kheops_url}/albums/{album_id}/items/{study_instance_uid}"
    headers = {"Authorization": f"Bearer {kheops_access_token}"}

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"Study {study_instance_uid} deleted from album {album_id}")
    else:
        print(f"Error deleting study: {response.text}")

def update_album_metadata(kheops_url, kheops_access_token, album_id, album_name, album_description):
    url = f"{kheops_url}/albums/{album_id}"
    headers = {"Authorization": f"Bearer {kheops_access_token}", "Accept": "application/json"}
    payload = {"name": album_name, "description": album_description}

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 204:
       print(f"Album {album_id} metadata updated successfully")
    else:
       print(f"Error updating album metadata: {response.text}")

def create_album(subset_folder_location, album_name, kheops_url, kheops_access_token):
    url = f"{kheops_url}/albums"
    headers = {"Authorization": f"Bearer {kheops_access_token}", "Accept": "application/json"}

    payload = {"name": album_name}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        album_id = response.json()["id"]
        print(f"Album created with ID: {album_id}")

        for root, dirs, files in os.walk(subset_folder_location):
            for filename in files:
                dicom_file_path = os.path.join(root, filename)
                with open(dicom_file_path, 'rb') as f:
                    response = requests.post(f"{url}/{album_id}/items", headers=headers, data=f)
                    if response.status_code != 201:
                        print(f"Error uploading {dicom_file_path}: {response.text}")
                        continue

        share_url = f"{kheops_url}/album/{album_id}/link"
        print(f"Shareable URL: {share_url}")
    else:
        print(f"Error creating album: {response.text}")

if __name__ == "__main__":
    system_config = read_system_config()
    filter_criteria_list = read_filter_criteria_csv("filter_criteria.csv")
    
    if len(sys.argv) < 2:
       subset_folder_location = system_config["subset_folder_location"]
       album_name = input("Enter album name: ")
       album_description = input("Enter album description: ")
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]

       create_album(subset_folder_location, album_name, kheops_url, kheops_access_token)

    elif sys.argv[1] == "list":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       get_albums(kheops_url, kheops_access_token)

    elif sys.argv[1] == "delete":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       album_id = input("Enter album ID to delete: ")
       delete_album(kheops_url, kheops_access_token, album_id)

    elif sys.argv[1] == "add":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       album_id = input("Enter album ID to add study to: ")
       study_path = input("Enter path of study to add: ")
       add_study_to_album(kheops_url, kheops_access_token, album_id, study_path)

    elif sys.argv[1] == "link":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       album_id = input("Enter album ID to generate link for: ")
       generate_album_link(kheops_url, kheops_access_token, album_id)

    elif sys.argv[1] == "search":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       search_criteria = input("Enter search criteria: ")
       search_albums(kheops_url, kheops_access_token, search_criteria)

    elif sys.argv[1] == "delete-study":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       album_id = input("Enter album ID to delete study from: ")
       study_instance_uid = input("Enter study instance UID to delete: ")
       delete_study_from_album(kheops_url, kheops_access_token, album_id, study_instance_uid)

    elif sys.argv[1] == "update":
       kheops_url = system_config["kheops_url"]
       kheops_access_token = system_config["kheops_access_token"]
       album_id = input("Enter album ID to update metadata: ")
       album_name = input("Enter new album name: ")
       album_description = input("Enter new album description: ")
       update_album_metadata(kheops_url, kheops_access_token, album_id, album_name, album_description)

    else:
       print("Invalid command. Please enter one of the following commands:")
       print("  list     : List all albums")
       print("  delete   : Delete an album")
       print("  add      : Add a study to an album")
       print("  link     : Generate a shareable link for an album")
       print("  search   : Search for albums")
       print("  delete-study : Delete a study from an album")
       print("  update   : Update album metadata")
