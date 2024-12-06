import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
import bcrypt  # For secure password hashing
import plotly.graph_objects as go

# File paths for local storage
USER_DATA_FILE = "user_data.json"
TRANSACTION_LOG_FILE = "transaction_logs.json"

# Helper Functions for Local Storage
def load_json(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump({}, file)
    with open(file_path, "r") as file:
        return json.load(file)

def save_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

# Load local data
user_data = load_json(USER_DATA_FILE)
transaction_logs = load_json(TRANSACTION_LOG_FILE)

# Password Hashing Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_password, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_password.encode('utf-8'))

# Function to log transactions
def store_transaction_data(user_id, data):
    try:
        # Analyze the transactions to calculate total balance, incoming, and outgoing
        total_balance, incoming, outgoing = analyze_transactions(data)

        # Log transaction data locally
        if user_id not in transaction_logs:
            transaction_logs[user_id] = []

        transaction_logs[user_id].append({
            "transactions": data.to_dict(orient="records"),  # Store transaction data
            "total_balance": total_balance,  # Calculated total balance
            "total_credit": incoming,  # Total credits
            "total_debit": outgoing,  # Total debits
            "timestamp": datetime.now().isoformat()  # Log timestamp
        })

        save_json(TRANSACTION_LOG_FILE, transaction_logs)

        st.success(f"Transaction logged successfully!")
        st.success(f"Total Balance: {total_balance}.")
        st.success(f"Total Debit: {outgoing}.")
        st.success(f"Total Credit: {incoming}.")
    except Exception as e:
        st.error(f"Error storing transaction data: {e}")

# Function to analyze transactions
def analyze_transactions(data):
    if 'DrCr' in data.columns and 'balance' in data.columns:
        incoming = data[data['DrCr'] == 'Cr']['balance'].sum()
        outgoing = data[data['DrCr'] == 'Db']['balance'].sum()
        total_balance = data['balance'].iloc[-1]
        return total_balance, incoming, outgoing
    else:
        raise ValueError("Dataset must contain 'DrCr' and 'balance' columns.")

# User Profile Page
def user_profile_page(user_id, user_data, transaction_logs):
    st.title("User Profile")

    # Retrieve user information
    user_info = user_data.get(user_id, {})
    user_activities = transaction_logs.get(user_id, [{}])[-1]  # Get the latest transaction log

    # Extract required details
    name = user_info.get("name", "Unknown")
    email = user_info.get("email", "Unknown")
    total_balance = user_activities.get("total_balance", 0)
    total_credit = user_activities.get("total_credit", 0)
    total_debit = user_activities.get("total_debit", 0)

    # Display the information
    st.markdown(f"## Welcome, {name}!")
    st.markdown(f"### User ID: {user_id}")
    st.markdown(f"### Email: {email}")
    st.markdown(f"### Total Balance: {total_balance}")

    # Display Donut Chart for Total Credit and Debit
    fig = go.Figure(data=[go.Pie(
        labels=["Total Credit", "Total Debit"],
        values=[total_credit, total_debit],
        hole=0.4,  # Create a donut chart
        hoverinfo="label+percent",
        textinfo="value+percent",
        marker=dict(colors=["#28a745", "#dc3545"])  # Green for Credit, Red for Debit
    )])

    fig.update_layout(
        title="Debit vs Credit Distribution",
        annotations=[dict(text="Debit vs Credit", x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"### Total Debit: {total_debit}")
    st.markdown(f"### Total Credit: {total_credit}")

# Recommendations Page
def recommendations_page(user_id, transaction_logs):
    st.title("Recommendations")

    # Retrieve transaction logs for user
    user_transactions = transaction_logs.get(user_id, [])
    
    if not user_transactions:
        st.warning("No transaction data available for recommendations.")
        return
    
    # Example recommendation logic: Suggest saving based on debits
    latest_transaction = user_transactions[-1]
    total_balance = latest_transaction.get("total_balance", 0)
    total_debit = latest_transaction.get("total_debit", 0)

    if total_debit > total_balance * 0.5:
        st.markdown("### Recommendation: You are spending more than half of your balance. Consider budgeting your expenses.")
    else:
        st.markdown("### Recommendation: Your spending is under control! Keep up the good work.")
    
    # More personalized recommendations could be added here based on transaction data

# Data Analytics Page
def data_analytics_page(user_id):
    st.title("Smart Finance Dashboard")
    st.markdown("Visualize your financial data with appealing charts.")

    uploaded_file = st.file_uploader("Upload CSV or PDF File", type=["csv", "pdf"])
    if uploaded_file is not None:
        with st.spinner("Loading data..."):
            data = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else None
        if data is not None:
            st.success("Data loaded successfully!")
            st.write("### Uploaded Data Preview")
            st.dataframe(data)

            # Store and analyze transaction data
            store_transaction_data(user_id, data)

            # Visualization options
            st.sidebar.header("Visualization Options")
            chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Pie Chart"])
            numeric_columns = data.select_dtypes(include=["float", "int"]).columns.tolist()

            if numeric_columns:
                x_axis = st.sidebar.selectbox("X-Axis", options=numeric_columns)
                y_axis = st.sidebar.selectbox("Y-Axis", options=numeric_columns)

                if chart_type == "Bar Chart":
                    fig = px.bar(data, x=x_axis, y=y_axis)
                elif chart_type == "Line Chart":
                    fig = px.line(data, x=x_axis, y=y_axis)
                elif chart_type == "Pie Chart":
                    category = st.sidebar.selectbox("Category Column", options=data.columns)
                    fig = px.pie(data, names=category, values=y_axis)

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No numeric columns found for visualization.")
        else:
            st.error("Error loading file. Please check the format.")

# Authentication and Main Application
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Login", "Sign Up", "Profile", "Recommendations", "Data Analytics"])

    if page == "Sign Up":
        st.title("Sign Up")
        user_id = st.text_input("Enter a unique User ID")
        name = st.text_input("Enter your Name")
        email = st.text_input("Enter your Email")
        password = st.text_input("Enter a Password", type="password")
        if st.button("Register"):
            if user_id in user_data:
                st.error("User ID already exists.")
            else:
                hashed_password = hash_password(password)
                user_data[user_id] = {"name": name, "email": email, "password": hashed_password}
                save_json(USER_DATA_FILE, user_data)
                st.success("User registered successfully!")

    elif page == "Login":
        st.title("Login")
        user_id = st.text_input("Enter your User ID")
        password = st.text_input("Enter your Password", type="password")
        if st.button("Login"):
            if user_id in user_data and verify_password(user_data[user_id]["password"], password):
                st.success(f"Welcome back, {user_data[user_id]['name']}!")
                st.session_state["user_id"] = user_id
            else:
                st.error("Invalid User ID or Password.")

    elif page == "Profile":
        user_id = st.session_state.get("user_id")
        if user_id:
            user_profile_page(user_id, user_data, transaction_logs)
        else:
            st.warning("Please log in to view your profile.")

    elif page == "Recommendations":
        user_id = st.session_state.get("user_id")
        if user_id:
            recommendations_page(user_id, transaction_logs)
        else:
            st.warning("Please log in to view recommendations.")

    elif page == "Data Analytics":
        user_id = st.session_state.get("user_id")
        if user_id:
            data_analytics_page(user_id)
        else:
            st.warning("Please log in to access the dashboard.")

if __name__ == "__main__":
    main()
