def create_table(app, db):
    with app.app_context():
        db.create_all()
        app.logger.debug("DB table created!")


# Insert data into the table
def insert_data(User, app, db, id, session_id, grammar_on, caption_on, translation_on):
    with app.app_context():
        new_user = User(
            id=id, session_id=session_id,
            grammar_on=grammar_on,
            caption_on=caption_on,
            translation_on=translation_on
            )
        db.session.add(new_user)
        db.session.commit()
        return True


# Update session_id with specific id
def update_session(User, app, db, id, session_id):
    with app.app_context():
        user = User.query.get(id)
        if user:
            user.session_id = session_id
            db.session.commit()
            return True
        return False


# Update grammar_on and caption_on with specific id
def update_flags(User, app, db, id, grammar_on, caption_on, translation_on):
    with app.app_context():
        user = User.query.get(id)
        if user:
            user.grammar_on = grammar_on
            user.caption_on = caption_on
            user.translation_on = translation_on
            db.session.commit()
            return True
        return False


# Select data with specific id
def select_data(User, app, id):
    with app.app_context():
        user = User.query.get(id)
        if user:
            return {
                "id": user.id, "session_id": user.session_id,
                "grammar_on": user.grammar_on,
                "caption_on": user.caption_on,
                "translation_on": user.translation_on
            }
        return False


# Delete data with specific id
def delete_data(User, app, db, id):
    with app.app_context():
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
