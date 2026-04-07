import streamlit as st
import pandas as pd
from datetime import datetime

# Load Excel data from your GitHub repository
@st.cache_data
def load_data():
    return pd.read_excel("TDS_Master_Rate_Table_v2.xlsx", sheet_name="Master Rate Table")

df = load_data()

st.title("🏛️ Automated TDS Calculation Portal")
st.markdown("---")

# 1. INPUT FORM
col1, col2 = st.columns(2)

with col1:
    section = st.selectbox("Select TDS Section", options=sorted(df['Section'].unique()))
    amount = st.number_input("Gross Transaction Amount (INR)", min_value=0.0, step=500.0)
    pay_date = st.date_input("Date of Payment/Credit")

with col2:
    pan_status = st.radio("PAN Status of Payee", ["Available", "Not Available"])
    # We add this because some sections (194A, 194N) depend on the Payee Category
    payee_type = st.selectbox("Payee Category", options=df['Payee Type'].unique())

# 2. LOGIC ENGINE
if st.button("Calculate TDS Now"):
    # Convert dates to match Excel format
    target_date = pd.to_datetime(pay_date)
    
    # Filter logic: Section + Payee Type + Date validity
    rule = df[
        (df['Section'] == section) & 
        (df['Payee Type'] == payee_type) &
        (pd.to_datetime(df['Effective From']) <= target_date) & 
        (pd.to_datetime(df['Effective To']) >= target_date)
    ]

    if not rule.empty:
        selected_rule = rule.iloc[0]
        threshold = selected_rule['Threshold Amount (Rs)']
        base_rate = selected_rule['Rate of TDS (%)']
        
        # Amendment Check: If rate is 'Avg' (Salary), explain it
        if base_rate == "Avg":
            st.info("Section 192 (Salary): TDS is calculated based on average slab rates for the employee.")
        else:
            # Check PAN Penalty (Section 206AA logic)
            final_rate = 20.0 if pan_status == "Not Available" else float(base_rate)
            
            # Threshold Comparison Logic
            if amount > threshold:
                tax = (amount * final_rate) / 100
                st.success(f"Deduct TDS: ₹{tax:,.2f}")
                st.metric("Final Rate Applied", f"{final_rate}%")
                st.caption(f"Note: {selected_rule['Notes']}")
            else:
                st.warning(f"No TDS Required. Amount is below the threshold of ₹{threshold}.")
    else:
        st.error("No matching rule found. Check if the Payee Category matches the Section.")
