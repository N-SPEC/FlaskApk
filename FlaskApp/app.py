from flask_sqlalchemy  import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'dinuchakedi'  # Change this!   
app.config['SECRET_KEY'] = "dinuchakedi"

# sqlite config
# app.config['SQLALCHEMY_DATABASE_URI'] = 'localhost:5432'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/flaskpostgre'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# Bind the instance to the 'app.py' Flask application
db = SQLAlchemy(app)

class area(db.Model):
    __tablename__ = 'area' 
    area_id = db.Column(db.Integer, primary_key = True)
    area_name = db.Column(db.String(250))

    def __repr__(self):
    
        return '\n area_id: {0} area_name: {1}'.format(self.area_id, self.area_name)


    def __str__(self):

        return '\n area_id: {0} area_name: {1}'.format(self.area_id, self.area_name)

class position(db.Model):
    __tablename__ = 'position' 
    position_id = db.Column(db.Integer, primary_key = True)
    area_id = db.Column(db.Integer)
    position_name = db.Column(db.String(250))

    def __repr__(self):
    
        return '\n position_id: {0} position_id: {1} position_name: {2}'.format(self.position_id, self.area_id, self.position_name)


    def __str__(self):

        return '\n position_id: {0} area_id: {1} position_name: {2}'.format(self.position_id, self.area_id, self.position_name)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = Users(username=request.form['username'],
                    email=request.form['email'],
                    password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('You are now registered!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Users.query.filter_by(email=request.form['email']).first()
        if user and user.verify_password(request.form['password']):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


def get_dropdown_values():

    area_records = area.query.all()
    # Create an empty dictionary
    myDict = {}
    for p in area_records:
    
        key = p.area_name
        area_id = p.area_id

        q = position.query.filter_by(area_id=area_id).all()
    
        lst_c = []
        for c in q:
            lst_c.append( c.position_name )
        myDict[key] = lst_c
    
    class_entry_relations = myDict
                        
    return class_entry_relations

@app.route("/area")
@login_required
def show_area():
    areas_data = area.query.all()  # Corrected to use the 'area' model
    # Create a table with HTML
    table_html = "<table><tr><th>Area ID</th><th>Area Name</th></tr>"
    for area_obj in areas_data:
        table_html += f"<tr><td>{area_obj.area_id}</td><td>{area_obj.area_name}</td></tr>"
    table_html += "</table>"
    return table_html

@app.route("/position")
@login_required
def show_position():
    positions_data = position.query.all()  # Query all positions from the database
    # Start the HTML for the table
    table_html = "<table border='1'><tr><th>Position ID</th><th>Position Name</th></tr>"    
    # Loop through the positions and add each one as a new row in the table
    for pos in positions_data:
        table_html += f"<tr><td>{pos.position_id}</td><td>{pos.position_name}</td></tr>"    
    table_html += "</table>"
    return table_html


@app.route('/_update_dropdown')
def update_dropdown():

    # the value of the first dropdown (selected by the user)
    selected_class = request.args.get('selected_class', type=str)

    # get values for the second dropdown
    updated_values = get_dropdown_values()[selected_class]

    # create the value sin the dropdown as a html string
    html_string_selected = ''
    for entry in updated_values:
        html_string_selected += '<option value="{}">{}</option>'.format(entry, entry)

    return jsonify(html_string_selected=html_string_selected)


@app.route('/_process_data')
def process_data():
    selected_class = request.args.get('selected_class', type=str)
    selected_entry = request.args.get('selected_entry', type=str)

    # process the two selected values here and return the response; here we just create a dummy string

    return jsonify(random_text="You selected the area: {} and the position: {}.".format(selected_class, selected_entry))


@app.route("/index")
def index():
    return render_template('index.html')


@app.route('/area_position')
@login_required
def select_area_position():

    """
    initialize drop down menus
    """

    class_entry_relations = get_dropdown_values()

    default_classes = sorted(class_entry_relations.keys())
    default_values = class_entry_relations[default_classes[0]]

    return render_template('area_position.html',
                       all_classes=default_classes,
                       all_entries=default_values)

@app.route('/admin/add_area', methods=['GET', 'POST'])
@login_required
def add_area():
    if not current_user.is_admin:
        return 'Access Denied', 403
    if request.method == 'POST':
        area_name = request.form['area_name']
        new_area = area(area_name=area_name)
        db.session.add(new_area)
        db.session.commit()
        flash('Area added successfully!')
        return redirect(url_for('add_area'))
    return render_template('add_area.html')


@app.route('/admin/add_position', methods=['GET', 'POST'])
@login_required
def add_position():
    if not current_user.is_admin:
        return 'Access Denied', 403
    if request.method == 'POST':
        position_name = request.form['position_name']
        area_id = request.form['area_id']
        new_position = position(position_name=position_name, area_id=area_id)
        db.session.add(new_position)
        db.session.commit()
        flash('Position added successfully!')
        return redirect(url_for('add_position'))
    areas = area.query.all()
    return render_template('add_position.html', areas=areas)

# admin_area_manage
@app.route('/admin/manage_areas', methods=['GET', 'POST'])
@login_required
def manage_areas():
    if not current_user.is_admin:
        return 'Access Denied', 403

    if request.method == 'POST':
        if 'add_area' in request.form:
            area_name = request.form['area_name']
            new_area = area(area_name=area_name)
            db.session.add(new_area)
            db.session.commit()
            flash('Area added successfully!')
        elif 'delete_area' in request.form:
            area_id = request.form['area_id']
            area_to_delete = area.query.get(area_id)
            db.session.delete(area_to_delete)
            db.session.commit()
            flash('Area deleted successfully!')
        elif 'edit_area' in request.form:
            area_id = request.form['area_id']
            edited_area_name = request.form['edited_area_name']
            area_to_edit = area.query.get(area_id)
            area_to_edit.area_name = edited_area_name
            db.session.commit()
            flash('Area updated successfully!')

    areas = area.query.all()
    return render_template('manage_areas.html', areas=areas)


# admin_position_manage
@app.route('/admin/manage_positions', methods=['GET', 'POST'])
@login_required
def manage_positions():
    if not current_user.is_admin:
        return 'Access Denied', 403
    
    if request.method == 'POST':
        if 'add_position' in request.form:
            position_name = request.form['position_name']
            area_id = request.form['area_id']
            new_position = position(position_name=position_name, area_id=area_id)
            db.session.add(new_position)
            db.session.commit()
            flash('Position added successfully!')
            return redirect(url_for('manage_positions'))
        
        elif 'delete_position' in request.form:
            position_id = request.form['position_id']
            position_to_delete = position.query.get(position_id)
            db.session.delete(position_to_delete)
            db.session.commit()
            flash('Position deleted successfully!')
            return redirect(url_for('manage_positions'))
        
        elif 'edit_position' in request.form:
            position_id = request.form['position_id']
            position_to_edit = position.query.get(position_id)
            position_to_edit.position_name = request.form['edited_position_name']
            position_to_edit.area_id = request.form['edited_area_id']
            db.session.commit()
            flash('Position updated successfully!')
            return redirect(url_for('manage_positions'))

    areas = area.query.all()
    positions = position.query.all()
    return render_template('manage_positions.html', areas=areas, positions=positions)

if __name__ == '__main__':
    app.run(debug=True, port=5001)


