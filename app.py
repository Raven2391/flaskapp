from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func
import plotly.express as px
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(200), nullable=True)

# Routes
@app.route('/')
def index():
    # Get the sort order from the query string (default is no sorting)
    sort_order = request.args.get('sort', 'default')

    # Base query
    recipes = Recipe.query

    # Apply sorting logic based on user selection
    if sort_order == 'category':
        # Custom order for categories
        category_order = ['Breakfast', 'Lunch', 'Dinner', 'Dessert']
        recipes = sorted(recipes.all(), key=lambda r: category_order.index(r.category))
    elif sort_order == 'difficulty':
        recipes = recipes.order_by(Recipe.difficulty).all()
    elif sort_order == 'name':
        recipes = recipes.order_by(Recipe.name).all()
    else:
        # Default order (no specific sorting)
        recipes = recipes.all()

    return render_template('project_list.html', recipes=recipes, sort_order=sort_order)

@app.route('/', methods=['POST'])
def add_recipe():
    name = request.form['recipe_name']
    category = request.form['category']
    difficulty = int(request.form['difficulty'])
    ingredients = request.form['ingredients']

    # Handle file upload
    photo = request.files['photo']
    photo_filename = None
    if photo:
        photo_filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

    new_recipe = Recipe(
        name=name,
        category=category,
        difficulty=difficulty,
        ingredients=ingredients,
        photo_filename=photo_filename
    )
    db.session.add(new_recipe)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if request.method == 'POST':
        recipe.name = request.form['recipe_name']
        recipe.category = request.form['category']
        recipe.difficulty = int(request.form['difficulty'])
        recipe.ingredients = request.form['ingredients']

        # Handle file upload
        photo = request.files['photo']
        if photo:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            recipe.photo_filename = photo_filename

        db.session.commit()
        return redirect('/')
    return render_template('update.html', recipe=recipe)

@app.route('/delete/<int:id>')
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.photo_filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.photo_filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    db.session.delete(recipe)
    db.session.commit()
    return redirect('/')

@app.route('/visualization')
def visualization():
    # Sample data (you can replace this with data fetched from your database)
    data = db.session.query(Recipe.category, func.count(Recipe.id)).group_by(Recipe.category).all()
    data_dict = {'Category': [row[0] for row in data], 'Count': [row[1] for row in data]}
    # Create an interactive pie chart with Plotly
    fig = px.pie(
        data_dict, 
        names='Category', 
        values='Count', 
        title='Recipe Distribution by Category',
        color_discrete_sequence=['#FF6F61', '#6FA5FF', '#61FF6F', '#FFC861']  # Custom colors
    )

    # Convert the plot to an HTML div
    graph_html = fig.to_html(full_html=False)

    return render_template('visualization.html', graph=graph_html)
 


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)



 
