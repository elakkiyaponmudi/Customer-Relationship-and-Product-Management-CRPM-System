import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
import plotly.express as px

class CRPMSystem:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                CustomerID INT AUTO_INCREMENT PRIMARY KEY,
                FirstName VARCHAR(50) NOT NULL,
                LastName VARCHAR(50) NOT NULL,
                Email VARCHAR(100) UNIQUE NOT NULL,
                PhoneNumber VARCHAR(20) NOT NULL,
                Address VARCHAR(255),
                City VARCHAR(50),
                State VARCHAR(50),
                PostalCode VARCHAR(20),
                Country VARCHAR(50),
                DateOfBirth DATE,
                RegistrationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Status VARCHAR(20) DEFAULT 'Active'
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                ProductID INT AUTO_INCREMENT PRIMARY KEY,
                ProductName VARCHAR(100) NOT NULL,
                CategoryID INT,
                SupplierID INT,
                QuantityPerUnit VARCHAR(50),
                UnitPrice DECIMAL(10,2),
                UnitsInStock INT,
                UnitsOnOrder INT,
                ReorderLevel INT,
                Discontinued TINYINT(1) DEFAULT 0,
                Description TEXT,
                ImageURL VARCHAR(255),
                Weight DECIMAL(10,2),
                Dimensions VARCHAR(50),
                DateAdded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                LastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                PurchaseID INT AUTO_INCREMENT PRIMARY KEY,
                CustomerID INT NOT NULL,
                ProductID INT NOT NULL,
                Quantity INT NOT NULL,
                PurchaseDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID),
                FOREIGN KEY (ProductID) REFERENCES products(ProductID)
            );
        ''')

        self.conn.commit()

    def add_customer(self, first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth):
        try:
            self.cursor.execute('''
                INSERT INTO customers (FirstName, LastName, Email, PhoneNumber, Address, City, State, PostalCode, Country, DateOfBirth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth))
            self.conn.commit()
        except mysql.connector.IntegrityError:
            raise ValueError("Email already exists.")

    def get_customers(self):
        self.cursor.execute('SELECT * FROM customers WHERE Status = "Active"')
        return self.cursor.fetchall()

    def update_customer(self, customer_id, first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth):
        self.cursor.execute('''
            UPDATE customers
            SET FirstName = %s, LastName = %s, Email = %s, PhoneNumber = %s, Address = %s, City = %s, State = %s, PostalCode = %s, Country = %s, DateOfBirth = %s
            WHERE CustomerID = %s
        ''', (first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth, customer_id))
        self.conn.commit()

    def deactivate_customer(self, customer_id):
        self.cursor.execute('UPDATE customers SET Status = "Inactive" WHERE CustomerID = %s', (customer_id,))
        self.conn.commit()

    def add_product(self, name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions):
        self.cursor.execute('''
            INSERT INTO products (ProductName, CategoryID, SupplierID, QuantityPerUnit, UnitPrice, UnitsInStock, UnitsOnOrder, ReorderLevel, Discontinued, Description, ImageURL, Weight, Dimensions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions))
        self.conn.commit()

    def get_products(self):
        self.cursor.execute('SELECT * FROM products')
        return self.cursor.fetchall()

    def update_product(self, product_id, name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions):
        self.cursor.execute('''
            UPDATE products
            SET ProductName = %s, CategoryID = %s, SupplierID = %s, QuantityPerUnit = %s, UnitPrice = %s, UnitsInStock = %s, UnitsOnOrder = %s, ReorderLevel = %s, Discontinued = %s, Description = %s, ImageURL = %s, Weight = %s, Dimensions = %s
            WHERE ProductID = %s
        ''', (name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions, product_id))
        self.conn.commit()

    def deactivate_product(self, product_id):
        self.cursor.execute('UPDATE products SET Discontinued = 1 WHERE ProductID = %s', (product_id,))
        self.conn.commit()

    def record_purchase(self, customer_id, product_id, quantity):
        self.cursor.execute('''
            INSERT INTO purchases (CustomerID, ProductID, Quantity)
            VALUES (%s, %s, %s)
        ''', (customer_id, product_id, quantity))
        self.cursor.execute('UPDATE products SET UnitsInStock = UnitsInStock - %s WHERE ProductID = %s', (quantity, product_id))
        self.conn.commit()

    def get_purchase_history(self, customer_id):
        self.cursor.execute('''
            SELECT p.ProductID, p.ProductName, pr.Quantity, pr.PurchaseDate
            FROM purchases pr
            JOIN products p ON pr.ProductID = p.ProductID
            WHERE pr.CustomerID = %s
        ''', (customer_id,))
        return self.cursor.fetchall()

    def generate_sales_report(self):
        self.cursor.execute('''
            SELECT SUM(pr.Quantity * p.UnitPrice) as total_revenue, COUNT(pr.PurchaseID) as total_sales
            FROM purchases pr
            JOIN products p ON pr.ProductID = p.ProductID
        ''')
        return self.cursor.fetchone()

    def get_top_customers(self):
        self.cursor.execute('''
            SELECT c.CustomerID, c.FirstName, c.LastName, SUM(pr.Quantity * p.UnitPrice) as total_spent
            FROM purchases pr
            JOIN customers c ON pr.CustomerID = c.CustomerID
            JOIN products p ON pr.ProductID = p.ProductID
            GROUP BY c.CustomerID
            ORDER BY total_spent DESC
            LIMIT 10
        ''')
        return self.cursor.fetchall()

    def get_product_performance(self):
        self.cursor.execute('''
            SELECT p.ProductID, p.ProductName, SUM(pr.Quantity) as total_sold
            FROM purchases pr
            JOIN products p ON pr.ProductID = p.ProductID
            GROUP BY p.ProductID
            ORDER BY total_sold DESC
        ''')
        return self.cursor.fetchall()

# Initialize the CRPM system
crpm_system = CRPMSystem(host='localhost', user='root', password='#ponmudi22', database='crpm')

st.title("Customer Relationship and Product Management System")

# Sidebar for navigation
menu = ["Customer Management", "Product Management", "Purchases", "Analytics"]
choice = st.sidebar.selectbox("Menu", menu)

# Customer Management
if choice == "Customer Management":
    st.subheader("Customer Management")
    action = st.selectbox("Select Action", ["Add Customer", "View Customers", "Update Customer", "Deactivate Customer"])

    if action == "Add Customer":
        st.subheader("Add Customer")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone_number = st.text_input("Phone Number")
        address = st.text_area("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        postal_code = st.text_input("Postal Code")
        country = st.text_input("Country")
        date_of_birth = st.date_input("Date of Birth")
        if st.button("Add Customer"):
            try:
                crpm_system.add_customer(first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth)
                st.success("Customer added successfully!")
            except ValueError as e:
                st.error(f"Error: {str(e)}")

    elif action == "View Customers":
        st.subheader("View Customers")
        customers = crpm_system.get_customers()
        if customers:
            st.table(customers)
        else:
            st.info("No active customers found.")

    elif action == "Update Customer":
        st.subheader("Update Customer")
        customer_id = st.number_input("Customer ID", min_value=1)
        if st.button("Load Customer Data"):
            customer_data = crpm_system.get_customers()
            customer = next((c for c in customer_data if c[0] == customer_id), None)
            if customer:
                first_name = st.text_input("First Name", customer[1])
                last_name = st.text_input("Last Name", customer[2])
                email = st.text_input("Email", customer[3])
                phone_number = st.text_input("Phone Number", customer[4])
                address = st.text_area("Address", customer[5])
                city = st.text_input("City", customer[6])
                state = st.text_input("State", customer[7])
                postal_code = st.text_input("Postal Code", customer[8])
                country = st.text_input("Country", customer[9])
                date_of_birth = st.date_input("Date of Birth", customer[10])
                if st.button("Update Customer"):
                    crpm_system.update_customer(customer_id, first_name, last_name, email, phone_number, address, city, state, postal_code, country, date_of_birth)
                    st.success("Customer updated successfully!")

    elif action == "Deactivate Customer":
        st.subheader("Deactivate Customer")
        customer_id = st.number_input("Customer ID", min_value=1)
        if st.button("Deactivate Customer"):
            crpm_system.deactivate_customer(customer_id)
            st.success("Customer deactivated successfully!")

# Product Management
elif choice == "Product Management":
    st.subheader("Product Management")
    action = st.selectbox("Select Action", ["Add Product", "View Products", "Update Product", "Deactivate Product"])

    if action == "Add Product":
        st.subheader("Add Product")
        name = st.text_input("Product Name")
        category_id = st.number_input("Category ID", min_value=1)
        supplier_id = st.number_input("Supplier ID", min_value=1)
        quantity_per_unit = st.text_input("Quantity Per Unit")
        unit_price = st.number_input("Unit Price", min_value=0.0)
        units_in_stock = st.number_input("Units in Stock", min_value=0)
        units_on_order = st.number_input("Units on Order", min_value=0)
        reorder_level = st.number_input("Reorder Level", min_value=0)
        discontinued = st.checkbox("Discontinued")
        description = st.text_area("Description")
        image_url = st.text_input("Image URL")
        weight = st.number_input("Weight (in grams)")
        dimensions = st.text_input("Dimensions")
        if st.button("Add Product"):
            crpm_system.add_product(name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions)
            st.success("Product added successfully!")

    elif action == "View Products":
        st.subheader("View Products")
        products = crpm_system.get_products()
        if products:
            st.table(products)
        else:
            st.info("No products found.")

    elif action == "Update Product":
        st.subheader("Update Product")
        product_id = st.number_input("Product ID", min_value=1)
        if st.button("Load Product Data"):
            product_data = crpm_system.get_products()
            product = next((p for p in product_data if p[0] == product_id), None)
            if product:
                name = st.text_input("Product Name", product[1])
                category_id = st.number_input("Category ID", min_value=1, value=product[2])
                supplier_id = st.number_input("Supplier ID", min_value=1, value=product[3])
                quantity_per_unit = st.text_input("Quantity Per Unit", product[4])
                unit_price = st.number_input("Unit Price", min_value=0.0, value=product[5])
                units_in_stock = st.number_input("Units in Stock", min_value=0, value=product[6])
                units_on_order = st.number_input("Units on Order", min_value=0, value=product[7])
                reorder_level = st.number_input("Reorder Level", min_value=0, value=product[8])
                discontinued = st.checkbox("Discontinued", value=product[9])
                description = st.text_area("Description", product[10])
                image_url = st.text_input("Image URL", product[11])
                weight = st.number_input("Weight (in grams)", value=product[12])
                dimensions = st.text_input("Dimensions", product[13])
                if st.button("Update Product"):
                    crpm_system.update_product(product_id, name, category_id, supplier_id, quantity_per_unit, unit_price, units_in_stock, units_on_order, reorder_level, discontinued, description, image_url, weight, dimensions)
                    st.success("Product updated successfully!")

    elif action == "Deactivate Product":
        st.subheader("Deactivate Product")
        product_id = st.number_input("Product ID", min_value=1)
        if st.button("Deactivate Product"):
            crpm_system.deactivate_product(product_id)
            st.success("Product deactivated successfully!")

# Purchases
elif choice == "Purchases":
    st.subheader("Purchases")
    action = st.selectbox("Select Action", ["Record Purchase", "View Purchase History"])

    if action == "Record Purchase":
        st.subheader("Record Purchase")
        customer_id = st.number_input("Customer ID", min_value=1)
        product_id = st.number_input("Product ID", min_value=1)
        quantity = st.number_input("Quantity", min_value=1)
        if st.button("Record Purchase"):
            crpm_system.record_purchase(customer_id, product_id, quantity)
            st.success("Purchase recorded successfully!")

    elif action == "View Purchase History":
        st.subheader("View Purchase History")
        customer_id = st.number_input("Customer ID", min_value=1)
        if st.button("View Purchase History"):
            history = crpm_system.get_purchase_history(customer_id)
            if history:
                st.table(history)
            else:
                st.info("No purchase history found for this customer.")

# Analytics
elif choice == "Analytics":
    st.subheader("Analytics")
    action = st.selectbox("Select Action", ["Sales Report", "Top Customers", "Product Performance"])

    if action == "Sales Report":
        st.subheader("Sales Report")
        report = crpm_system.generate_sales_report()
        st.write(f"Total Revenue: {report[0]}")
        st.write(f"Total Sales: {report[1]}")

    elif action == "Top Customers":
        st.subheader("Top Customers")
        top_customers = crpm_system.get_top_customers()
        if top_customers:
            st.table(top_customers)
        else:
            st.info("No top customers found.")

    elif action == "Product Performance":
        st.subheader("Product Performance")
        performance = crpm_system.get_product_performance()
        if performance:
            product_data = [{"Product Name": p[1], "Total Sold": p[2]} for p in performance]
            df = pd.DataFrame(product_data)
            fig = px.bar(df, x="Product Name", y="Total Sold", title="Total Products Sold")
            st.plotly_chart(fig)
        else:
            st.info("No product performance data found.")
