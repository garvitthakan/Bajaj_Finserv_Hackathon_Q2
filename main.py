import pandas as pd
import json

# Load JSON data
with open('./DataEngineeringQ2.json') as file:
    json_data = file.read()

# Parse JSON data
data = json.loads(json_data)

# Extract required columns from JSON data
appointments = []
for item in data:
    patient_details = item['patientDetails']
    gender = patient_details.get('gender', None)
    birth_date = patient_details.get('birthDate', None)
    appointment = {
        'appointmentId': item['appointmentId'],
        'phoneNumber': item['phoneNumber'],
        'firstName': patient_details['firstName'],
        'lastName': patient_details['lastName'],
        'gender': gender if gender in ['M', 'F'] else   None,
        'DOB': birth_date,
        'medicines': item['consultationData']['medicines']
    }
    appointments.append(appointment)

# Create DataFrame from extracted data
df = pd.DataFrame(appointments)

# Renaming birthDate column as DOB
df.rename(columns={"birthDate": "DOB"}, inplace=True)


# Transforming phoneNumber column
# Validating if the number is a valid Indian phone number
def is_valid_mobile(number):
    if number is None:
        return False
    number = str(number)
    if number.startswith("+91"):
        number = number[3:]
    elif number.startswith("91"):
        number = number[2:]
    return number.isdigit() and 6000000000 <= int(number) <= 9999999999


df["isValidMobile"] = df["phoneNumber"].apply(is_valid_mobile)

# Creating fullName column
df["fullName"] = df["firstName"] + " " + df["lastName"]

import hashlib
# Hashing valid phone numbers
def hash_phone_number(number):
    if number is None or not is_valid_mobile(number):
        return None
    number = str(number)
    if number.startswith("+91"):
        number = number[3:]
    elif number.startswith("91"):
        number = number[2:]
    return hashlib.sha256(number.encode()).hexdigest()

df["phoneNumberHash"] = df["phoneNumber"].apply(hash_phone_number)

# Calculating age
def calculate_age(birth_date):
    if birth_date is None:
        return None
    birth_date = pd.to_datetime(birth_date)
    today = pd.Timestamp.now()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age
df["Age"] = df["DOB"].apply(calculate_age)

# Aggregating columns by appointmentId
df["noOfMedicines"] = df["medicines"].apply(lambda x: len(x))
df["noOfActiveMedicines"] = df["medicines"].apply(lambda x: sum(1 for med in x if med["isActive"]))
df["noOfInActiveMedicines"] = df["medicines"].apply(lambda x: sum(1 for med in x if not med["isActive"]))
df["medicineNames"] = df["medicines"].apply(lambda x: ", ".join(med["medicineName"] for med in x if med["isActive"]))
# Remove the 'medicines' column if not needed
# df = df.drop("medicines", axis=1)


# Selecting final columns
df = df[["appointmentId", "fullName", "phoneNumber", "isValidMobile", "phoneNumberHash", "gender", "DOB", "Age",
         "noOfMedicines", "noOfActiveMedicines", "noOfInActiveMedicines", "medicineNames"]]


# Exporting dataframe to CSV file
df.to_csv("output.csv", sep="~", index=False)

df = df.astype(object)  # Convert all columns to object data type
df["phoneNumber"] = df["phoneNumber"].astype(str)  # Convert phoneNumber column to string

# Aggregating data for export to JSON
aggregated_data = {
    "Age": df["Age"].mean(),
    "gender": df["gender"].value_counts().to_dict(),
    "validPhoneNumbers": df["isValidMobile"].sum(),
    "appointments": len(df),
    "medicines": df["noOfMedicines"].sum(),
    "activeMedicines": df["noOfActiveMedicines"].sum()
}

# Exporting aggregated data to JSON
with open("aggregated_data.json", "w") as file:
    json.dump(aggregated_data, file, indent=4)

# Plotting a pie chart for number of appointments against gender
import matplotlib.pyplot as plt

gender_counts = df["gender"].value_counts(dropna = False)
plt.pie(gender_counts, labels=gender_counts.index, autopct="%1.1f%%")
plt.axis("equal")
plt.title("Number of Appointments by Gender")
plt.show()