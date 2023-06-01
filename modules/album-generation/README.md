# The Nifler Shreable Album Generator

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

