import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database setup
DB_FILE = "car_selling.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            mileage INTEGER NOT NULL,
            condition TEXT NOT NULL,
            description TEXT,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

    # Insert sample data only if table is empty
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cars")
    if c.fetchone()[0] == 0:
        sample_cars = [
            ('Toyota', 'Camry', 2022, 25000, 30000, 'Excellent', 'Low mileage, one owner'),
            ('Honda', 'Civic', 2021, 22000, 45000, 'Good', 'Reliable and fuel efficient'),
            ('Ford', 'Mustang', 2020, 35000, 20000, 'Excellent', 'Sporty and powerful'),
        ]
        c.executemany('''
            INSERT INTO cars (make, model, year, price, mileage, condition, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_cars)
        conn.commit()
    conn.close()

# Initialize database on app start
init_db()

def get_cars():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, make, model, year, price, mileage, condition, description, added_on FROM cars ORDER BY added_on DESC", conn)
    conn.close()
    df['added_on'] = pd.to_datetime(df['added_on'])
    return df

def add_car(make, model, year, price, mileage, condition, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO cars (make, model, year, price, mileage, condition, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (make, model, year, price, mileage, condition, description))
    conn.commit()
    conn.close()

def update_car(car_id, make, model, year, price, mileage, condition, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE cars
        SET make = ?, model = ?, year = ?, price = ?, mileage = ?, condition = ?, description = ?
        WHERE id = ?
    ''', (make, model, year, price, mileage, condition, description, car_id))
    conn.commit()
    conn.close()

def delete_car(car_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()

# App title
st.title("🚗 Car Selling System")
st.markdown("A persistent car selling platform using SQLite as the database.")

# Load cars
cars = get_cars()

# Sidebar navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Browse Cars", "Search Cars", "Admin: Add Car", "Admin: Manage Cars"])

if page == "Browse Cars":
    st.header("Available Cars for Sale")
    if cars.empty:
        st.info("No cars listed yet.")
    else:
        cols = st.columns(3)
        for idx, row in cars.iterrows():
            with cols[idx % 3]:
                st.image("https://via.placeholder.com/300x200?text=Car+Image", caption=f"{row['make']} {row['model']}")
                st.subheader(f"{row['year']} {row['make']} {row['model']}")
                st.write(f"**Price:** ${row['price']:,.0f}")
                st.write(f"**Mileage:** {row['mileage']:,} km")
                st.write(f"**Condition:** {row['condition']}")
                st.write(row['description'])
                st.caption(f"Listed on: {row['added_on'].date()}")

elif page == "Search Cars":
    st.header("Search Cars")
    search_make = st.text_input("Search by Make (e.g., Toyota)", "")
    min_price = st.slider("Minimum Price ($)", 0, 100000, 0)
    max_price = st.slider("Maximum Price ($)", min_price, 100000, 100000)

    filtered = cars[
        (cars['make'].str.contains(search_make, case=False, na=False) | (search_make == "")) &
        (cars['price'] >= min_price) &
        (cars['price'] <= max_price)
    ]

    if filtered.empty:
        st.info("No cars match your search criteria.")
    else:
        # Hide internal columns
        display_df = filtered[['make', 'model', 'year', 'price', 'mileage', 'condition', 'description', 'added_on']].copy()
        display_df.rename(columns={'added_on': 'Listed On'}, inplace=True)
        st.dataframe(display_df, use_container_width=True)

elif page == "Admin: Add Car":
    st.header("Add New Car Listing")
    with st.form("add_car_form"):
        make = st.text_input("Make *")
        model = st.text_input("Model *")
        year = st.number_input("Year", min_value=1900, max_value=datetime.now().year + 1, step=1)
        price = st.number_input("Price ($)", min_value=0.0, step=1000.0)
        mileage = st.number_input("Mileage (km)", min_value=0, step=1000)
        condition = st.selectbox("Condition", ["New", "Excellent", "Good", "Fair", "Poor"])
        description = st.text_area("Description")

        submitted = st.form_submit_button("Add Car")
        if submitted:
            if make.strip() and model.strip():
                add_car(make.strip(), model.strip(), int(year), price, mileage, condition, description)
                st.success(f"{make} {model} added successfully!")
                st.rerun()
            else:
                st.error("Make and Model are required.")

elif page == "Admin: Manage Cars":
    st.header("Manage Car Listings")
    if cars.empty:
        st.info("No cars to manage.")
    else:
        # Create a readable label for selection
        cars['display'] = cars.apply(lambda row: f"{row['make']} {row['model']} ({row['year']}) - ID: {row['id']}", axis=1)
        car_to_edit = st.selectbox("Select Car to Edit/Delete", cars['id'].tolist(), format_func=lambda x: cars[cars['id']==x]['display'].values[0])

        selected_row = cars[cars['id'] == car_to_edit].iloc[0]

        with st.form("edit_car_form"):
            make = st.text_input("Make", value=selected_row['make'])
            model = st.text_input("Model", value=selected_row['model'])
            year = st.number_input("Year", min_value=1900, max_value=datetime.now().year + 1, value=int(selected_row['year']))
            price = st.number_input("Price ($)", min_value=0.0, value=float(selected_row['price']), step=1000.0)
            mileage = st.number_input("Mileage (km)", min_value=0, value=int(selected_row['mileage']), step=1000)
            condition = st.selectbox("Condition", ["New", "Excellent", "Good", "Fair", "Poor"],
                                     index=["New", "Excellent", "Good", "Fair", "Poor"].index(selected_row['condition']))
            description = st.text_area("Description", value=selected_row['description'] or "")

            col1, col2 = st.columns(2)
            update_btn = col1.form_submit_button("Update Car")
            delete_btn = col2.form_submit_button("Delete Car")

            if update_btn:
                update_car(car_to_edit, make, model, year, price, mileage, condition, description)
                st.success("Car updated successfully!")
                st.rerun()

            if delete_btn:
                if st.button("Confirm Delete? This cannot be undone."):
                    delete_car(car_to_edit)
                    st.success("Car deleted successfully!")
                    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💾 Data is now persistently stored in `car_selling.db` (SQLite). Changes survive app restarts and deployments.")