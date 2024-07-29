#importing the libraries
import pandas as pd
from google.cloud import storage #importing google cloud client library
from joblib import load #load the pretrained model from file path
import xgboost as xgb 
import os #fetching and interacting with operating system
from io import StringIO #reading csv data from files
import json #encoding and decoding json files
from scipy.fft import fft, ifft #signal processing
import numpy as np
from dotenv import load_dotenv #loading environment variables from .env file
load_dotenv("../secret_keys/.env")

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


def preprocessing(data):
    #dropping the last empty columns
    if len(data.columns) > 26:
        data = data.drop(columns=data.columns[26:])
        
    #adding the column names
    column_names = ["Unit_ID", "Time_in_Cycles", "Setting_1", "Setting_2", "Setting_3", "T2", "T24", "T30", "T50", "P2", "P15", "P30", "Nf", "Nc", "epr", "Ps30", "phi", "NRf", "NRc", "BPR", "farB", "htBleed", "Nf_dmd", "PCRfR_dmd", "W31", "W32"]
    data.columns = column_names

    #dropping the non-variability columns(constant values)
    data = data.drop(columns = ["Setting_3", "T2", "P2", "epr", "farB", "Nf_dmd", "P15", "PCRfR_dmd"])
    
    return data

#reconstructing the signal using principal frequencies from fourier transform
def principal_signal_reconstruction(testing_dataset):

    def signal_reconstruction(dataset):
        #converting the dataset to numpy array
        dataset = np.array(dataset) 

        #calulating fourier transform values                   
        fourier = fft(dataset) #transforming time-domain signal to spectrum of frequencies

        #calculating the magnitude of frequency spectrum                  
        magnitude_spectrum = np.abs(fourier) #(provides the contribution of each frequency to the overall signal)

        #defining the percentage of frequencies to retain
        principal_percentage = 30

        #calculating the number of frequencies to retain based on the principal_percentage
        top_frequency_count = int(len(dataset) * principal_percentage / 100)

        #sorting the magnitude spectrum to find indices of the principal(dominant) frequencies (ordered largest to smallest)
        principal_indices = magnitude_spectrum.argsort()[-top_frequency_count:][::-1] #(capturing the dominant characteristics of the original signal) (- top_frequency_count = indice of largest principal value)

        #converting the fourier values to a dataframe
        fourier_df = pd.DataFrame({"fourier_transformed_values": fourier})

        #initialising a new column with zeros
        fourier_df["significant_fourier_values"] = 0

        #assigning the principal frequency indices values to significant_fourier_values column 
        fourier_df.loc[principal_indices, "significant_fourier_values"] = fourier_df.loc[principal_indices, "fourier_transformed_values"]

        #reconstructing the signal using inverse fourier transform
        reconstructed_signal = ifft(fourier_df["significant_fourier_values"].values).real #(taking only real part of complex number(discarding imaginary part)
        
        return reconstructed_signal

    #list of non sensor values to be excluded from the signal reconstruction process
    non_sensor_values = ["Unit_ID", "Time_in_Cycles", "Setting_1", "Setting_2", "RUL"]

    #reconstructing the sensor reading in the testing dataset
    reconstructed_testing_dataset = testing_dataset.copy()
    for column in reconstructed_testing_dataset.columns:
        if column not in non_sensor_values:
            reconstructed_testing_dataset["principal_recon_" + column] = signal_reconstruction(testing_dataset[column])

    return reconstructed_testing_dataset

def main():

    #fetching the backet name and file path
    bucket_name = os.getenv("BUCKET_NAME")
    file_path = os.getenv("file_path")

    xgb_model_path = "routes/xgb_model.pkl" #defining the path of trained xGBoost model

    try:
        data = fetch_data(bucket_name, file_path) #fetching data
        data = preprocessing(data) #preprocessing data
        data = principal_signal_reconstruction(data) #reconstructing signals

        #separating the "Unit_ID" for output and dropping the column since it is not needed for prediction
        engine_numbers = data["Unit_ID"].values
        prediction_data = data.drop(columns=["Unit_ID"])

        #loading the trained XGBoost model using the model path
        xgb_model = load(xgb_model_path)

        #converting data to DMatrix format for prediction
        prediction_dmatrix = xgb.DMatrix(prediction_data)

        #predicting the RUL
        predictions = xgb_model.predict(prediction_dmatrix)
        #print(type(predictions))
        
        #converting the predictions to a list
        predictions = predictions.tolist()

        #formatting the results, as we only needed respective "Unit_ID" and their "RUL"
        results = []
        for engine_number, rul in zip(engine_numbers, predictions):
            result = {
                "Unit_ID": int(engine_number),
                "RUL": int(round(rul))
            }
            results.append(result)

        print(json.dumps(results)) #printing the results in json format

    #handling the exceptions occured during the process
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__": #executing the main function
    main()

#references: 
#(Google Storage Documentation, 2023b)
#(Python, 2019)
#(Python, 2023a)
#(Joblib, 2023)
#(Kumar, 2023)
#(Scipy, 2023)
#(Real Python, 2020)
#(Python, 2023b)