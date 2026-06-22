import os
from PIL import Image
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
img_path = os.path.join(BASE_DIR, "assets", "logo.png")

img = Image.open(img_path)
st.image(img)
img.thumbnail((50,50))

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Predator Finder & Analysis App",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🕷️ Predator Finder & Analysis App")

# ---------------- CLASS ----------------
class Predator:
    def __init__(self, name, size, shape, colour, aggressive, development_speed):
        self.name = name
        self.size = size
        self.shape = shape
        self.colour = colour
        self.aggressive = aggressive
        self.development_speed = development_speed


# ---------------- DATA ----------------
predators = [
    Predator(
        "Neoseiulus californicus",
        "medium",
        "oval_to_teardrop",
        "grey",
        False,
        "moderate"
    ),

    Predator(
        "Typhlodromus montdorensis",
        "medium",
        "oval_slender",
        "cream_tan",
        True,
        "fast"
    ),

    Predator(
        "Amblyseius cucumeris",
        "medium",
        "pear_shaped",
        "beige_tan",
        False,
        "moderate"
    ),

    Predator(
        "Amblyseius swirskii",
        "medium",
        "broad_oval",
        "light_tan",
        True,
        "fast"
    )
]

# ---------------- SESSION STATE ----------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ---------------- INPUT FORM ----------------
if not st.session_state.submitted:

    st.subheader("🔎 Enter Search Criteria")

    search_size = st.selectbox(
        "Size",
        ["small", "medium", "big"]
    )

    search_shape = st.selectbox(
        "Shape",
        ["pear_shaped", "oval_to_teardrop", "broad_oval", "oval_slender"]
    )

    search_colour = st.selectbox(
        "Colour",
        ["grey", "light_tan", "beige_tan", "cream_tan"]
    )

    search_aggressive = st.selectbox(
        "Aggressive?",
        ["True", "False"]
    )

    search_development_speed = st.selectbox(
        "Development Speed",
        ["fast", "moderate", "slow"]
    )

    if st.button("Find Predator"):
        st.session_state.search_size = search_size
        st.session_state.search_shape = search_shape
        st.session_state.search_colour = search_colour
        st.session_state.search_aggressive = (search_aggressive == "True")
        st.session_state.search_development_speed = search_development_speed
        st.session_state.submitted = True
        st.rerun()

# ---------------- RESULT SECTION ----------------
if st.session_state.submitted:

    st.subheader("📊 Result")

    found = None
    best_percentage = 0

    # Search for the closest matching predator
    for p in predators:

        score = 0

        if p.size == st.session_state.search_size:
            score += 1

        if p.shape == st.session_state.search_shape:
            score += 1

        if p.colour == st.session_state.search_colour:
            score += 1

        if p.aggressive == st.session_state.search_aggressive:
            score += 1

        if p.development_speed == st.session_state.search_development_speed:
            score += 1

        percentage = (score / 5) * 100

        if percentage > best_percentage:
            best_percentage = percentage
            found = p

    # Display result
    if best_percentage == 100:
        st.success(f"✅ Identified Predator: {found.name}")

    elif best_percentage >= 75:
        st.warning(
            f"⚠️ Predator likely to be **{found.name}** "
            f"(Confidence: {best_percentage:.0f}%)"
        )

    elif best_percentage >= 70:
        st.info(
            f"ℹ️ Predator possibly resembles **{found.name}** "
            f"(Confidence: {best_percentage:.0f}%)"
        )

    else:
        st.error("❌ No close predator match found.")

    # Show details if a match exists
    if found:
        st.write("### Details")
        st.write(f"**Size:** {found.size}")
        st.write(f"**Shape:** {found.shape}")
        st.write(f"**Colour:** {found.colour}")
        st.write(f"**Aggressive:** {found.aggressive}")
        st.write(f"**Development Speed:** {found.development_speed}")

    # Reset button
    if st.button("🔄 New Search"):
        st.session_state.submitted = False
        st.rerun()