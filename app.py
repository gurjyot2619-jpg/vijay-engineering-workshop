from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st

# Setup SQLite Database
conn = sqlite3.connect("vijay_engineering.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS daily_jobs (
    job_id TEXT PRIMARY KEY,
    date TEXT,
    customer_name TEXT,
    vehicle_number TEXT,
    phone_number TEXT,
    job_description TEXT,
    total_bill REAL,
    amount_paid REAL,
    due_amount REAL,
    payment_status TEXT,
    bill_timestamp TEXT
)
"""
)
conn.commit()

st.title("🔧 Vijay Engineering Company, Bhopal")
st.subheader("Daily Workshop & Dues Management System")

# --- DIRECTORS' DIGEST SIDEBAR SECTION ---
st.sidebar.markdown("---")
st.sidebar.subheader("👑 Directors' Digest")
st.sidebar.caption("For: 9827053347 & 9893053349")

if st.sidebar.button("Generate Director's Report"):
  pending_df = pd.read_sql(
      "SELECT customer_name, vehicle_number, phone_number, due_amount,"
      " bill_timestamp FROM daily_jobs WHERE due_amount > 0",
      conn,
  )

  if pending_df.empty:
    st.sidebar.success("No pending dues! All accounts are fully cleared.")
  else:
    total_dues = pending_df["due_amount"].sum()
    report_text = (
        "📊 *Vijay Engineering Company - Pending Dues Digest*\n\n"
    )

    for _, row in pending_df.iterrows():
      report_text += (
          f"• *{row['customer_name']}* ({row['vehicle_number']}):"
          f" ₹{row['due_amount']} (Ph: {row['phone_number']})\n"
      )

    report_text += f"\n*Total Outstanding Market Dues: ₹{total_dues:,.2f}*"

    st.sidebar.markdown("---")
    st.sidebar.write("**Report ready for forwarding:**")
    st.sidebar.code(report_text)

# Navigation Menu
menu = [
    "Add New Entry",
    "Operational Summary & Dues",
    "Payment Reminders & Receipts",
]
choice = st.sidebar.selectbox("Navigation", menu)

# --- 1. ADD NEW ENTRY FORM ---
if choice == "Add New Entry":
  st.header("📝 Register New Workshop Job")

  with st.form("entry_form", clear_on_submit=True):
    customer_name = st.text_input("Customer Name")
    vehicle_number = st.text_input("Vehicle Number (e.g., MP04 AB 1234)")
    phone_number = st.text_input(
        "Phone Number (e.g., +91 98260 11111)", value="+91 "
    )
    job_description = st.text_area("Job Description / Service Details")
    total_bill = st.number_input("Total Bill Amount (₹)", min_value=0.0, step=100.0)
    amount_paid = st.number_input(
        "Amount Paid Now (₹)", min_value=0.0, step=100.0
    )

    submit_button = st.form_submit_button(label="Save Entry")

    if submit_button:
      if customer_name and vehicle_number:
        job_id = f"JOB-{int(datetime.now().timestamp())}"
        date = datetime.now().strftime("%Y-%m-%d")
        due_amount = total_bill - amount_paid

        if due_amount == 0:
          payment_status = "Paid"
        elif amount_paid > 0:
          payment_status = "Pending"
        else:
          payment_status = "Overdue"

        bill_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO daily_jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_id,
                date,
                customer_name,
                vehicle_number,
                phone_number,
                job_description,
                total_bill,
                amount_paid,
                due_amount,
                payment_status,
                bill_timestamp,
            ),
        )
        conn.commit()
        st.success(f"Entry successfully saved for {customer_name}!")

        # Show instant WhatsApp-ready receipt message if fully paid
        if due_amount == 0:
          st.success("🎉 Bill fully cleared! Ready-to-send WhatsApp message:")
          st.code(
              f"Dear {customer_name}, we have received your full payment of"
              f" ₹{total_bill} for vehicle {vehicle_number}. Thank you for"
              " visiting Vijay Engineering Company, Bhopal! We appreciate your"
              " trust in our service. Please visit again! 🚗🔧"
          )
      else:
        st.error(
            "Please fill in at least the Customer Name and Vehicle Number."
        )

# --- 2. OPERATIONAL SUMMARY ---
elif choice == "Operational Summary & Dues":
  st.header("📊 Daily Turnover & Pending Dues")

  df_jobs = pd.read_sql("SELECT * FROM daily_jobs", conn)

  if df_jobs.empty:
    st.info("No workshop entries recorded yet.")
  else:
    total_entries = len(df_jobs)
    total_incurred = df_jobs["total_bill"].sum()
    total_collected = df_jobs["amount_paid"].sum()
    total_dues = df_jobs["due_amount"].sum()

    col1, col2 = st.metric(
        label="Total Entries", value=total_entries
    ), st.metric(label="Total Bill Incurred", value=f"₹{total_incurred:,.2f}")
    col3, col4 = st.metric(
        label="Total Collected", value=f"₹{total_collected:,.2f}"
    ), st.metric(label="Total Pending Dues", value=f"₹{total_dues:,.2f}")

    st.markdown("---")
    st.subheader("All Job Records")
    st.dataframe(df_jobs)

# --- 3. REMINDERS & RECEIPTS ---
elif choice == "Payment Reminders & Receipts":
  st.header("🔔 Customer Receipts & Payment Follow-ups")

  df_jobs = pd.read_sql("SELECT * FROM daily_jobs", conn)

  if df_jobs.empty:
    st.info("No workshop entries recorded yet.")
  else:
    st.subheader("✅ Paid Invoices (Thank You Notes)")
    paid_df = df_jobs[df_jobs["due_amount"] == 0]
    if paid_df.empty:
      st.write("No fully paid entries to show right now.")
    else:
      for index, row in paid_df.iterrows():
        st.success(f"**{row['customer_name']}** ({row['vehicle_number']})")
        st.code(
            f"Dear {row['customer_name']}, thank you for clearing your balance"
            f" of ₹{row['total_bill']} for vehicle {row['vehicle_number']}. It"
            " was a pleasure servicing your vehicle at Vijay Engineering"
            " Company, Bhopal. Thanks for visiting us, please visit again!"
            " Drive safe! 🚗🔧"
        )

    st.markdown("---")
    st.subheader("⏳ Pending Dues & Overdue Reminders")
    pending_df = df_jobs[df_jobs["due_amount"] > 0]
    if pending_df.empty:
      st.success("Awesome! No pending dues or overdue accounts right now.")
    else:
      now = datetime.now()
      for index, row in pending_df.iterrows():
        bill_time = datetime.strptime(row["bill_timestamp"], "%Y-%m-%d %H:%M:%S")
        hours_passed = (now - bill_time).total_seconds() / 3600

        if hours_passed <= 48:
          st.info(
              f"**Standard Reminder (Under 48h) for {row['customer_name']}**"
              f" (`{row['phone_number']}`)"
          )
          st.code(
              f"Hello {row['customer_name']}, this is a reminder from Vijay"
              f" Engineering Company regarding vehicle {row['vehicle_number']}."
              f" There is an outstanding balance of ₹{row['due_amount']}"
              " remaining on your account. Please arrange to clear this at your"
              " earliest convenience. Thank you."
          )
        else:
          st.error(
              f"**🚨 ESCALATED NOTICE & OWNER ALERT (> 48h) for"
              f" {row['customer_name']}** (`{row['phone_number']}`)"
          )
          st.code(
              f"Dear {row['customer_name']}, your account for vehicle"
              f" {row['vehicle_number']} reflects an overdue balance of"
              f" ₹{row['due_amount']} which has crossed the 48-hour payment"
              " window. Please remit the total outstanding amount immediately"
              " to avoid disruption of future workshop services."
          )
          st.warning(
              f"OWNER ACTION REQUIRED: Unpaid for {int(hours_passed)} hours."
              f" Amount due: ₹{row['due_amount']}."
          )