from flask import Flask, request, jsonify, make_response, render_template_string, session, redirect, url_for
from flask_mysqldb import MySQL
import jwt
import datetime
from functools import wraps
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import hashlib
import os

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = os.environ.get('SECRET_KEY', 'shoe-api-secret-key')
mysql = MySQL(app)

# === RESPONSE FORMATTER (JSON/XML) ===
def format_response(data, fmt='json'):
    if fmt.lower() == 'xml':
        root = Element('response')
        if isinstance(data, list):
            for item in data:
                elem = SubElement(root, 'shoe')
                for key, val in item.items():
                    SubElement(elem, key).text = str(val)
        else:
            for key, val in data.items():
                SubElement(root, key).text = str(val)
        rough = tostring(root, 'utf-8')
        reparsed = xml.dom.minidom.parseString(rough)
        xml_str = reparsed.toprettyxml(indent="  ")
        resp = make_response(xml_str)
        resp.headers['Content-Type'] = 'application/xml'
        return resp
    else:
        return jsonify(data)

# === JWT AUTH DECORATOR ===
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        elif 'token' in session:
            token = session['token']

        if not token:
            if request.args.get('format') in ['json', 'xml']:
                return format_response({'message': 'Token is missing!'}, request.args.get('format')), 401
            else:
                return redirect(url_for('login'))

        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            if request.args.get('format') in ['json', 'xml']:
                return format_response({'message': 'Token is invalid!'}, request.args.get('format')), 401
            else:
                session.pop('token', None)
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# === REGISTER (HTML + JSON) ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template_string('''
        <h2>Register</h2>
        <form method="POST">
            <p><input type="text" name="username" placeholder="Username" required></p>
            <p><input type="password" name="password" placeholder="Password" required></p>
            <p><button type="submit">Register</button></p>
            <a href="/login">Already have an account?</a>
        </form>
        ''')

    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return '<h3>Error: Username and password required</h3><a href="/register">Try again</a>', 400

    hashed = hashlib.sha256(password.encode()).hexdigest()
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        mysql.connection.commit()
        cur.close()
        return '<h3>Registered successfully!</h3><a href="/login">Login now</a>'
    except Exception as e:
        cur.close()
        if "Duplicate entry" in str(e):
            return '<h3>Username already exists</h3><a href="/register">Try again</a>', 400
        return '<h3>Registration failed</h3><a href="/register">Try again</a>', 500

# === LOGIN (HTML + JSON) ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            <p><input type="text" name="username" placeholder="Username" required></p>
            <p><input type="password" name="password" placeholder="Password" required></p>
            <p><button type="submit">Login</button></p>
            <a href="/register">Don't have an account?</a>
        </form>
        ''')

    username = request.form.get('username')
    password = request.form.get('password')
    hashed = hashlib.sha256(password.encode()).hexdigest()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed))
    user = cur.fetchone()
    cur.close()

    if not user:
        return '<h3>Invalid credentials</h3><a href="/login">Try again</a>', 401

    token = jwt.encode({
        'user': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    session['token'] = token
    return redirect(url_for('list_shoes'))

# === LOGOUT ===
@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('login'))

# === CREATE SHOE (HTML FORM) ===
@app.route('/shoes/new', methods=['GET', 'POST'])
@token_required
def create_shoe():
    if request.method == 'GET':
        return render_template_string('''
        <h2>Add New Shoe</h2>
        <form method="POST">
            <p><input name="brand" placeholder="Brand (e.g., Nike)" required></p>
            <p><input name="model" placeholder="Model (e.g., Air Max)" required></p>
            <p><input name="size" type="number" step="0.5" placeholder="Size (e.g., 9.0)" required></p>
            <p><input name="color" placeholder="Color" required></p>
            <p><input name="price" type="number" step="0.01" placeholder="Price (e.g., 150.00)" required></p>
            <p><input name="stock" type="number" placeholder="Stock (e.g., 25)" required></p>
            <p><button type="submit">Add Shoe</button></p>
            <a href="/shoes">Cancel</a>
        </form>
        ''')

    data = {
        'brand': request.form['brand'],
        'model': request.form['model'],
        'size': request.form['size'],
        'color': request.form['color'],
        'price': request.form['price'],
        'stock': request.form['stock']
    }

    try:
        size = float(data['size'])
        price = float(data['price'])
        stock = int(data['stock'])
        if price <= 0 or stock < 0:
            return '<h3>Error: Price > 0, Stock >= 0</h3><a href="/shoes/new">Try again</a>', 400
    except:
        return '<h3>Error: Invalid number format</h3><a href="/shoes/new">Try again</a>', 400

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO shoes (brand, model, size, color, price, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['brand'], data['model'], size, data['color'], price, stock))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_shoes'))
    except Exception as e:
        cur.close()
        return f'<h3>Error: {str(e)}</h3><a href="/shoes/new">Try again</a>', 400

# === READ ALL + SEARCH (with JSON/XML support) ===
@app.route('/shoes', methods=['GET'])
@token_required
def list_shoes():
    search = request.args.get('search', '')
    fmt = request.args.get('format', 'html')

    cur = mysql.connection.cursor()
    if search:
        cur.execute("SELECT * FROM shoes WHERE brand LIKE %s OR model LIKE %s OR color LIKE %s",
                    (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM shoes")
    rows = cur.fetchall()
    cur.close()

    shoes = []
    for row in rows:
        shoes.append({
            'id': row[0],
            'brand': row[1],
            'model': row[2],
            'size': float(row[3]),
            'color': row[4],
            'price': float(row[5]),
            'stock': row[6]
        })

    if fmt in ['json', 'xml']:
        return format_response(shoes, fmt)

    html = '''
    <h2>Shoe Inventory</h2>
    <p><a href="/shoes?format=json">JSON</a> | <a href="/shoes?format=xml">XML</a></p>
    <form method="GET">
        <input type="text" name="search" placeholder="Search by brand/model/color" value="{{search}}">
        <button type="submit">Search</button>
    </form>
    <p><a href="/shoes/new">Add New Shoe</a></p>
    <ul>
    {% for s in shoes %}
        <li>
            {{s.brand}} {{s.model}} (Size: {{s.size}}, {{s.color}}) - ₱{{s.price}}, Stock: {{s.stock}}
            | <a href="/shoes/{{s.id}}">View</a>
            | <a href="/shoes/{{s.id}}?format=json">JSON</a>
            | <a href="/shoes/{{s.id}}?format=xml">XML</a>
            | <a href="/shoes/{{s.id}}/edit">Edit</a>
            | <a href="/shoes/{{s.id}}/delete" onclick="return confirm('Delete?')">Delete</a>
        </li>
    {% endfor %}
    </ul>
    <p><a href="/">Home</a> | <a href="/logout">Logout</a></p>
    '''
    return render_template_string(html, shoes=shoes, search=search)

# === VIEW / UPDATE / DELETE ===
@app.route('/shoes/<int:id>', methods=['GET', 'POST', 'DELETE'])
@token_required
def shoe_detail(id):
    if request.method == 'POST' and 'delete' in request.form:
        request.method = 'DELETE'

    fmt = request.args.get('format', 'html')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM shoes WHERE id = %s", (id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        if fmt in ['json', 'xml']:
            return format_response({'error': 'Shoe not found'}, fmt), 404
        else:
            return '<h3>Shoe not found</h3><a href="/shoes">Back</a>', 404

    shoe = {
        'id': row[0],
        'brand': row[1],
        'model': row[2],
        'size': float(row[3]),
        'color': row[4],
        'price': float(row[5]),
        'stock': row[6]
    }

    if request.method == 'GET':
        if fmt in ['json', 'xml']:
            cur.close()
            return format_response(shoe, fmt)
        else:
            html = '''
            <h2>{{shoe.brand}} {{shoe.model}}</h2>
            <p><strong>Size:</strong> {{shoe.size}}</p>
            <p><strong>Color:</strong> {{shoe.color}}</p>
            <p><strong>Price:</strong> ₱{{shoe.price}}</p>
            <p><strong>Stock:</strong> {{shoe.stock}}</p>
            <p>
                <a href="/shoes/{{shoe.id}}/edit">Edit</a> |
                <form method="POST" style="display:inline" onsubmit="return confirm('Delete?')">
                    <input type="hidden" name="delete" value="1">
                    <button type="submit">Delete</button>
                </form> |
                <a href="/shoes">Back to list</a>
            </p>
            '''
            cur.close()
            return render_template_string(html, shoe=shoe)

    # Handle Update
    elif request.method == 'POST':
        if 'delete' not in request.form:
            data = {
                'brand': request.form['brand'],
                'model': request.form['model'],
                'size': request.form['size'],
                'color': request.form['color'],
                'price': request.form['price'],
                'stock': request.form['stock']
            }
            try:
                size = float(data['size'])
                price = float(data['price'])
                stock = int(data['stock'])
                if price <= 0 or stock < 0:
                    return '<h3>Error: Price > 0, Stock >= 0</h3><a href="/shoes/{{id}}/edit">Try again</a>', 400
            except:
                return '<h3>Error: Invalid number format</h3><a href="/shoes/{{id}}/edit">Try again</a>', 400

            cur.execute("""
                UPDATE shoes
                SET brand=%s, model=%s, size=%s, color=%s, price=%s, stock=%s
                WHERE id=%s
            """, (data['brand'], data['model'], size, data['color'], price, stock, id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('shoe_detail', id=id))

    # Handle DELETE
    if request.method == 'DELETE':
        cur.execute("DELETE FROM shoes WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        if fmt in ['json', 'xml']:
            return format_response({'message': 'Deleted'}, fmt)
        else:
            return redirect(url_for('list_shoes'))

# === EDIT FORM ===
@app.route('/shoes/<int:id>/edit', methods=['GET', 'POST'])
@token_required
def edit_shoe(id):
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM shoes WHERE id = %s", (id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return '<h3>Not found</h3><a href="/shoes">Back</a>', 404
        s = {
            'id': row[0],
            'brand': row[1],
            'model': row[2],
            'size': float(row[3]),
            'color': row[4],
            'price': float(row[5]),
            'stock': row[6]
        }
        html = '''
        <h2>Edit Shoe</h2>
        <form method="POST" action="/shoes/{{s.id}}">
            <p><input name="brand" value="{{s.brand}}" required></p>
            <p><input name="model" value="{{s.model}}" required></p>
            <p><input name="size" type="number" step="0.5" value="{{s.size}}" required></p>
            <p><input name="color" value="{{s.color}}" required></p>
            <p><input name="price" type="number" step="0.01" value="{{s.price}}" required></p>
            <p><input name="stock" type="number" value="{{s.stock}}" required></p>
            <p><button type="submit">Save Changes</button></p>
            <a href="/shoes/{{s.id}}">Cancel</a>
        </form>
        '''
        return render_template_string(html, s=s)

# === HOME ===
@app.route('/')
def index():
    if 'token' in session:
        return '<h2>Welcome to Shoe Inventory!</h2><p><a href="/shoes">Manage Shoes</a></p><p><a href="/logout">Logout</a></p>'
    else:
        return '<h2>Shoe Inventory System</h2><p><a href="/login">Login</a> or <a href="/register">Register</a></p>'

if __name__ == '__main__':
    app.run(debug=True)