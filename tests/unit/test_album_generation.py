import os
import sys
import pytest
import requests

from unittest.mock import patch
from pathlib import Path
from pytest_mock import MockerFixture

niffler_modules_path = Path.cwd() / 'modules'
sys.path.append(str(niffler_modules_path / 'album-generation'))
import AlbumGenerator;

from AlbumGenerator import create_subset_folder
from AlbumGenerator import authenticate

@pytest.fixture
def mock_mongo_client():
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = mock_client.return_value.dicom_metadata_db
        mock_collection = mock_db.metadata
        yield mock_collection

def test_create_subset_folder(mock_mongo_client, tmpdir):
    source_folder = "/path/to/source"
    subset_folder = str(tmpdir.mkdir("subset"))
    mongo_uri = "mongodb://localhost:27017"
    filter_criteria = {"PatientName": "John Doe"}

    metadata1 = {"StudyInstanceUID": "study1"}
    metadata2 = {"StudyInstanceUID": "study2"}
    mock_mongo_client.find.return_value = [metadata1, metadata2]

    # Create some dummy DICOM files in the source folder
    dicom_files = [
        os.path.join(source_folder, "study1", "image1.dcm"),
        os.path.join(source_folder, "study1", "image2.dcm"),
        os.path.join(source_folder, "study2", "image3.dcm"),
        os.path.join(source_folder, "study3", "image4.dcm"),
    ]
    for dicom_file in dicom_files:
        os.makedirs(os.path.dirname(dicom_file), exist_ok=True)
        with open(dicom_file, "w") as f:
            f.write("dummy DICOM content")

    create_subset_folder(source_folder, subset_folder, mongo_uri, filter_criteria)

    # Assert the expected behavior
    assert mock_mongo_client.find.called_once_with(filter_criteria)

    assert os.path.exists(subset_folder)

    assert os.path.exists(os.path.join(subset_folder, "study1"))
    assert os.path.exists(os.path.join(subset_folder, "study2"))
    assert not os.path.exists(os.path.join(subset_folder, "study3"))

    assert os.path.exists(os.path.join(subset_folder, "study1", "image1.dcm"))
    assert os.path.exists(os.path.join(subset_folder, "study1", "image2.dcm"))
    assert os.path.exists(os.path.join(subset_folder, "study2", "image3.dcm"))
    assert not os.path.exists(os.path.join(subset_folder, "study3", "image4.dcm"))

@pytest.fixture
def mock_post_request():
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsImtpZCI6IjEifQ.eyJzdWIiOiIxMDQzOTE0ODIzNDkxNzE4Mzc1NzYifQ.zkqemWjCKVUqoRpPtoxUrocAw8uo63Q49-bXlG7G6m8",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        yield mock_post

def test_authenticate(mock_post_request):
    kheops_url = "https://your-kheops-instance.com"
    token = AlbumGenerator.authenticate(kheops_url)
    assert token == "eyJhbGciOiJIUzI1NiIsImtpZCI6IjEifQ.eyJzdWIiOiIxMDQzOTE0ODIzNDkxNzE4Mzc1NzYifQ.zkqemWjCKVUqoRpPtoxUrocAw8uo63Q49-bXlG7G6m8"
    mock_post_request.assert_called_once_with("https://your-kheops-instance.com/token", headers={"Content-Type": "application/x-www-form-urlencoded"})
