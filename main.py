from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, computed_field
from fastapi.responses import JSONResponse
from typing import Annotated
import json
import os

app = FastAPI()

FILE_PATH = r"C:\Users\rohan\Desktop\Fast Api\patients.json"


# ==============================
# Pydantic Model
# ==============================
class Patient(BaseModel):

    id: Annotated[str, Field(..., description="Unique patient ID", example="P001")]
    name: Annotated[str, Field(..., description="Patient name", example="John Doe")]
    city: Annotated[str, Field(..., description="City", example="Pune")]
    age: Annotated[int, Field(..., gt=0, description="Age", example=25)]
    gender: Annotated[str, Field(..., description="Gender", example="Male")]
    height: Annotated[float, Field(..., gt=0, description="Height in cm", example=175)]
    weight: Annotated[float, Field(..., gt=0, description="Weight in kg", example=70)]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / ((self.height / 100) ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi >= 30:
            return "Obese"
        elif self.bmi >= 25:
            return "Overweight"
        elif self.bmi >= 18.5:
            return "Normal"
        else:
            return "Underweight"


# ==============================
# File Handling Functions
# ==============================
def load_data():
    if not os.path.exists(FILE_PATH):
        return {}
    with open(FILE_PATH, "r") as f:
        return json.load(f)


def save_data(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ==============================
# Basic Endpoints
# ==============================
@app.get("/")
def home():
    return {"message": "Patient Management System API is running"}


@app.get("/about")
def about():
    return {"message": "FastAPI Patient Management System"}


# ==============================
# View All Patients
# ==============================
@app.get("/view")
def view_patients():
    return load_data()


# ==============================
# Get Patient by ID
# ==============================
@app.get("/patient/{patient_id}")
def get_patient(
    patient_id: str = Path(..., description="Patient ID", example="P001")
):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = Patient(id=patient_id, **data[patient_id])
    return patient.model_dump()


# ==============================
# Create Patient
# ==============================
@app.post("/create")
def create_patient(patient: Patient):

    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400,
                            detail="Patient with this ID already exists")

    data[patient.id] = patient.model_dump(exclude={"id"})
    save_data(data)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Patient created successfully",
            "patient_id": patient.id
        }
    )


# ==============================
# Sort Patients
# ==============================
@app.get("/sort")
def sort_patients(sort_by: str = Query(..., description="height, weight, or bmi"), 
    order: str = Query("asc", description="asc or desc"))  :

    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,
                            detail=f"sort_by must be {valid_fields}")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400,
                            detail="order must be asc or desc")

    data = load_data()

    patients = [
        Patient(id=pid, **info)
        for pid, info in data.items()
    ]

    sorted_patients = sorted(
        patients,
        key=lambda x: getattr(x, sort_by),
        reverse=(order == "desc")
    )

    return [p.model_dump() for p in sorted_patients]


# ==============================
# Update Patient
# ==============================
@app.put("/update/{patient_id}")
def update_patient(patient_id: str, updated_patient: Patient):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    data[patient_id] = updated_patient.model_dump(exclude={"id"})
    save_data(data)

    return {"message": "Patient updated successfully"}


# ==============================
# Delete Patient
# ==============================
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    del data[patient_id]
    save_data(data)

    return {"message": "Patient deleted successfully"}