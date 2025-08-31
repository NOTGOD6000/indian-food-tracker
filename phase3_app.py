# phase3_app.py
import streamlit as st
from transformers import pipeline
import pandas as pd
from rapidfuzz import process, fuzz
from PIL import Image

# ----------------------------
# Load Nutrition DB
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("indian_food_with_nutrition_v3.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# ----------------------------
# Helper: Match model prediction to DB
# ----------------------------
def get_food_nutrition(food_name, df, qty=1):
    choices = df["name"].tolist()
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
# Load Hugging Face model
# ----------------------------
classifier = pipeline("image-classification", model="NOTGOD6000/finetuned-indian-food")

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🍛 Indian Food Calorie Calculator (Phase 3)")

uploaded_file = st.file_uploader("Upload a food image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Convert to PIL for Hugging Face
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # Run prediction
    preds = classifier(image)
    food_name = preds[0]['label']
    st.write(f"🔍 Predicted Food: **{food_name}**")

    # Lookup nutrition info
    nutrition, score = get_food_nutrition(food_name, df)
    if nutrition:
        st.subheader("🥗 Nutrition Info")
        st.write(f"Matched: {nutrition['food']} ({score:.0f}%)")
        st.write(f"Calories: {nutrition['calories']:.1f} kcal")
        st.write(f"Protein: {nutrition['protein']:.1f} g")
        st.write(f"Fat: {nutrition['fat']:.1f} g")
        st.write(f"Carbs: {nutrition['carbs']:.1f} g")
    else:
        st.warning("⚠️ Food not found in dataset!")
