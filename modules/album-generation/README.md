# The Niffler Shareable Album Generator

## Getting Started

### Installation

To use these scripts, you need to have a KHEOPS instance set up on your system. Follow the installation guide [here](https://docs.kheops.online/docs/installation) for detailed instructions on setting up KHEOPS.

## Configuration

### System Configuration

Change the values of system.json file in the root directory of the module and fill it accordingly:

* *dicom_folder_location*: Set the correct path to the input DICOM folder.

* *subset_folder_location*: Set the correct path to the output subset folder.

* *mongo_uri*: Set the MongoDB URI for connecting to the database. In this case, the URI is "mongodb://127.0.0.1:27017".

* *db_name*: Specify the name of the DICOM metadata database. In this case, the name is "dicom_metadata_db".

* *collection_name*: Specify the name of the collection in the MongoDB database where the metadata will be stored. In this case, the collection name is "metadata".

* *kheops_url*: Set the URL of your Kheops instance. Replace "your-kheops-instance.com" with the actual URL.

* *kheops_access_token*: Set the access token for authenticating with the Kheops instance. Replace "your-kheops-access-token" with the actual access token.

### Filter Criteria Configuration

Update filter_criteria.csv file in the root directory of the project and fill it with the filter criteria that you want to use to identify the DICOM studies that you want to upload to a Kheops album.

The format examples:
```
[1]
PatientID
AAAAA
AAAAA
AAAAA

[2]
PatientID,AccessionNumber
AAAAA,BBBBBYYBBBBB
AAAAA,BBBBBYYBBBBB
AAAAA,BBBBBYYBBBBB

[3]
PatientID,AccessionNumber,StudyDate
AAAAA,BBBBBYYBBBBB,YYYYMMDD
AAAAA,BBBBBYYBBBBB,YYYYMMDD
AAAAA,BBBBBYYBBBBB,YYYYMMDD


[4]
PatientID,AccessionNumber,StudyMonth
AAAAA,BBBBBYYBBBBB,YYYYMM
AAAAA,BBBBBYYBBBBB,YYYYMM
AAAAA,BBBBBYYBBBBB,YYYYMM

``` 
