# app.py
import streamlit as st
from transformers import pipeline
import pandas as pd
from rapidfuzz import process, fuzz
from PIL import Image
import random

# ----------------------------
# Load Nutrition DB
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("indian_food_with_nutrition_v3.csv")
    df.columns = df.columns.str.strip().str.lower()
    if "name" in df.columns:
        df.rename(columns={"name": "food"}, inplace=True)
    return df

df = load_data()

# ----------------------------
# Helper: Nutrition lookup
# ----------------------------
def get_food_nutrition(food_name, df, qty=1):
    choices = df["food"].tolist()
    match, score, idx = process.extractOne(food_name, choices, scorer=fuzz.WRatio)
    if score > 60:  # threshold
        row = df.iloc[idx]
        return {
            "food": match,
            "calories": row.get("calories", 0) * qty,
            "protein": row.get("protein_g", 0) * qty,
            "fat": row.get("fat_g", 0) * qty,
            "carbs": row.get("carbs_g", 0) * qty
        }, score
    else:
        return None, score

# ----------------------------
# Helper: BMI & BMR
# ----------------------------
def calculate_bmi(weight, height):
    return round(weight / ((height/100)**2), 2)

def calculate_bmr(weight, height, age, gender):
    if gender == "Male":
        return 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        return 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)

def activity_multiplier(level):
    return {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Active": 1.725,
        "Very Active": 1.9
    }[level]

# ----------------------------
# Load Hugging Face model
# ----------------------------
@st.cache_resource
def load_model():
    return pipeline("image-classification", model="NOTGOD6000/finetuned-indian-food")

classifier = load_model()

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🍛 Indian Food Calorie Tracker")

# Sidebar: User profile
st.sidebar.header("User Profile")
weight = st.sidebar.number_input("Weight (kg)", 40, 150, 70)
height = st.sidebar.number_input("Height (cm)", 140, 210, 170)
age = st.sidebar.number_input("Age", 10, 80, 25)
gender = st.sidebar.radio("Gender", ["Male", "Female"])
activity = st.sidebar.selectbox("Activity Level",
                                ["Sedentary", "Light", "Moderate", "Active", "Very Active"])

bmi = calculate_bmi(weight, height)
bmr = calculate_bmr(weight, height, age, gender)
daily_needs = round(bmr * activity_multiplier(activity), 2)

st.sidebar.markdown(f"**BMI:** {bmi}")
st.sidebar.markdown(f"**Daily Calorie Needs:** {daily_needs} kcal")

# ----------------------------
# Tabs: Manual vs Image Input
# ----------------------------
tab1, tab2 = st.tabs(["Manual Entry", "Upload Image"])

# Store combined food entries
if "food_log" not in st.session_state:
    st.session_state.food_log = []

# --------- Manual Entry ---------
with tab1:
    st.header("🍲 Manual Food Entry")
    food_input = st.text_input("E.g. 2 Chapati and Dal")
    
    if food_input:
        total_cals, total_protein, total_fat, total_carbs = 0, 0, 0, 0
        found_items = []

        for item in food_input.split(" and "):
            qty = 1
            parts = item.strip().split()
            if parts[0].isdigit():
                qty = int(parts[0])
                food = " ".join(parts[1:])
            else:
                food = item.strip()

            nutrition, score = get_food_nutrition(food, df, qty)
            if nutrition:
                total_cals += nutrition["calories"]
                total_protein += nutrition["protein"]
                total_fat += nutrition["fat"]
                total_carbs += nutrition["carbs"]
                found_items.append(f"{qty} x {nutrition['food']} ({score:.0f}%)")
                st.session_state.food_log.append(nutrition)

        if found_items:
            st.subheader("Matched Foods")
            st.write(", ".join(found_items))

# --------- Image Upload ---------
with tab2:
    st.header("📸 Upload Food Image")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)  # FIXED

        preds = classifier(image)
        st.subheader("Predicted Foods")
        for pred in preds[:3]:
            food_name = pred['label']
            score = pred['score'] * 100
            st.write(f"{food_name} ({score:.1f}%)")
            
            # Add to log if confidence > threshold
            if score > 60:
                nutrition, _ = get_food_nutrition(food_name, df)
                if nutrition:
                    st.session_state.food_log.append(nutrition)

# --------- Nutrition Summary ---------
if st.session_state.food_log:
    st.header("🥗 Today's Food Summary")
    total_cals = sum(item["calories"] for item in st.session_state.food_log)
    total_protein = sum(item["protein"] for item in st.session_state.food_log)
    total_fat = sum(item["fat"] for item in st.session_state.food_log)
    total_carbs = sum(item["carbs"] for item in st.session_state.food_log)

    st.write(f"**Calories:** {total_cals:.1f} kcal")
    st.write(f"**Protein:** {total_protein:.1f} g")
    st.write(f"**Fat:** {total_fat:.1f} g")
    st.write(f"**Carbs:** {total_carbs:.1f} g")

    # Show progress toward daily needs safely
    if daily_needs > 0:
        st.progress(min(int(total_cals / daily_needs * 100), 100))
    else:
        st.warning("Please enter valid profile details in the sidebar to track progress.")
