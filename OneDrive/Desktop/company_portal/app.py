import streamlit as st
import pandas as pd
import sqlite3

# -----------------------------
# APP CONFIG
# -----------------------------
st.set_page_config(page_title="Company Portal", layout="wide")

st.markdown("""
<style>
.stApp { background-color: lightgreen; }

[data-testid="stSidebar"] {
    background-color: green;
}

[data-testid="stSidebar"] * {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# DB CONNECTION
# -----------------------------
conn = sqlite3.connect("company.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# TABLES
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS quality_control (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    batch_id TEXT,
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS montdorensis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT,
    date TEXT,
    counts INTEGER,
    contamination REAL,
    benchmark REAL,
    result TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS phytoseilus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT,
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS bio_mulch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT,
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
    cursor.executemany("""
    INSERT INTO users (username, password, role, department)
    VALUES (?, ?, ?, ?)
    """, [
        ("admin", "1234", "admin", "DataScience"),
        ("simon", "2345", "phytoseilus", "phytoseilus"),
        ("faith ", "3456", "bio_mulch", "bio_mulch"),
        ("julia", "4567", "montdorensis", "montdorensis"),
        ("judy", "5678", "qc", "quality_control"),
    ])
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

# -----------------------------
# LOAD FUNCTION (FILTERS)
# -----------------------------
def load_table(table, date_filter=None, batch_filter=None):
    query = f"SELECT * FROM {table} WHERE 1=1"
    params = []

    if date_filter:
        query += " AND date = ?"
        params.append(str(date_filter))

    if batch_filter:
        query += " AND batch_id LIKE ?"
        params.append(f"%{batch_filter}%")

    return pd.read_sql_query(query, conn, params=params)

# -----------------------------
# ROLE ACCESS TABLES
# -----------------------------
st.title("📊 Department Data")

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

# -----------------------------
# TABLES WITH INDIVIDUAL FILTERS
# -----------------------------
for t in allowed_tables:

    st.subheader(f"📊 {t}")

    col1, col2 = st.columns(2)

    with col1:
        date_filter = st.date_input(f"{t} - Date Filter", key=f"date_{t}")

    with col2:
        batch_filter = st.text_input(f"{t} - Batch Filter", key=f"batch_{t}")

    st.dataframe(load_table(t, date_filter, batch_filter))

# -----------------------------
# QUALITY CONTROL ENTRY
# -----------------------------
if st.session_state.role in ["admin", "qc"]:

    st.title("Quality Control Entry")

    with st.form("qc_form"):
        date = st.date_input("Date")
        batch_id = st.text_input("Batch ID")
        product = st.text_input("Product")
        counts = st.number_input("Counts", min_value=0)
        cfus_ml = st.number_input("CFUs/ml", format="%e")
        cfu_gm = st.number_input("CFU/gm", format="%e")
        viability = st.number_input("Viability")
        contamination = st.number_input("Contamination", format="%e")
        benchmark = st.number_input("Benchmark", format="%e")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO quality_control (
                date, batch_id, product_name, counts,
                cfus_ml, cfu_gm, viability,
                contamination, benchmark, result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(date), batch_id, product, counts,
                cfus_ml, cfu_gm, viability,
                contamination, benchmark, result
            ))
            conn.commit()
            st.success("Saved")

# -----------------------------
# MONTDORENSIS ENTRY
# -----------------------------
if st.session_state.role in ["admin", "montdorensis"]:

    st.title("Montdorensis Entry")

    with st.form("mont_form"):
        date = st.date_input("Date")
        batch_id = st.text_input("Batch ID")
        counts = st.number_input("Counts", min_value=0)
        contamination = st.number_input("Contamination")
        benchmark = st.number_input("Benchmark")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO montdorensis (
                batch_id, date, counts, contamination, benchmark, result
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                batch_id, str(date), counts,
                contamination, benchmark, result
            ))
            conn.commit()
            st.success("Saved")

# -----------------------------
# PHITOSEILUS ENTRY
# -----------------------------
if st.session_state.role in ["admin", "phytoseilus"]:

    st.title("Phytoseilus Entry")

    with st.form("phyto_form"):
        date = st.date_input("Date")
        batch_id = st.text_input("Batch ID")
        temp = st.number_input("Temperature")
        humidity = st.number_input("Humidity")
        morning = st.number_input("Morning Harvest")
        evening = st.number_input("Evening Harvest")
        bench_g = st.number_input("Greenhouse Benchmark")
        daily_bench = st.number_input("Daily Benchmark")
        total = st.number_input("Total Harvest")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO phytoseilus (
                batch_id, date,
                average_daily_temperature,
                average_daily_humidity,
                morning_harvest_gm,
                evening_harvest_gm,
                benchmark_greenhouse,
                daily_benchmark,
                total_daily_harvest,
                result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id, str(date),
                temp, humidity,
                morning, evening,
                bench_g, daily_bench,
                total, result
            ))
            conn.commit()
            st.success("Saved")

# -----------------------------
# BIO MULCH ENTRY
# -----------------------------
if st.session_state.role in ["admin", "bio_mulch"]:

    st.title("Bio Mulch Entry")

    with st.form("bio_form"):
        date = st.date_input("Date")
        batch_id = st.text_input("Batch ID")
        cfus_ml = st.number_input("CFUs/ml", format="%e")
        contamination = st.number_input("Contamination", format="%e")
        produced = st.number_input("Bags Produced")
        discarded = st.number_input("Bags Discarded")
        target = st.number_input("Targeted Bags")
        harvested = st.number_input("Bags Harvested")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO bio_mulch (
                batch_id, date, cfus_ml, contamination,
                bags_produced, bags_discarded,
                targeted_bags, bags_harvested, result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id, str(date), cfus_ml, contamination,
                produced, discarded, target, harvested, result
            ))
            conn.commit()
            st.success("Saved")

# -----------------------------
# USER MANAGEMENT
# -----------------------------
if st.session_state.role == "admin":

    st.title("User Management")

    with st.form("user_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        r = st.selectbox("Role", ["admin", "qc", "montdorensis", "bio_mulch", "phytoseilus"])
        d = st.text_input("Department")

        if st.form_submit_button("Add"):
            try:
                cursor.execute("""
                INSERT INTO users (username, password, role, department)
                VALUES (?, ?, ?, ?)
                """, (u, p, r, d))
                conn.commit()
                st.success("User added")
            except sqlite3.IntegrityError:
                st.error("Username already exists")