# phase2_app.py
import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# ----------------------------
# Helper functions
# ----------------------------
def calculate_bmi(weight, height):
    height_m = height / 100
    return round(weight / (height_m ** 2), 2)

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
# Load Nutrition DB
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("indian_food_with_nutrition_v3.csv")
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    # Rename if needed
    if "name" in df.columns:
        df = df.rename(columns={"name": "food"})
    return df

df = load_data()

# Debug helper (to see structure)
st.sidebar.write("📊 DB Preview:", df.head())

# ----------------------------
# Nutrition Lookup
# ----------------------------
def get_food_nutrition(food_name, df, qty=1):
    choices = df["food"].tolist()
    match, score, idx = process.extractOne(food_name, choices, scorer=fuzz.WRatio)
    if score > 60:  # threshold
        row = df.iloc[idx]
        return {
            "food": match,
            "calories": row["calories"] * qty if "calories" in row else 0,
            "protein": row["protein_g"] * qty if "protein_g" in row else 0,
            "fat": row["fat_g"] * qty if "fat_g" in row else 0,
            "carbs": row["carbs_g"] * qty if "carbs_g" in row else 0
        }, score
    else:
        return None, score

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🍲 Indian Food Calorie & Diet Tracker (Phase 2)")

# Sidebar - User Profile
st.sidebar.header("User Profile")
weight = st.sidebar.number_input("Weight (kg)", 40, 150, 70)
height = st.sidebar.number_input("Height (cm)", 140, 210, 170)
age = st.sidebar.number_input("Age", 10, 80, 25)
gender = st.sidebar.radio("Gender", ["Male", "Female"])
activity = st.sidebar.selectbox("Activity Level",
                                ["Sedentary", "Light", "Moderate", "Active", "Very Active"])

# BMI & Calorie Needs
bmi = calculate_bmi(weight, height)
bmr = calculate_bmr(weight, height, age, gender)
daily_needs = round(bmr * activity_multiplier(activity), 2)

st.sidebar.markdown(f"**Your BMI:** {bmi}")
st.sidebar.markdown(f"**Daily Calorie Needs:** {daily_needs} kcal")

# Food input
st.header("🍛 Enter Food (Manual Lookup)")
food_input = st.text_input("E.g. 2 Chapati and Dal")

if food_input:
    total_cals, total_protein, total_fat, total_carbs = 0, 0, 0, 0
    found_items = []

    for word in food_input.split(" and "):
        qty = 1
        parts = word.strip().split()
        if parts[0].isdigit():
            qty = int(parts[0])
            food = " ".join(parts[1:])
        else:
            food = word.strip()

        nutrition, score = get_food_nutrition(food, df, qty)
        if nutrition:
            total_cals += nutrition["calories"]
            total_protein += nutrition["protein"]
            total_fat += nutrition["fat"]
            total_carbs += nutrition["carbs"]
            found_items.append(f"{qty} x {nutrition['food']} ({score:.0f}%)")

    if found_items:
        st.subheader("Matched Foods")
        st.write(", ".join(found_items))

        st.subheader("Estimated Nutrition")
        st.write(f"Calories: {total_cals:.1f} kcal")
        st.write(f"Protein: {total_protein:.1f} g")
        st.write(f"Fat: {total_fat:.1f} g")
        st.write(f"Carbs: {total_carbs:.1f} g")

        st.progress(min(int(total_cals / daily_needs * 100), 100))
    else:
        st.warning("⚠️ No foods matched. Try again.")
