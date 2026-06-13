import streamlit as st
import pandas as pd
import sqlite3

# -----------------------------
# APP CONFIG
# -----------------------------
st.set_page_config(page_title="Company Portal", layout="wide")

st.markdown("""
<style>

/* Main page */
.stApp {
    background-color: lightblue;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: lightgreen;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: white;
}

/* Tables */
[data-testid="stDataFrame"] {
    background-color: lightblue;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# DB CONNECTION
# -----------------------------
conn = sqlite3.connect("company.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# USERS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    department TEXT
)
""")

# -----------------------------
# QUALITY CONTROL
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS quality_control (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    product_name TEXT,
    counts INTEGER,
    cfus_ml REAL,
    cfu_gm REAL,
    viability REAL,
    contamination REAL,
    benchmark REAL,
    result TEXT
)
""")

# -----------------------------
# MONTDORENSIS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS montdorensis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    counts INTEGER,
    contamination REAL,
    benchmark REAL,
    result TEXT
)
""")

# -----------------------------
# PHITOSEILUS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS phytoseilus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    average_daily_temperature REAL,
    average_daily_humidity REAL,
    morning_harvest_gm REAL,
    evening_harvest_gm REAL,
    benchmark_greenhouse REAL,
    daily_benchmark REAL,
    total_daily_harvest REAL,
    result TEXT
)
""")

# -----------------------------
# BIO MULCH
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS bio_mulch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    cfus_ml REAL,
    contamination REAL,
    bags_produced REAL,
    bags_discarded REAL,
    targeted_bags REAL,
    bags_harvested REAL,
    result TEXT
)
""")

conn.commit()

# -----------------------------
# DEFAULT ADMIN
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO users (username, password, role, department)
    VALUES (?, ?, ?, ?)
    """, ("admin", "1234", "admin", "DataScience"))
    conn.commit()

# -----------------------------
# SESSION STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.department = None

# -----------------------------
# LOGIN
# -----------------------------
if st.session_state.user is None:

    st.title("Company Portal Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("""
        SELECT role, department
        FROM users
        WHERE username=? AND password=?
        """, (username, password))

        user = cursor.fetchone()

        if user:
            st.session_state.user = username
            st.session_state.role = user[0].lower()
            st.session_state.department = user[1]
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# -----------------------------
# DASHBOARD
# -----------------------------
st.title("Company Dashboard")
st.write("User:", st.session_state.user)
st.write("Role:", st.session_state.role)
st.write("Department:", st.session_state.department)

#def load_table(table):
    #return pd.read_sql_query(f"SELECT * FROM {st.table}", conn)
def load_table(table, date_filter=None, product_filter=None):
    query = f"SELECT * FROM {table} WHERE 1=1"
    params = []

    # date filter
    if date_filter:
        query += " AND date = ?"
        params.append(str(date_filter))

    # product filter (only works for tables that have product_name)
    if product_filter and table == "quality_control":
        query += " AND product_name LIKE ?"
        params.append(f"%{product_filter}%")

    return pd.read_sql_query(query, conn, params=params)

tables = ["quality_control", "montdorensis", "phytoseilus", "bio_mulch"]

#for t in tables:
   # st.subheader(t)
    #st.dataframe(load_table(t))
# -----------------------------
# ROLE-BASED TABLE ACCESS
# -----------------------------
st.title("Department Data")

role = st.session_state.role

if role == "admin":
    allowed_tables = ["quality_control", "montdorensis", "phytoseilus", "bio_mulch"]

elif role == "qc":
    allowed_tables = ["quality_control"]

elif role == "montdorensis":
    allowed_tables = ["montdorensis"]

elif role == "phytoseilus":
    allowed_tables = ["phytoseilus"]

elif role == "bio_mulch":
    allowed_tables = ["bio_mulch"]

else:
    allowed_tables = []

for t in allowed_tables:
    st.subheader(t)
    st.dataframe(load_table(t))

# -----------------------------
# QUALITY CONTROL
# -----------------------------
if st.session_state.role in ["admin", "qc"]:

    st.title("Quality Control Entry")

    with st.form("qc_form"):

        date = st.date_input("Date", key="qc_date")
        product = st.text_input("Product", key="qc_product")
        counts = st.number_input("Counts", min_value=0, key="qc_counts")
        cfus_ml = st.number_input("CFUs/ml", format="%e", key="qc_cfus_ml")
        cfu_gm = st.number_input("CFU/gm", format="%e", key="qc_cfu_gm")
        viability = st.number_input("Viability (%)", key="qc_viability")
        contamination = st.number_input(
            "Contamination",
            format="%e",
            key="qc_contamination"
        )
        benchmark = st.number_input(
            "Benchmark",
            format="%e",
            key="qc_benchmark"
        )
        result = st.selectbox(
            "Result",
            ["Pass", "Fail"],
            key="qc_result"
        )

        submit_qc = st.form_submit_button("Save")

        if submit_qc:
            cursor.execute("""
            INSERT INTO quality_control (
                date, product_name, counts,
                cfus_ml, cfu_gm, viability,
                contamination, benchmark, result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(date), product, counts,
                cfus_ml, cfu_gm, viability,
                contamination, benchmark, result
            ))
            conn.commit()
            st.success("Saved")
# -----------------------------
# MONTDORENSIS
# -----------------------------
if st.session_state.role in ["admin", "montdorensis"]:

    st.title("Montdorensis Entry")

    with st.form("mont_form"):

        date = st.date_input("Date", key="mont_date")
        counts = st.number_input("Counts", min_value=0, key="mont_counts")
        contamination = st.number_input("Contamination", key="mont_cont")
        benchmark = st.number_input("Benchmark", key="mont_bench")
        result = st.selectbox(
            "Result",
            ["Pass", "Fail"],
            key="mont_result"
        )

        submit_mont = st.form_submit_button("Save")

        if submit_mont:
            cursor.execute("""
            INSERT INTO montdorensis
            (date, counts, contamination, benchmark, result)
            VALUES (?, ?, ?, ?, ?)
            """, (
                str(date),
                counts,
                contamination,
                benchmark,
                result
            ))

            conn.commit()
            st.success("Saved")
            
# -----------------------------
# PHITOSEILUS
# -----------------------------
if st.session_state.role in ["admin", "phytoseilus"]:

    st.title("Phytoseilus Entry")

    with st.form("phyto_form"):

        date = st.date_input("Date", key="phy_date")
        temp = st.number_input("Temperature", key="phy_temp")
        humidity = st.number_input("Humidity", key="phy_hum")
        morning = st.number_input("Morning Harvest", key="phy_morn")
        evening = st.number_input("Evening Harvest", key="phy_even")
        bench_g = st.number_input("Greenhouse Benchmark", key="phy_bench")
        daily_bench = st.number_input("Daily Benchmark", key="phy_daily")
        total = st.number_input("Total Harvest", key="phy_total")
        result = st.selectbox(
            "Result",
            ["Pass", "Fail"],
            key="phy_result"
        )

        submit_phyto = st.form_submit_button("Save")

        if submit_phyto:
            cursor.execute("""
            INSERT INTO phytoseilus (
                date,
                average_daily_temperature,
                average_daily_humidity,
                morning_harvest_gm,
                evening_harvest_gm,
                benchmark_greenhouse,
                daily_benchmark,
                total_daily_harvest,
                result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(date),
                temp,
                humidity,
                morning,
                evening,
                bench_g,
                daily_bench,
                total,
                result
            ))

            conn.commit()
            st.success("Saved")

# -----------------------------
# BIO MULCH
# -----------------------------
if st.session_state.role in ["admin", "bio_mulch"]:

    st.title("Bio Mulch Entry")

    with st.form("bio_form"):

        date = st.date_input("Date", key="bio_date")
        cfus_ml = st.number_input(
            "CFUs/ml",
            format="%e",
            key="bio_cfus"
        )

        contamination = st.number_input(
            "Contamination",
            format="%e",
            key="bio_cont"
        )

        produced = st.number_input(
            "Bags Produced",
            key="bio_prod"
        )

        discarded = st.number_input(
            "Bags Discarded",
            key="bio_disc"
        )

        target = st.number_input(
            "Targeted Bags",
            key="bio_target"
        )

        harvested = st.number_input(
            "Bags Harvested",
            key="bio_harvest"
        )

        result = st.selectbox(
            "Result",
            ["Pass", "Fail"],
            key="bio_result"
        )

        submit_bio = st.form_submit_button("Save")

        if submit_bio:

            cursor.execute("""
            INSERT INTO bio_mulch (
                date,
                cfus_ml,
                contamination,
                bags_produced,
                bags_discarded,
                targeted_bags,
                bags_harvested,
                result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(date),
                cfus_ml,
                contamination,
                produced,
                discarded,
                target,
                harvested,
                result
            ))

            conn.commit()
            st.success("Saved")

# -----------------------------
# USER MANAGEMENT
# -----------------------------
if st.session_state.role == "admin":

    st.title("User Management")

    with st.form("user_form"):
        u = st.text_input("Username", key="u1")
        p = st.text_input("Password", type="password", key="p1")
        r = st.selectbox("Role", ["admin", "qc", "montdorensis", "bio_mulch", "phytoseilus"], key="r1")
        d = st.text_input("Department", key="d1")

        if st.form_submit_button("Add"):
            cursor.execute("""
            INSERT INTO users (username, password, role, department)
            VALUES (?, ?, ?, ?)
            """, (u, p, r, d))
            conn.commit()
            st.success("User added")