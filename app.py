# 1. UPDATED INPUT FORM
with col1:
    section_list = sorted(df['Section'].unique())
    section = st.selectbox("Select TDS Section", options=section_list)
    amount = st.number_input("Gross Transaction Amount (INR)", min_value=0.0, step=500.0)
    pay_date = st.date_input("Date of Payment/Credit")

with col2:
    pan_status = st.radio("PAN Status of Payee", ["Available", "Not Available"])
    
    # FIX: This now pulls EVERY Payee Type you have in your Excel 
    # (Individual/HUF, Company, Firm/LLP, etc.)
    available_payees = sorted(df[df['Section'] == section]['Payee Type'].unique())
    payee_type = st.selectbox("Payee Category", options=available_payees)

# 2. UPDATED LOGIC ENGINE (Future-Aware)
if st.button("Calculate TDS Now"):
    target_date = pd.to_datetime(pay_date)
    
    # Filter by Section and Payee Type
    potential_rules = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
    
    # Match the date: Look for a row where date fits, 
    # OR if date is in the future, pick the most recent rule available.
    rule = potential_rules[
        (potential_rules['Effective From'] <= target_date) & 
        (potential_rules['Effective To'] >= target_date)
    ]
    
    # If no rule found for a future date, grab the latest one
    if rule.empty and not potential_rules.empty:
        rule = potential_rules.sort_values(by='Effective From', ascending=False).head(1)
        st.caption("✨ Using latest available rate for future-dated transaction.")

    if not rule.empty:
        selected_rule = rule.iloc[0]
        threshold = float(selected_rule['Threshold Amount (Rs)'])
        base_rate = selected_rule['Rate of TDS (%)']
        
        # Salary/Avg check
        if str(base_rate).strip() == "Avg":
            st.info(f"Section {section}: Average slab rates apply. {selected_rule['Notes']}")
        else:
            # PAN Penalty Logic
            final_rate = 20.0 if pan_status == "Not Available" else float(base_rate)
            
            if amount > threshold:
                tax = (amount * final_rate) / 100
                st.success(f"Deduct TDS: ₹{tax:,.2f}")
                st.metric("Applied Rate", f"{final_rate}%")
            else:
                st.warning(f"Below threshold of ₹{threshold}. No TDS.")
    else:
        st.error("No matching rule found. Check if this Section + Payee combo exists in Excel.")
