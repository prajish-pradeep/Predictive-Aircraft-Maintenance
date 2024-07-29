import pandas as pd
from io import StringIO #reading csv data from files
from google.cloud import storage #importing google cloud client library
import os #fetching and interacting with operating system
from dotenv import load_dotenv #loading environment variables from .env file
load_dotenv("../secret_keys/.env")

#fetching the data from GCP bucket
def fetch_data(bucket_name, file_path):

    #extracting the file path
    parts = file_path.split("/")
    file_path = "/".join(parts[1:])

    #authenticating the client using the service account JSON
    service_account_path = os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH")
    storage_client = storage.Client.from_service_account_json(service_account_path)

    #reference to the specified bucket
    bucket = storage_client.bucket(bucket_name)

    #reference to the specified file
    blob = bucket.blob(file_path)

    #downloading the content of file as text
    text_file = blob.download_as_text()

    #converting the text content to a dataframe
    data = pd.read_csv(StringIO(text_file), delimiter=" ", header = None)
    return data

def preprocessing(data): #preprocessing the data

    #dropping the last empty columns
    if len(data.columns) > 26:
        data = data.drop(columns=data.columns[26:])

    #adding the column names
    column_names = ["Unit_ID", "Time_in_Cycles", "Setting_1", "Setting_2", "Setting_3", "T2", "T24", "T30", "T50", "P2", "P15", "P30", "Nf", "Nc", "epr", "Ps30", "phi", "NRf", "NRc", "BPR", "farB", "htBleed", "Nf_dmd", "PCRfR_dmd", "W31", "W32"]
    data.columns = column_names
    return data

critical_sensors = {
    "Setting_3": 100.0,
    "T2": 518.67,
    "P2": 14.62,
    "epr": 1.3,
    "farB": 0.03,
    "Nf_dmd": 2388,
    "PCRfR_dmd": 100.0,
    "P15": (21.60, 21.61)
}

#creating the monitoring and alert system
def monitoring_and_alert_system(dataset):
    alerts = []
    required_features = dataset[["Unit_ID"] + list(critical_sensors.keys())] #extract only the columns of critical sensors
    for index, row in required_features.iterrows(): #iterate through each row of required features
        engine = int(row["Unit_ID"]) #extracting the engine number
        
        for key, expected_value in critical_sensors.items(): #iterating through key-value pair(sensor, expected_value) in dictionary(critical_sensor)
            actual_value = row[key] #value from current row
    
            if key == "P15": #checking P15 sensor data
                if not expected_value[0] <= actual_value <= expected_value[1]: #if sensor value is outside the range
                    alerts.append(f"ALERT!!! Deviation detected in Engine {engine} for sensor {key}. The sensor returned {actual_value}. The value should lie between {expected_value[0]} and {expected_value[1]}.")
                
            elif actual_value != expected_value: #if sensor value is different from expected(all sensors)
                alerts.append(f"ALERT!!!! Deviation detected in Engine {engine} for sensor {key}. The sensor returned {actual_value}. The expected value should be {expected_value}.")
    
    return alerts

if __name__ == "__main__":

    #fetching the bucket name and file path
    bucket_name = os.getenv("BUCKET_NAME")
    file_path = os.getenv("file_path")
    data = fetch_data(bucket_name, file_path) #fetching data from gcp bucket
    data = preprocessing(data) #preprocessing data
    alerts = monitoring_and_alert_system(data) #checking the deviation
    if not alerts:  #no deviation
        print("No deviation detected in the critical sensors")
    else: #print the alert
        for alert in alerts:
            print(alert + "<br>")

#reference: 
#(Google Storage Documentation, 2023b)
#(Python, 2019)
#(Python, 2023a)