import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import serial
import time
import warnings
import requests  # For ThingSpeak HTTP requests

warnings.filterwarnings("ignore")

# Initialize serial connection
ser = serial.Serial('COM3', baudrate=9600)  # Adjust COM port and baudrate as needed
print("Serial connection opened successfully!")

# Load data from an Excel sheet and split into features and labels
data = pd.read_excel("data.xlsx", engine="openpyxl")

feature_1 = data['bpm']
feature_2 = data['temparature']
feature_3 = data['respiration']

label_1 = data['label_bpm']
label_2 = data['label_temparature']
label_3 = data['label_respiration']

# Split the data into training and testing sets for each parameter
X_train_1, X_test_1, y_train_1, y_test_1 = train_test_split(feature_1, label_1, test_size=0.2, random_state=42)
X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(feature_2, label_2, test_size=0.2, random_state=42)
X_train_3, X_test_3, y_train_3, y_test_3 = train_test_split(feature_3, label_3, test_size=0.2, random_state=42)

# Build Random Forest models for each parameter
rf_model_1 = RandomForestClassifier(random_state=42)
rf_model_1.fit(X_train_1.values.reshape(-1, 1), y_train_1)

rf_model_2 = RandomForestClassifier(random_state=42)
rf_model_2.fit(X_train_2.values.reshape(-1, 1), y_train_2)

rf_model_3 = RandomForestClassifier(random_state=42)
rf_model_3.fit(X_train_3.values.reshape(-1, 1), y_train_3)

# ThingSpeak API setup
THINGSPEAK_API_KEY = "SLLSVRWEWHPBE1CI"  # Replace with your Write API Key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

def readData():
    """Reads and extracts sensor data from the serial input."""
    time.sleep(1)
    serial_data = ser.readline().decode().strip()
    
    while not serial_data.startswith('a'):
        serial_data = ser.readline().decode().strip()
    
    time.sleep(1)
    print("\n----------------------------")
    print("     -= Data Received =- ")
    print("----------------------------\n")
    print("Data:", serial_data, "\n")
    
    a = serial_data.find("a") + 1
    b = serial_data.find("b")
    val_1 = int(serial_data[a:b])
    print("bpm   :", val_1)
    
    b += 1
    c = serial_data.find("c")
    val_2 = int(serial_data[b:c])
    print("temperature :", val_2)
    
    c += 1
    d = serial_data.find("d")
    val_3 = int(serial_data[c:d])
    print("respiration :", val_3)
    
    return val_1, val_2, val_3

def upload_to_thingspeak(bpm, temperature, respiration):
    """Uploads real sensor data to ThingSpeak."""
    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": bpm,
        "field2": temperature,
        "field3": respiration
    }
    try:
        response = requests.get(THINGSPEAK_URL, params=payload)
        if response.status_code == 200:
            print("Data uploaded to ThingSpeak successfully!")
        else:
            print(f"Failed to upload data. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error uploading to ThingSpeak: {e}")

while True:
    serial_data = ser.readline().decode().strip()
    input_data = readData()
    if input_data is None:
        continue
    
    feature_1_val, feature_2_val, feature_3_val = input_data
    
    # Make predictions using the trained Random Forest models
    rf_prediction_1 = rf_model_1.predict([[feature_1_val]])[0]
    rf_prediction_2 = rf_model_2.predict([[feature_2_val]])[0]
    rf_prediction_3 = rf_model_3.predict([[feature_3_val]])[0]
    
    print("\n----------------------------")
    print("RF-prediction")
    print("----------------------------\n")
    
    time.sleep(1)
    print(f'bpm Prediction          : {rf_prediction_1}')
    print(f'temperature Prediction  : {rf_prediction_2}')
    print(f'respiration Prediction  : {rf_prediction_3}')
    
    print("\n----------------------------")
    values_string = f"toku{rf_prediction_1}v{rf_prediction_2}w{rf_prediction_3}w"
    time.sleep(1)
    print(values_string)
    time.sleep(2)
    ser.write(bytes(values_string, 'utf-8'))
    time.sleep(3)
    print("completed")
    
    # Upload **real sensor readings** (not predictions) to ThingSpeak
    upload_to_thingspeak(feature_1_val, feature_2_val, feature_3_val)
    
    time.sleep(1)
