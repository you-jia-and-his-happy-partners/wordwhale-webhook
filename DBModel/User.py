from app import db


# Define the model with columns id (user id or group id), session_id, grammar_on, caption_on
class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    session_id = db.Column(db.String)
    grammar_on = db.Column(db.Boolean, default=False)
    caption_on = db.Column(db.Boolean, default=False)
    translation_on = db.Column(db.Boolean, default=False)