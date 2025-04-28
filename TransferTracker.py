import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

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

# Define local timezone
local_timezone = pytz.timezone('Australia/Sydney')

# ---------- Functions ----------

def load_locations():
    if not os.path.exists(stock_on_hand_file):
        st.error(f"Stock on hand file '{stock_on_hand_file}' not found.")
        st.stop()
    df = pd.read_excel(stock_on_hand_file)
    if "Bin Location Description" not in df.columns:
        st.error("'Bin Location Description' column not found in book1.xlsx.")
        st.stop()
    locations = sorted(df["Bin Location Description"].dropna().unique().tolist())
    return locations

def load_parts():
    if not os.path.exists(catalogue_file):
        st.error(f"Catalogue file '{catalogue_file}' not found.")
        st.stop()
    df = pd.read_excel(catalogue_file)
    if "ItemCode" not in df.columns or "ItemName" not in df.columns:
        st.error("'ItemCode' or 'ItemName' column not found in CATALOGUE.xlsx.")
        st.stop()
    df["Combined"] = df["ItemCode"].astype(str) + " - " + df["ItemName"].astype(str)
    return df

def add_row(prev_from=None, prev_to=None):
    new_row = {
        "item_selected": "",
        "quantity": 0,  # Start at 0
        "from_location": prev_from if prev_from else locations_list[0],
        "to_location": prev_to if prev_to else locations_list[0],
    }
    st.session_state.transfer_rows.append(new_row)

def delete_row(idx):
    if 0 <= idx < len(st.session_state.transfer_rows):
        st.session_state.transfer_rows.pop(idx)

def save_transfers(rows):
    if not rows:
        return

    now = datetime.now(local_timezone)

    records = []
    for row in rows:
        selected_text = row["item_selected"]
        quantity = row["quantity"]

        # Only save rows where item is selected and quantity > 0
        if selected_text and quantity > 0:
            if " - " in selected_text:
                item_code, item_name = selected_text.split(" - ", 1)
            else:
                item_code, item_name = selected_text, ""

            records.append({
                "Date": now.strftime("%Y-%m-%d"),
                "Time": now.strftime("%H:%M:%S"),
                "Item No": item_code,
                "Item Description": item_name,
                "Quantity": quantity,
                "From Location": row["from_location"],
                "To Location": row["to_location"],
            })

    if not records:
        st.warning("⚠️ No valid transfers to save.")
        return

    new_df = pd.DataFrame(records)

    if os.path.exists(transfers_file):
        existing_df = pd.read_excel(transfers_file)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    combined_df.to_excel(transfers_file, index=False)

def last_row_has_item_selected():
    if not st.session_state.transfer_rows:
        return False
    last_row = st.session_state.transfer_rows[-1]
    return last_row["item_selected"] != ""

# ---------- Load Data ----------

locations_list = load_locations()
parts_df = load_parts()
all_parts = parts_df["Combined"].tolist()

# ---------- Session State ----------
if "transfer_rows" not in st.session_state:
    st.session_state.transfer_rows = []

# Add first row if empty
if len(st.session_state.transfer_rows) == 0:
    add_row()

# ---------- App Interface ----------

st.markdown("### Fill Stock Transfers:")

rows_to_delete = []

# Display transfer rows
for idx, row in enumerate(st.session_state.transfer_rows):
    st.markdown(f"**Transfer {idx+1}**")

    cols = st.columns([3, 3, 4, 1])  # To | From | Item | Qty

    with cols[0]:
        to_loc = st.selectbox(
            "To", options=locations_list,
            index=locations_list.index(row["to_location"]) if row["to_location"] in locations_list else 0,
            key=f"to_{idx}",
        )
        st.session_state.transfer_rows[idx]["to_location"] = to_loc

    with cols[1]:
        from_loc = st.selectbox(
            "From", options=locations_list,
            index=locations_list.index(row["from_location"]) if row["from_location"] in locations_list else 0,
            key=f"from_{idx}",
        )
        st.session_state.transfer_rows[idx]["from_location"] = from_loc

    with cols[2]:
        selection = st.selectbox(
            "Item", options=[""] + all_parts,
            index=(all_parts.index(row["item_selected"]) + 1) if row["item_selected"] in all_parts else 0,
            key=f"item_{idx}",
        )
        st.session_state.transfer_rows[idx]["item_selected"] = selection

    with cols[3]:
        quantity = st.number_input(
            "Qty", min_value=0, value=row["quantity"], key=f"qty_{idx}"
        )
        st.session_state.transfer_rows[idx]["quantity"] = quantity

    if st.button(f"❌ Delete Transfer {idx+1}", key=f"delete_{idx}"):
        rows_to_delete.append(idx)

# Handle deletion
for idx in sorted(rows_to_delete, reverse=True):
    delete_row(idx)

st.markdown("---")

# Check if last row has an item selected, then auto add new blank row
if last_row_has_item_selected():
    last_row = st.session_state.transfer_rows[-1]
    add_row(prev_from=last_row["from_location"], prev_to=last_row["to_location"])

# Submit button
if st.button("✅ Submit Transfers"):
    save_transfers(st.session_state.transfer_rows)
    st.session_state.transfer_rows = []
    add_row()
    st.success("Transfers submitted successfully!")

# ---------- Display Past Transfers ----------
if os.path.exists(transfers_file):
    st.markdown("### Last 10 Transfers:")
    df = pd.read_excel(transfers_file)
    st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("No transfers have been submitted yet.")
