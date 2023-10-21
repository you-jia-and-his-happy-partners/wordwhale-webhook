from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db = SQLAlchemy(app)

# Define the model with columns id (user id or group id), session_id, grammar_on, caption_on
class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    session_id = db.Column(db.String)
    grammar_on = db.Column(db.Boolean, default=False)
    caption_on = db.Column(db.Boolean, default=False)

# Create the table
def create_table():
    with app.app_context():
        db.create_all()
    return "Table created successfully."

# Insert data into the table
def insert_data(id, session_id, grammar_on, caption_on):
    new_user = User(id=id, session_id=session_id, grammar_on=grammar_on, caption_on=caption_on)
    db.session.add(new_user)
    db.session.commit()
    return True

# Update session_id with specific id
def update_session(id, session_id):
    user = User.query.get(id)
    if user:
        user.session_id = session_id
        db.session.commit()
        return True
    return False

# Update grammar_on and caption_on with specific id
def update_flags(id, grammar_on, caption_on):
    user = User.query.get(id)
    if user:
        user.grammar_on = grammar_on
        user.caption_on = caption_on
        db.session.commit()
        return True
    return False

# Select data with specific id
def select_data(id):
    user = User.query.get(id)
    if user:
        return {"id": user.id, "session_id": user.session_id, "grammar_on": user.grammar_on, "caption_on": user.caption_on}
    return False

# Delete data with specific id
def delete_data(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False

# Drop the table
def drop_table():
    with app.app_context():
        db.drop_all()
    return "Table dropped successfully."