import streamlit as st
import pandas as pd
import os
from datetime import datetime
from rapidfuzz import process

# ---------- Setup ----------
st.set_page_config(page_title="Stock Transfer Tracker", page_icon="🚚", layout="wide")
st.title("Stock Transfer Tracker")

# Ensure data folder exists
data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

# File paths
stock_on_hand_file = os.path.join(data_folder, "book1.xlsx")
catalogue_file = os.path.join(data_folder, "CATALOGUE.xlsx")
transfers_file = os.path.join(data_folder, "stock_transfers.xlsx")

# Load location list
def load_locations():
    df = pd.read_excel(stock_on_hand_file)
    if "Bin Location Description" not in df.columns:
        st.error("'Bin Location Description' column not found in book1.xlsx.")
        st.stop()
    locations = sorted(df["Bin Location Description"].dropna().unique().tolist())
    return locations

# Load parts list
def load_parts():
    df = pd.read_excel(catalogue_file)
    if "Item Code" not in df.columns or "ItemName" not in df.columns:
        st.error("'ItemCode' or 'ItemName' column not found in CATALOGUE.xlsx.")
        st.stop()
    df["Combined"] = df["ItemCode"] + " - " + df["ItemName"]
    return df

locations_list = load_locations()
parts_df = load_parts()
all_parts = parts_df["Combined"].tolist()

# ---------- Session State ----------
if "transfer_rows" not in st.session_state:
    st.session_state.transfer_rows = []

# ---------- Functions ----------
def add_row(prev_from=None, prev_to=None):
    new_row = {
        "item_selected": "",
        "quantity": 1,
        "from_location": prev_from if prev_from else locations_list[0],
        "to_location": prev_to if prev_to else locations_list[0],
    }
    st.session_state.transfer_rows.append(new_row)

def clear_rows():
    st.session_state.transfer_rows = []

def save_transfers(rows):
    if not rows:
        return

    records = []
    for row in rows:
        # Split item_selected back into Item Code and Item Name
        selected_text = row["item_selected"]
        if " - " in selected_text:
            item_code, item_name = selected_text.split(" - ", 1)
        else:
            item_code, item_name = selected_text, ""
        
        records.append({
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Item No": item_code,
            "Item Description": item_name,
            "Quantity": row["quantity"],
            "From Location": row["from_location"],
            "To Location": row["to_location"],
        })

    new_df = pd.DataFrame(records)

    if os.path.exists(transfers_file):
        existing_df = pd.read_excel(transfers_file)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    combined_df.to_excel(transfers_file, index=False)

# ---------- App Interface ----------

st.markdown("### Fill Stock Transfers:")

# Display transfer rows
for idx, row in enumerate(st.session_state.transfer_rows):
    st.markdown(f"**Transfer {idx+1}**")
    cols = st.columns([4, 1, 3, 3])

    with cols[0]:
        selection = st.selectbox(
            f"Item", options=all_parts, index=all_parts.index(row["item_selected"]) if row["item_selected"] in all_parts else 0, key=f"item_{idx}",
        )
        st.session_state.transfer_rows[idx]["item_selected"] = selection

    with cols[1]:
        quantity = st.number_input(f"Qty", min_value=1, value=row["quantity"], key=f"qty_{idx}")
        st.session_state.transfer_rows[idx]["quantity"] = quantity

    with cols[2]:
        from_loc = st.selectbox(
            f"From", options=locations_list, index=locations_list.index(row["from_location"]) if row["from_location"] in locations_list else 0, key=f"from_{idx}",
        )
        st.session_state.transfer_rows[idx]["from_location"] = from_loc

    with cols[3]:
        to_loc = st.selectbox(
            f"To", options=locations_list, index=locations_list.index(row["to_location"]) if row["to_location"] in locations_list else 0, key=f"to_{idx}",
        )
        st.session_state.transfer_rows[idx]["to_location"] = to_loc

st.markdown("---")

# Buttons
col1, col2, col3 = st.columns([1,1,2])

with col1:
    if st.button("➕ Add Row"):
        prev_from = st.session_state.transfer_rows[-1]["from_location"] if st.session_state.transfer_rows else None
        prev_to = st.session_state.transfer_rows[-1]["to_location"] if st.session_state.transfer_rows else None
        add_row(prev_from, prev_to)

with col2:
    if st.button("✅ Submit"):
        save_transfers(st.session_state.transfer_rows)
        clear_rows()
        st.success("Transfers submitted successfully!")

# Display last 10 transfers
if os.path.exists(transfers_file):
    st.markdown("### Last 10 Transfers:")
    df = pd.read_excel(transfers_file)
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("No transfers have been submitted yet.")

# Add initial row if empty
if not st.session_state.transfer_rows:
    add_row()
