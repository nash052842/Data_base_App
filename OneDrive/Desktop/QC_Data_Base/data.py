import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="QC Database",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- DATABASE CONNECTION ----------
conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()
# ---------- CREATE TABLE ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER,
    date TEXT,
    product TEXT,
    Market TEXT,
    counts INTEGER DEFAULT 0,
    benchmark INTEGER DEFAULT 0,
    customer_name TEXT,
    remarks TEXT
)
""")
conn.commit()

# ---------- TITLE ----------
st.title("📊 QC Database App")

# ---------- INPUT FORM ----------
st.subheader("Enter Record Details")

date_value = st.date_input("Date")

# Automatically calculate week number
week = date_value.isocalendar().week

st.info(f"📅 Week Number: {week}")

product = st.text_input("Product")
market = st.text_input("Market")
customer_name = st.text_input("Customer Name")
counts = st.number_input(
    "Counts",
    min_value=0,
    step=1,
    value=0
)

benchmark = st.number_input(
    "Benchmark",
    min_value=0,
    step=1,
    value=0
)
remarks = st.text_area("Remarks")   

# ---------- SAVE DATA ----------
if st.button("💾 Save to Database"):

    if not product.strip():
        st.error("Please enter a product name.")
    else:
        try:
            with conn:
                cursor.execute("""
                    INSERT INTO users
                    (
                        week,
                        date,
                        product,
                        Market,
                        counts,
                        benchmark,
                        customer_name,
                        remarks
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(week),
                    str(date_value),
                    product.strip(),
                    market.strip(),
                    int(counts),
                    int(benchmark),
                    customer_name.strip(),
                    remarks.strip()
                ))

            # Update Excel automatically
            export_df = pd.read_sql_query(
                "SELECT * FROM users ORDER BY id DESC",
                conn
            )

            export_df.to_excel(
                "QC_Database.xlsx",
                index=False
            )

            st.success("✅ Record saved successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error saving data: {e}")

# ---------- DISPLAY DATA ----------
st.subheader("📁 Stored Records")

try:
    df = pd.read_sql_query("""
        SELECT
            id,
            week,
            date,
            product,
            Market,
            counts,
            benchmark,
            customer_name,
            remarks
        FROM users
        ORDER BY id DESC
    """, conn)

    with st.expander("📁 View Stored Records", expanded=False):

        week_options = ["All"] + sorted(
            df["week"].dropna().unique().tolist()
        )

        week_filter = st.selectbox(
            "Filter by Week",
            week_options
        )

        filtered_df = df.copy()

        if week_filter != "All":
            filtered_df = filtered_df[
                filtered_df["week"] == week_filter
            ]

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

        st.write(
            f"**Records Found:** {len(filtered_df)}"
        )

    # ---------- DOWNLOAD EXCEL ----------
    if not df.empty:

        try:
            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:
                df.to_excel(
                    writer,
                    index=False,
                    sheet_name="QC_Data"
                )

            st.download_button(
                label="📥 Download Excel File",
                data=excel_buffer.getvalue(),
                file_name="QC_Database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except ImportError:
            st.warning(
                "openpyxl is not installed. "
                "Install it using: pip install openpyxl"
            )

            csv = df.to_csv(index=False)

            st.download_button(
                label="📥 Download CSV File",
                data=csv,
                file_name="QC_Database.csv",
                mime="text/csv"
            )

except Exception as e:
    st.error(f"Error loading data: {e}")

