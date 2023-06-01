import csv
import json


def read_system_config():
    with open("system.json", "r") as file:
        return json.load(file)

def read_filter_criteria_csv(csv_file_path):
    with open(csv_file_path, "r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]