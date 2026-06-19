import streamlit as st
import pandas as pd
import sqlite3
import io

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
# DEFAULT USER
# -----------------------------
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO users (username, password, role, department)
    VALUES (?, ?, ?, ?)
    """, ("admin", "1234", "admin", "DataScience"))
    conn.commit()

# -----------------------------
# SESSION
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

# -----------------------------
# LOGIN
# -----------------------------
if st.session_state.user is None:

    st.title("Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("""
        SELECT role FROM users WHERE username=? AND password=?
        """, (u, p))

        res = cursor.fetchone()

        if res:
            st.session_state.user = u
            st.session_state.role = res[0].strip().lower()
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

view = st.selectbox("View Data", ["Show", "Hide"])
search = st.text_input("Search all tables")

# -----------------------------
# ROLE TABLE MAP
# -----------------------------
role = st.session_state.role

tables_map = {
    "admin": ["quality_control", "montdorensis", "phytoseilus", "bio_mulch"],
    "qc": ["quality_control"],
    "montdorensis": ["montdorensis"],
    "phytoseilus": ["phytoseilus"],
    "bio_mulch": ["bio_mulch"]
}

tables = tables_map.get(role, [])

# -----------------------------
# HELPERS
# -----------------------------
def load_table(table, search=None):
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

    if search:
        search = search.lower()
        df = df[df.astype(str).apply(
            lambda r: r.str.lower().str.contains(search).any(),
            axis=1
        )]

    return df

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# -----------------------------
# VIEW DATA
# -----------------------------
if view == "Show":

    st.title("Saved Data")

    for t in tables:

        st.subheader(t)

        df = load_table(t, search)

        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download Excel",
            data=to_excel(df),
            file_name=f"{t}.xlsx"
        )

        if "counts" in df.columns:
            st.line_chart(df.set_index("date")["counts"])

else:
    st.info("Data hidden")

# -----------------------------
# QC FORM
# -----------------------------
if role in ["admin", "qc"]:

    st.title("Quality Control")

    with st.form("qc"):
        date = st.date_input("Date")
        batch = st.text_input("Batch ID")
        product = st.text_input("Product")
        counts = st.number_input("Counts")
        cfus = st.number_input("CFUs/ml")
        cfu_gm = st.number_input("CFU/gm")
        viability = st.number_input("Viability")
        contamination = st.number_input("Contamination")
        benchmark = st.number_input("Benchmark")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO quality_control (
                date, batch_id, product_name, counts,
                cfus_ml, cfu_gm, viability,
                contamination, benchmark, result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(date), batch, product, counts,
                  cfus, cfu_gm, viability,
                  contamination, benchmark, result))
            conn.commit()
            st.success("Saved")

# -----------------------------
# MONTDORENSIS FORM
# -----------------------------
if role in ["admin", "montdorensis"]:

    st.title("Montdorensis")

    with st.form("mont"):
        date = st.date_input("Date")
        batch = st.text_input("Batch ID")
        counts = st.number_input("Counts")
        contamination = st.number_input("Contamination")
        benchmark = st.number_input("Benchmark")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO montdorensis (
                batch_id, date, counts, contamination, benchmark, result
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (batch, str(date), counts, contamination, benchmark, result))
            conn.commit()
            st.success("Saved")

# -----------------------------
# PHITOSEILUS FORM
# -----------------------------
if role in ["admin", "phytoseilus"]:

    st.title("Phytoseilus")

    with st.form("phyto"):
        date = st.date_input("Date")
        batch = st.text_input("Batch ID")
        temp = st.number_input("Temperature")
        humidity = st.number_input("Humidity")
        morning = st.number_input("Morning Harvest")
        evening = st.number_input("Evening Harvest")
        bench = st.number_input("Benchmark")
        daily = st.number_input("Daily Benchmark")
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
            """, (batch, str(date), temp, humidity,
                  morning, evening, bench, daily, total, result))
            conn.commit()
            st.success("Saved")

# -----------------------------
# BIO MULCH FORM
# -----------------------------
if role in ["admin", "bio_mulch"]:

    st.title("Bio Mulch")

    with st.form("bio"):
        date = st.date_input("Date")
        batch = st.text_input("Batch ID")
        cfus = st.number_input("CFUs/ml")
        contamination = st.number_input("Contamination")
        produced = st.number_input("Produced")
        discarded = st.number_input("Discarded")
        target = st.number_input("Target")
        harvested = st.number_input("Harvested")
        result = st.selectbox("Result", ["Pass", "Fail"])

        if st.form_submit_button("Save"):
            cursor.execute("""
            INSERT INTO bio_mulch (
                batch_id, date, cfus_ml, contamination,
                bags_produced, bags_discarded,
                targeted_bags, bags_harvested, result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (batch, str(date), cfus, contamination,
                  produced, discarded, target, harvested, result))
            conn.commit()
            st.success("Saved")

# -----------------------------
# USER MANAGEMENT (ADMIN ONLY)
# -----------------------------
if st.session_state.role == "admin":

    st.title("👤 User Management")

    tab1, tab2 = st.tabs(["➕ Add User", "📋 View Users"])

    # ----------------- ADD USER -----------------
    with tab1:
        with st.form("user_form"):

            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            r = st.selectbox("Role", [
                "admin",
                "qc",
                "montdorensis",
                "bio_mulch",
                "phytoseilus"
            ])
            d = st.text_input("Department")

            submit = st.form_submit_button("Add User")

            if submit:
                if u.strip() == "" or p.strip() == "":
                    st.error("Username and password required")
                else:
                    try:
                        cursor.execute("""
                        INSERT INTO users (username, password, role, department)
                        VALUES (?, ?, ?, ?)
                        """, (u.strip(), p, r, d))

                        conn.commit()
                        st.success("User added successfully")
                    except sqlite3.IntegrityError:
                        st.error("❌ Username already exists")

    # ----------------- VIEW USERS -----------------
    with tab2:
        df_users = pd.read_sql_query("SELECT id, username, role, department FROM users", conn)

        st.dataframe(df_users, use_container_width=True)

        st.download_button(
            "Download Users Excel",
            data=to_excel(df_users),
            file_name="users.xlsx"
        )