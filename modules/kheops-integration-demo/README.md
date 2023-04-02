# Kheops Integration Demo

This repository contains code for a demo of integrating the Kheops shareable albums feature into your application. The code is divided into two scripts:

- `subset_identification.py`: This script searches for DICOM studies that match a set of filter criteria, and creates a subset of those studies in a separate folder. This is useful if you have a large dataset and want to upload only a subset of the data to Kheops.
- `album_management.py`: This script uploads a folder of DICOM studies to a Kheops shareable album, and generates a shareable link that can be used to access the album.

## Getting Started

### Prerequisites

Before you can use these scripts, you need to have the following:

- Set up KHEOPS instance on your system
  - Install Docker (latest version)
  - Install Docker-Compose (latest version)
  - Make sure that the current user is in the docker group.
  - Run the following command:
    ```
    bash <(curl -sL https://raw.githubusercontent.com/OsiriX-Foundation/KheopsOrchestration/insecure-install-v1.1/kheopsinstall.sh)
    ```
  - checkout KHEOPS installation [guide](https://docs.kheops.online/docs/installation) for more details.
- Python 3.6 or later installed on your system.

### Installation

To install the required Python packages, run the following command in the terminal:

```bash
pip install -r requirements.txt
```

## Configuration

Before you can run the scripts, you need to configure your Kheops instance and system settings.

### Kheops Configuration

To authenticate your API calls to your Kheops instance, you need to obtain an access token from your Kheops instance. Follow these steps to generate an access token:

- Log in to your Kheops instance using your Kheops credentials.
- Click on your user profile in the top right corner of the screen and select "Settings" from the dropdown menu.
- Click on the "API Tokens" tab.
- Click on the "New Token" button to generate a new API token.
- Enter a name for the token and select the appropriate permissions.
- Click the "Create" button to create the token.
- Copy the access token value to your clipboard.

### System Configuration

Change the values of system.json file in the root directory of the module and fill it accordingly:

```
{
    "dicom_folder_location": "/path/to/input_dicom_folder",
    "subset_folder_location": "/path/to/output_subset_folder",
    "mongo_uri": "mongodb://127.0.0.1:27017",
    "db_name": "dicom_metadata_db",
    "collection_name": "metadata",
    "kheops_url": "https://your-kheops-instance.com",
    "kheops_access_token": "your-kheops-access-token"
}
```

### Filter Criteria Configuration

Update filter_criteria.csv file in the root directory of the project and fill it with the filter criteria that you want to use to identify the DICOM studies that you want to upload to a Kheops album.
```
attribute_1,attribute_2
attribute_value_1,attribute_value_2
```

## Usage

To use the scripts, run the following command in the terminal in the root directory of the module:
```
python subset_identification.py
```
This will search for DICOM studies that match the filter criteria in filter_criteria.csv and create a subset of those studies in the directory specified by subset_folder_location. Optionally you can skip the subset identification process and directly provide the pre-identified subset location in the subset_folder_location

To upload the subset of DICOM studies to a Kheops album and generate a shareable link, run the following command in the terminal:
```
python album_management.py create
```
This will upload the DICOM studies in the directory specified by subset_folder_location to a new album in your Kheops instance, and generate a shareable link that can be used to access the album.

You can also use additional album handeling functions by replacing 'create' and adding desired function:
```
python album_management.py <insert_desired_function>
```
here is the list of additional functions :

- list: List all albums
- delete: Delete an album
- add: Add a study to an album
- link: Generate a shareable link for an album
- search: Search for albums
- delete-study: Delete a study from an album
- update: Update album metadata 

Depending on the command you enter, you will be prompted to enter additional information such as album names, IDs, or study IDs.

## NOTE:
As of now the KHEOPS API is not supporting the link generation and search album feature and is giving an empty response. for more details check KHEOPS albums [DOCS](https://github.com/OsiriX-Foundation/kheops/wiki)
