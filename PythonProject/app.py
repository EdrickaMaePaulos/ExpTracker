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
    location = request.args.get('location')
    category = request.args.get('category')
    name = request.args.get('name')

    query = "SELECT *, DATEDIFF(expiration_date, CURDATE()) AS days_remaining FROM items"
    filters = []
    params = []

    if location:
        filters.append("location = %s")
        params.append(location)
    if category:
        filters.append("category = %s")
        params.append(category)
    if name:
        filters.append("name LIKE %s")
        params.append(f"%{name}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    cur = mysql.connection.cursor()
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT location FROM items")
    locations = cur.fetchall()

    cur.execute("SELECT DISTINCT category FROM items")
    categories = cur.fetchall()
    cur.close()

    return render_template('index.html', items=items, locations=locations, categories=categories, location=location,
                           category=category, name=name)



@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        category = request.form.get('category')
        manufacturedDate = request.form.get('manufacturedDate')
        expiration_date = request.form.get('expiration_date')
        notes = request.form.get('notes')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO items (name,location, category,manufacturedDate, expiration_date, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, location, category, manufacturedDate, expiration_date, notes))
        mysql.connection.commit()
        cur.close()

        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_item.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        category = request.form['category']
        manufacturedDate = request.form['manufacturedDate']
        expiration_date = request.form['expiration_date']
        notes = request.form['notes']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE items SET name = %s,location = %s, category = %s,manufacturedDate = %s, expiration_date = %s, notes = %s WHERE id = %s",
                    (name, location, category, manufacturedDate, expiration_date, notes, id))
        mysql.connection.commit()
        cur.close()

        flash('Item updated successfully', 'success')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM items WHERE id = %s", [id])
    item = cur.fetchone()
    cur.close()

    return render_template('edit_item.html', item=item)


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
