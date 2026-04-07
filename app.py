import streamlit as st
import pandas as pd
from datetime import datetime

# Load Excel data
@st.cache_data
def load_data():
    # Load the sheet - using the name you provided
    df = pd.read_excel("TDS_Master_Rate_Table_v2.xlsx", sheet_name="Master Rate Table")
    
    # FIX 1: Clean hidden spaces in text columns immediately
    df['Section'] = df['Section'].astype(str).str.strip()
    df['Payee Type'] = df['Payee Type'].astype(str).str.strip()
    
    # FIX 2: Ensure Date columns are actual datetime objects
    df['Effective From'] = pd.to_datetime(df['Effective From'], dayfirst=True)
    df['Effective To'] = pd.to_datetime(df['Effective To'], dayfirst=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading Excel: {e}. Check if file name and sheet name match.")
    st.stop()

st.title("🏛️ Automated TDS Calculation Portal")
st.markdown("---")

# 1. INPUT FORM
col1, col2 = st.columns(2)

with col1:
    section_list = sorted(df['Section'].unique())
    section = st.selectbox("Select TDS Section", options=section_list)
    amount = st.number_input("Gross Transaction Amount (INR)", min_value=0.0, step=500.0)
    pay_date = st.date_input("Date of Payment/Credit")

with col2:
    pan_status = st.radio("PAN Status of Payee", ["Available", "Not Available"])
    
    # Filter payee types available ONLY for the selected section to avoid errors
    available_payees = df[df['Section'] == section]['Payee Type'].unique()
    payee_type = st.selectbox("Payee Category", options=available_payees)

# 2. LOGIC ENGINE
if st.button("Calculate TDS Now"):
    # Convert input date to match dataframe format
    target_date = pd.to_datetime(pay_date)
    
    # Filter logic: Section + Payee Type + Date validity
    rule = df[
        (df['Section'] == section) & 
        (df['Payee Type'] == payee_type) &
        (df['Effective From'] <= target_date) & 
        (df['Effective To'] >= target_date)
    ]

    if not rule.empty:
        selected_rule = rule.iloc[0]
        threshold = float(selected_rule['Threshold Amount (Rs)'])
        base_rate = selected_rule['Rate of TDS (%)']
        
        # Amendment Check: If rate is 'Avg' (Salary), explain it
        if str(base_rate).strip() == "Avg":
            st.info(f"Section {section}: TDS is calculated based on average slab rates. {selected_rule['Notes']}")
        else:
            # Check PAN Penalty (Section 206AA logic)
            # Ensure base_rate is treated as a number
            final_rate = 20.0 if pan_status == "Not Available" else float(base_rate)
            
            # Threshold Comparison Logic
            if amount > threshold:
                tax = (amount * final_rate) / 100
                st.success(f"Deduct TDS: ₹{tax:,.2f}")
                st.metric("Final Rate Applied", f"{final_rate}%")
                st.caption(f"Nature: {selected_rule['Nature of Payment']}")
                st.caption(f"Legal Note: {selected_rule['Notes']}")
            else:
                st.warning(f"No TDS Required. Amount ₹{amount} is at or below the threshold of ₹{threshold}.")
    else:
        # Show a helpful error if nothing matches
        st.error("No matching rule found for this specific Section, Payee, and Date.")
        st.info(f"Check your Excel to see if there is a row for Section {section} valid on {pay_date}.")
