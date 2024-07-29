#importing the libraries
import pandas as pd
import os #fetching and interacting with operating system
import copy
import numpy as np
from google.cloud import storage #importing google cloud client library
from io import StringIO #reading csv data from files
from scipy.fft import fft, ifft #signal processing
import xgboost as xgb
from dotenv import load_dotenv #loading environment variables from .env file
load_dotenv("../secret_keys/.env")
from joblib import dump #saving machine learning model to disk

def fetch_data(bucket_name, file_name):

    #authenticating the client using the service account JSON
    service_account_path = "../" + os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH_TRAIN")
    storage_client = storage.Client.from_service_account_json(service_account_path)

    #reference to the specified bucket
    bucket = storage_client.bucket(bucket_name)

    #reference to the specified file
    blob = bucket.blob(file_name)

    #downloading the content of file as text
    text_file = blob.download_as_text()

    #converting the text content to a dataframe
    data = pd.read_csv(StringIO(text_file), delimiter=" ", header = None)

    return data

def preprocessing(data):
    #dropping the last two empty columns
    data = data.drop(columns = [26,27])

    #adding the column names
    column_names = ["Unit_ID", "Time_in_Cycles", "Setting_1", "Setting_2", "Setting_3", "T2", "T24", "T30", "T50", "P2", "P15", "P30", "Nf", "Nc", "epr", "Ps30", "phi", "NRf", "NRc", "BPR", "farB", "htBleed", "Nf_dmd", "PCRfR_dmd", "W31", "W32"]
    data.columns = column_names

    #dropping the non-variability columns(constant values)
    data = data.drop(columns = ["Setting_3", "T2", "P2", "epr", "farB", "Nf_dmd", "P15", "PCRfR_dmd"])
    return data

#computing remaining useful life of training dataset
def remaining_useful_life_train(data):
    new_data = copy.copy(data) #creating a copy to make sure original data is not altered
    new_data["RUL"] = new_data.groupby("Unit_ID")["Time_in_Cycles"].transform(max) - new_data["Time_in_Cycles"] #find the maximum value of "Time_in_Cycles" for each group"Unit_ID' and subtract it with current "Time_in_Cycles"
    return new_data

#reconstructing the signal using principal frequencies from fourier transform
def principal_signal_reconstruction(training_dataset):

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

    #reconstructing the sensor reading in the training dataset
    reconstructed_training_dataset = training_dataset.copy()
    for column in reconstructed_training_dataset.columns:
        if column not in non_sensor_values:
            reconstructed_training_dataset["principal_recon_" + column] = signal_reconstruction(training_dataset[column])

    return reconstructed_training_dataset

def train_model(data):

    #removing the "Unit_ID" column
    data = data.drop(columns=["Unit_ID"])

    #splitting the data into independent variables and target
    X = data.drop(columns=["RUL"])  
    y = data["RUL"]

    #converting the dataset into Dmatrix optimized data structure 
    train_dmatrix = xgb.DMatrix(data=X, label=y)

    #setting the parameters (tuned, please refer the Hyperparameter tuning for xGBoost model in Machine_Learning.ipynb)
    params = {
        "booster": "gbtree",
        "objective": "reg:squarederror",
        "alpha": 0.05,
        "gamma": 0.5,
        "lambda": 1,
        "learning_rate": 0.05,
        "max_depth": 3,
        "min_child_weight": 5,
        "subsample": 1, 
        "colsample_bytree": 0.7
    }

    #training the XGBoost model
    xgb_model = xgb.train(params=params, dtrain=train_dmatrix, num_boost_round=100)
    print("XGBoost model training complete.")
    return xgb_model

def main():
    #retrieving the bucket name and file name from .env
    bucket_name = os.getenv("BUCKET_NAME_TRAIN")
    file_name = os.getenv("TRAIN_FILE_NAME")

    data = fetch_data(bucket_name, file_name)  #fetching the data
    data = preprocessing(data) #preprocessing data
    data = remaining_useful_life_train(data) #calculating RUL
    data = principal_signal_reconstruction(data) #reconstructing signals
    xgb_model = train_model(data) #training the data
    
    dump(xgb_model, "xgb_model.pkl") #saving the trained model to pickle file
    print("XGBoost model saved to .pkl file.")


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