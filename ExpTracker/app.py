from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'expiration_tracker')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')


@app.route('/')
def index():
    query_notifications = """
        SELECT i.name, s.name AS storage, 
               DATEDIFF(i.expiration_date, CURDATE()) AS days_remaining
        FROM items i \
        LEFT JOIN Storage s ON i.storageID = s.storageID
        WHERE i.expiration_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        ORDER BY i.expiration_date ASC
    """
    cur = mysql.connection.cursor()
    cur.execute(query_notifications)
    notifications = cur.fetchall()

    query_storages = "SELECT storageID, name FROM Storage ORDER BY name ASC"
    cur.execute(query_storages)
    storages = cur.fetchall()
    storage_id = request.args.get('storageID')
    items_in_storage = []
    if storage_id:
        query_items_in_storage = """
            SELECT i.*, s.name AS storage, c.name AS category,
                   DATEDIFF(i.expiration_date, CURDATE()) AS days_remaining
            FROM items i
            LEFT JOIN Storage s ON i.storageID = s.storageID
            LEFT JOIN Category c ON i.categoryID = c.categoryID
            WHERE i.storageID = %s
            ORDER BY i.expiration_date ASC
        """
        cur.execute(query_items_in_storage, (storage_id,))
        items_in_storage = cur.fetchall()

    cur.close()

    return render_template('index.html',
                           notifications=notifications,
                           storages=storages,
                           items_in_storage=items_in_storage)

#ITEM LIST
@app.route('/list')
def item_list():
    query = """SELECT i.*, s.name AS storage, c.name AS category,
               DATEDIFF(i.expiration_date, CURDATE()) AS days_remaining
               FROM items i
               LEFT JOIN Storage s ON i.storageID = s.storageID
               LEFT JOIN Category c ON i.categoryID = c.categoryID
               ORDER BY i.expiration_date ASC"""
    cur = mysql.connection.cursor()
    cur.execute(query)
    items = cur.fetchall()
    cur.close()

    return render_template('list.html', items=items)

# ADD ITEM
@app.route('/addItem', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        storageID = request.form.get('storageID')
        categoryID = request.form.get('categoryID')
        manufactured_date = request.form.get('manufactured_date')
        expiration_date = request.form.get('expiration_date')
        notes = request.form.get('notes')

        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO items (name, storageID, categoryID, manufactured_date, expiration_date, notes)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (name, storageID, categoryID, manufactured_date, expiration_date, notes))
        mysql.connection.commit()
        cur.close()

        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Storage")
    storages = cur.fetchall()

    cur.execute("SELECT * FROM Category")
    categories = cur.fetchall()
    cur.close()

    return render_template('add_item.html', storages=storages, categories=categories)


# Add Storage
@app.route('/addStorage', methods=['GET', 'POST'])
def add_storage():
    if request.method == 'POST':
        storage_name = request.form.get('storage')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Storage (name) VALUES (%s)", [storage_name])
        mysql.connection.commit()
        cur.close()

        flash('Storage added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_storage.html')


# Add Category
@app.route('/addCategory', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category_name = request.form.get('category')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Category (name) VALUES (%s)", [category_name])
        mysql.connection.commit()
        cur.close()

        flash('Category added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_category.html')


# Edit Item
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if request.method == 'POST':
        name = request.form.get('name')
        storage_id = request.form.get('storageID')
        category_id = request.form.get('categoryID')
        manufactured_date = request.form.get('manufactured_date')
        expiration_date = request.form.get('expiration_date')
        notes = request.form.get('notes')

        if not name or not storage_id or not category_id:
            flash("All fields are required.", "danger")
            return redirect(f'/edit/{item_id}')

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE items 
                SET name = %s, storageID = %s, categoryID = %s, 
                    manufactured_date = %s, expiration_date = %s, notes = %s
                WHERE id = %s
            """, (name, storage_id, category_id, manufactured_date, expiration_date, notes, item_id))
            mysql.connection.commit()
            cur.close()

            flash("Item updated successfully!", "success")
            return redirect('/')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(f'/edit/{item_id}')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cur.fetchone()
    cur.execute("SELECT * FROM Storage")
    storages = cur.fetchall()
    cur.execute("SELECT * FROM Category")
    categories = cur.fetchall()
    cur.close()

    return render_template('edit_item.html', item=item, storages=storages, categories=categories)

# Delete Item
@app.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM items WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()

    flash('Item deleted successfully', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
