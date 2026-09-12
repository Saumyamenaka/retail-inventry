import streamlit as st
import pandas as pd
import urllib.parse
import json
import os

st.set_page_config(page_title="Retail Inventory Engine", layout="wide")

USER_DB_FILE = "users_db.json"
STOCK_DB_FILE = "stock_db.json"

def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "master_inventory" not in st.session_state:
    st.session_state.master_inventory = {}

# ----------------- AUTHENTICATION SYSTEM -----------------
if not st.session_state.authenticated:
    st.title("🔐 Retail Engine - Portal Access")
    
    auth_mode = st.radio("Choose Access Mode", ["Login", "Register New Shop Account", "🔑 System Admin Login"])
    users = load_data(USER_DB_FILE)
    
    if auth_mode == "Register New Shop Account":
        st.subheader("📝 Register Your Shop Account")
        with st.form("registration_form"):
            shop_name = st.text_input("Shop Name")
            owner_name = st.text_input("Owner Full Name")
            email = st.text_input("Email Address")
            phone = st.text_input("WhatsApp Phone Number")
            username = st.text_input("Choose Username")
            password = st.text_input("Choose Password", type="password")
            
            submit_reg = st.form_submit_button("🚀 Register Account")
            if submit_reg:
                if not (shop_name and owner_name and email and phone and username and password):
                    st.error("⚠️ Please fill in ALL fields completely!")
                elif username in users:
                    st.error("⚠️ Username already exists!")
                else:
                    users[username] = {
                        "shop_name": shop_name,
                        "owner_name": owner_name,
                        "email": email,
                        "phone": phone,
                        "password": password,
                        "uploaded_dates": []
                    }
                    save_data(users, USER_DB_FILE)
                    st.success("🎉 Registration Successful! Switch to 'Login' above.")

    elif auth_mode == "Login":
        st.subheader("🔑 Login to Your Shop Dashboard")
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("🔓 Login")
            
            if submit_login:
                if login_user in users and users[login_user]["password"] == login_pass:
                    st.session_state.authenticated = True
                    st.session_state.user_info = users[login_user]
                    st.session_state.is_admin = False
                    
                    stock_db = load_data(STOCK_DB_FILE)
                    u_email = users[login_user]['email']
                    if u_email in stock_db:
                        st.session_state.master_inventory[u_email] = stock_db[u_email]
                        
                    st.success("✅ Login Successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password!")

    elif auth_mode == "🔑 System Admin Login":
        st.subheader("🛡️ System Owner/Admin Access")
        with st.form("admin_login_form"):
            admin_user = st.text_input("Admin Username")
            admin_pass = st.text_input("Admin Password", type="password")
            submit_admin = st.form_submit_button("🔓 Access Master Dashboard")
            
            if submit_admin:
                if admin_user == "admin" and admin_pass == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.is_admin = True
                    st.session_state.user_info = {"shop_name": "System Control Center", "owner_name": "System Admin"}
                    st.success("✅ Admin Access Granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Admin Credentials!")

# ----------------- SYSTEM ADMIN DASHBOARD -----------------
elif st.session_state.is_admin:
    st.title("🛡️ System Admin Master Control")
    col_a1, col_a2 = st.columns([4, 1])
    with col_a1:
        st.caption("Overview of all registered shop owners and active client stores.")
    with col_a2:
        if st.button("🚪 Logout Admin"):
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.rerun()
            
    st.divider()
    
    users = load_data(USER_DB_FILE)
    stocks = load_data(STOCK_DB_FILE)
    
    if not users:
        st.info("ℹ️ No shop owners registered yet.")
    else:
        st.subheader("👥 Registered Shop Owners Directory")
        user_list = []
        for uname, udata in users.items():
            u_email = udata.get("email", "")
            u_stock = stocks.get(u_email, [])
            total_items = sum(item.get("Stock_Qty", 0) for item in u_stock)
            
            user_list.append({
                "Username": uname,
                "Shop Name": udata.get("shop_name"),
                "Owner Name": udata.get("owner_name"),
                "Email": u_email,
                "Phone": udata.get("phone"),
                "Total Stock Items": total_items
            })
            
        admin_df = pd.DataFrame(user_list)
        st.dataframe(admin_df, use_container_width=True)
        
        csv_data = admin_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Registered Owners (CSV)",
            data=csv_data,
            file_name="Registered_Shop_Owners.csv",
            mime="text/csv"
        )

# ----------------- NORMAL SHOP DASHBOARD -----------------
else:
    user = st.session_state.user_info
    user_key = user['email']
    
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.title(f"🛍️ {user['shop_name']} - Inventory Intelligence")
        st.caption(f"Welcome, **{user['owner_name']}** | Email: {user['email']} | Phone: {user['phone']}")
    with col_h2:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
            
    st.divider()

    if user_key in st.session_state.master_inventory:
        master_df = pd.DataFrame(st.session_state.master_inventory[user_key])
    else:
        stock_db = load_data(STOCK_DB_FILE)
        if user_key in stock_db:
            st.session_state.master_inventory[user_key] = stock_db[user_key]
            master_df = pd.DataFrame(stock_db[user_key])
        else:
            master_df = None

    if master_df is not None and not master_df.empty:
        total_units = int(master_df['Stock_Qty'].sum())
        total_val = int((master_df['Stock_Qty'] * master_df['Price_LKR']).sum())
        dead_df = master_df[master_df['Days_In_Rack'] > 30]
        dead_units = int(dead_df['Stock_Qty'].sum())
        recoverable_val = int((dead_df['Stock_Qty'] * dead_df['Price_LKR'] * 0.8).sum())
        
        st.subheader("📊 Executive Performance Dashboard")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Total Stock Units", f"{total_units:,}")
        m2.metric("💎 Total Stock Valuation", f"LKR {total_val:,}")
        m3.metric("🚨 Current Dead Stock Units", f"{dead_units:,}")
        m4.metric("💰 Recoverable Cash", f"LKR {recoverable_val:,}")
        
        summary_csv = master_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Monthly Inventory & Performance Summary (CSV)",
            data=summary_csv,
            file_name=f"{user['shop_name']}_Monthly_Summary.csv",
            mime="text/csv"
        )
        st.divider()

    tab1, tab2, tab3 = st.tabs(["📦 Baseline Stock Setup", "🛒 Daily Sales & Cash Recovery", "🚚 Restock & Live Inventory Editor"])

    # TAB 1: MASTER SETUP
    with tab1:
        st.header("1. Upload Initial Master Stock Count")
        master_file = st.file_uploader("Upload Initial Inventory (Excel/CSV)", type=["csv", "xlsx"])
        if master_file is not None:
            df = pd.read_csv(master_file) if master_file.name.endswith('.csv') else pd.read_excel(master_file)
            if 'Size' not in df.columns: df['Size'] = 'Free Size'
            if 'Category' not in df.columns: df['Category'] = 'General'
            if 'Days_In_Rack' not in df.columns: df['Days_In_Rack'] = 0
            if 'Min_Limit' not in df.columns: df['Min_Limit'] = 5
            
            data_records = df.to_dict(orient="records")
            st.session_state.master_inventory[user_key] = data_records
            
            stock_db = load_data(STOCK_DB_FILE)
            stock_db[user_key] = data_records
            save_data(stock_db, STOCK_DB_FILE)
            
            st.success("✅ Baseline Successfully Saved!")
            st.dataframe(df, use_container_width=True)
            st.rerun()
        elif master_df is not None:
            st.info("📊 Current Active Baseline:")
            st.dataframe(master_df, use_container_width=True)

    # TAB 2: DAILY SALES & DEAD STOCK
    with tab2:
        st.header("2. Daily Sales Deductor & Intelligence")
        if master_df is None or master_df.empty:
            st.warning("⚠️ Upload Baseline in Tab 1 first!")
        else:
            sales_date = st.date_input("Select Sales Date for this Upload")
            sales_file = st.file_uploader("Upload Daily Sales File", type=["csv", "xlsx"], key="daily_sales")
            current_df = master_df.copy()
            
            if sales_file is not None:
                users_data = load_data(USER_DB_FILE)
                target_uname = None
                for un, ud in users_data.items():
                    if ud.get("email") == user_key:
                        target_uname = un
                        break
                
                if target_uname:
                    if "uploaded_dates" not in users_data[target_uname]:
                        users_data[target_uname]["uploaded_dates"] = []
                    
                    date_str = str(sales_date)
                    if date_str in users_data[target_uname]["uploaded_dates"]:
                        st.error(f"🛑 DUPLICATE UPLOAD BLOCKED! Sales for date **{date_str}** have already been processed and deducted!")
                    else:
                        sales_df = pd.read_csv(sales_file) if sales_file.name.endswith('.csv') else pd.read_excel(sales_file)
                        if 'Size' not in sales_df.columns: sales_df['Size'] = 'Free Size'
                        
                        for _, sale in sales_df.iterrows():
                            mask = (current_df['Item_Name'] == sale['Item_Name']) & (current_df['Size'] == sale['Size'])
                            if mask.any():
                                current_df.loc[mask, 'Stock_Qty'] -= sale['Sold_Qty']
                                current_df.loc[current_df['Stock_Qty'] < 0, 'Stock_Qty'] = 0
                        
                        sold_skus = list(zip(sales_df['Item_Name'], sales_df['Size']))
                        for idx, row in current_df.iterrows():
                            if (row['Item_Name'], row['Size']) not in sold_skus:
                                current_df.loc[idx, 'Days_In_Rack'] += 1
                                
                        updated_records = current_df.to_dict(orient="records")
                        st.session_state.master_inventory[user_key] = updated_records
                        
                        stock_db = load_data(STOCK_DB_FILE)
                        stock_db[user_key] = updated_records
                        save_data(stock_db, STOCK_DB_FILE)
                        
                        users_data[target_uname]["uploaded_dates"].append(date_str)
                        save_data(users_data, USER_DB_FILE)
                        
                        st.success(f"✅ Sales for {date_str} Successfully Deducted & Database Updated!")
                        st.rerun()

            dead_stock = current_df[current_df['Days_In_Rack'] > 30].copy()
            dead_stock['Discount_Price'] = (dead_stock['Price_LKR'] * 0.8).astype(int)
            
            st.divider()
            st.subheader("🎯 Size-Targeted WhatsApp Clearance Offers")
            
            if not dead_stock.empty:
                select_all_dead = st.checkbox("☑️ Select All Dead Stock Items for Bulk WhatsApp Broadcast")
                bulk_items_text = f"🌸 SPECIAL CLEARANCE SALE at {user['shop_name']}! Check items below:\n"
                
                for idx, row in dead_stock.iterrows():
                    if row['Stock_Qty'] > 0:
                        with st.expander(f"⚠️ {row['Item_Name']} - [Size: {row['Size']}] ({row['Stock_Qty']} units | Stuck: {row['Days_In_Rack']} days)"):
                            st.write(f"**Original Price:** LKR {row['Price_LKR']:,} | **Offer Price:** LKR {row['Discount_Price']:,}")
                            offer_text = f"🌸 CLEARANCE OFFER! {user['shop_name']} offers {row['Item_Name']} (Size: {row['Size']}) for LKR {row['Discount_Price']:,}! Reply YES to reserve."
                            encoded = urllib.parse.quote(offer_text)
                            st.markdown(f"[📲 Launch Individual WhatsApp Offer](https://wa.me/?text={encoded})", unsafe_allow_html=True)
                        
                        if select_all_dead:
                            bulk_items_text += f"- {row['Item_Name']} ({row['Size']}) Now LKR {row['Discount_Price']:,}\n"
                
                if select_all_dead:
                    encoded_bulk = urllib.parse.quote(bulk_items_text)
                    st.markdown(f"### 🚀 [Click Here to Send Bulk WhatsApp Broadcast for All Selected Items](https://wa.me/?text={encoded_bulk})")

    # TAB 3: RESTOCK & LIVE INVENTORY EDITOR
    with tab3:
        st.header("3. Smart Restock, Alerts & Live Inventory Editor")
        if master_df is not None and not master_df.empty:
            if 'Min_Limit' not in master_df.columns:
                master_df['Min_Limit'] = 5
                
            # --- LIVE EDITING TABLE ---
            st.subheader("✏️ Live Inventory Editor (Click any cell to edit Stock, Min Limit, or Prices directly)")
            edited_df = st.data_editor(master_df, num_rows="dynamic", use_container_width=True, key="live_stock_editor")
            
            if st.button("💾 Save Live Changes"):
                updated_records = edited_df.to_dict(orient="records")
                st.session_state.master_inventory[user_key] = updated_records
                
                stock_db = load_data(STOCK_DB_FILE)
                stock_db[user_key] = updated_records
                save_data(stock_db, STOCK_DB_FILE)
                
                st.success("🎉 Inventory changes saved successfully!")
                st.rerun()
                
            st.divider()
            
            # Alerts based on edited live data
            low_stock_df = edited_df[(edited_df['Stock_Qty'] > 0) & (edited_df['Stock_Qty'] <= edited_df['Min_Limit'])]
            out_of_stock = edited_df[edited_df['Stock_Qty'] == 0]
            
            if not out_of_stock.empty:
                st.error("🚨 CRITICAL: The following items are completely OUT OF STOCK!")
                st.table(out_of_stock[['Category', 'Item_Name', 'Size', 'Stock_Qty', 'Price_LKR']])
                
                out_text = f"🚨 URGENT RESTOCK ALERT for {user['shop_name']}! Items completely sold out. Please check dashboard."
                encoded_out = urllib.parse.quote(out_text)
                st.markdown(f"[📲 Send Out-of-Stock Alert via WhatsApp](https://wa.me/{user['phone']}?text={encoded_out})", unsafe_allow_html=True)
            
            if not low_stock_df.empty:
                st.warning("⚠️ LOW STOCK WARNING: The following items have dropped to or below their customized Minimum Limit:")
                st.table(low_stock_df[['Category', 'Item_Name', 'Size', 'Stock_Qty', 'Min_Limit', 'Price_LKR']])
                
                low_text = f"⚠️ LOW STOCK WARNING at {user['shop_name']}! {len(low_stock_df)} items have hit their customized minimum limits. Time to restock!"
                encoded_low = urllib.parse.quote(low_text)
                st.markdown(f"[📲 Send Low-Stock Warning via WhatsApp](https://wa.me/{user['phone']}?text={encoded_low})", unsafe_allow_html=True)
            
            if out_of_stock.empty and low_stock_df.empty:
                st.success("✅ All stock levels are healthy and above their specific threshold limits!")
