# Load JSON data
import csv
import json

# Path to your JSON file
file_path = 'Engage-Testing/data-struc.json'

# Open the file and load the data
with open(file_path) as file:
    data = json.load(file)
# Open a CSV file for writing
with open('Engage-Testing/geothermal_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(['Category', 'Field'])

    # Write the data
    for category, fields in data.items():
        for field in fields:
            writer.writerow([category, field])

print('CSV file has been created successfully.')
