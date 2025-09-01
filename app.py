# 🍛 Indian Food Calorie Tracker

import re
import streamlit as st
import pandas as pd
from PIL import Image
from transformers import pipeline
from rapidfuzz import process, fuzz

# ✅ Set page config
st.set_page_config(page_title="Indian Food Calorie Tracker", layout="centered")

# ----------------------------
# Load Nutrition DB
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("indian_food_with_nutrition_v4.csv")
    df.columns = df.columns.str.strip().str.lower()
    if "food" not in df.columns and "name" in df.columns:
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
            "quantity": qty,
            "calories": row.get("calories", 0) * qty,
            "protein": row.get("protein_g", 0) * qty,
            "fat": row.get("fat_g", 0) * qty,
            "carbs": row.get("carbs_g", 0) * qty
        }, score
    else:
        return None, score

# ----------------------------
# BMI & BMR
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
# Init Session State
# ----------------------------
if "food_log" not in st.session_state:
    st.session_state.food_log = []

# ----------------------------
# Sidebar: User profile
# ----------------------------
st.sidebar.header("User Profile")
weight = st.sidebar.number_input("Weight (kg)", 40, 150, 70)
height = st.sidebar.number_input("Height (cm)", 140, 210, 170)
age = st.sidebar.number_input("Age", 10, 80, 25)
gender = st.sidebar.radio("Gender", ["Male", "Female"])
activity = st.sidebar.selectbox(
    "Activity Level",
    ["Sedentary", "Light", "Moderate", "Active", "Very Active"]
)

bmi = calculate_bmi(weight, height)
bmr = calculate_bmr(weight, height, age, gender)
daily_needs = round(bmr * activity_multiplier(activity), 2)

st.sidebar.markdown(f"**BMI:** {bmi}")
st.sidebar.markdown(f"**Daily Calorie Needs:** {daily_needs} kcal")

# ----------------------------
# Tabs: Manual vs Image Input
# ----------------------------
tab1, tab2 = st.tabs(["Manual Entry", "Upload Image"])

# --------- Manual Entry ---------
with tab1:
    st.header("🍲 Manual Food Entry")
    food_input = st.text_input("E.g. 2 Chapati and 1 Dal")

    if food_input:
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
                st.write(f"{qty} x {nutrition['food']} ({score:.0f}%)")
                if st.button(f"Add {qty} x {nutrition['food']} to Log", key=f"manual_{food}"):
                    st.session_state.food_log.append(nutrition)

# --------- Image Upload ---------
with tab2:
    st.header("📸 Upload Food Image")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        preds = classifier(image)
        st.subheader("Predicted Foods")
        for i, pred in enumerate(preds[:3]):
            food_name = pred['label']
            score = pred['score'] * 100
            st.write(f"{food_name} ({score:.1f}%)")

            if score > 60:
                nutrition, _ = get_food_nutrition(food_name, df)
                if nutrition:
                    if st.button(f"Add {nutrition['food']} to Log", key=f"image_{i}"):
                        st.session_state.food_log.append(nutrition)

# ----------------------------
# Nutrition Summary & Log
# ----------------------------
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

    # ✅ Progress toward daily needs
    progress = min(total_cals / daily_needs, 1.0)
    st.progress(progress)

    # ✅ Show food log as a table
    st.subheader("Food Log")
    log_df = pd.DataFrame(st.session_state.food_log)
    st.dataframe(log_df, use_container_width=True)

    # ✅ Clear log button
    if st.button("Clear Log"):
        st.session_state.food_log = []
        st.success("Food log cleared!")


# ----------------------------
# Disclaimer (always visible)
# ----------------------------
st.caption(
    "⚠️ Disclaimer: Nutrition values are approximate and may vary depending on serving size (e.g., 100g, 1 piece, 1 cup) and preparation method."
)
