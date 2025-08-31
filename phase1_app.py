# phase1_app.py
import streamlit as st

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
# Nutrition database (dummy for Phase 1)
# ----------------------------
nutrition_db = {
    "Chapati": {"calories": 104, "protein": 3, "fat": 2, "carbs": 19},
    "Dal": {"calories": 120, "protein": 6, "fat": 4, "carbs": 15},
    "Paneer": {"calories": 200, "protein": 12, "fat": 14, "carbs": 6},
    "Rice": {"calories": 130, "protein": 2.5, "fat": 0.3, "carbs": 28},
}

# ----------------------------
# Streamlit App
# ----------------------------
st.title("🍲 Indian Food Calorie & Diet Tracker (Phase 1)")

# Sidebar for user profile
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

    for item in nutrition_db.keys():
        if item.lower() in food_input.lower():
            vals = nutrition_db[item]
            total_cals += vals["calories"]
            total_protein += vals["protein"]
            total_fat += vals["fat"]
            total_carbs += vals["carbs"]

    st.subheader("Estimated Nutrition")
    st.write(f"Calories: {total_cals} kcal")
    st.write(f"Protein: {total_protein} g")
    st.write(f"Fat: {total_fat} g")
    st.write(f"Carbs: {total_carbs} g")

    st.progress(min(int(total_cals / daily_needs * 100), 100))
