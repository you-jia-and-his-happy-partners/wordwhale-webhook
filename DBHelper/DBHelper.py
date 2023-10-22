class UserDBHelper(object):
    @classmethod
    def create_table(cls, app, db):
        with app.app_context():
            db.create_all()
            app.logger.debug("DB table created!")

    # Insert data into the table
    @classmethod
    def insert_data(cls, User, app, db, id, grammar_on, caption_on, translation_on):
        with app.app_context():
            new_user = User(
                id=id,
                grammar_on=grammar_on,
                caption_on=caption_on,
                translation_on=translation_on
                )
            db.session.add(new_user)
            db.session.commit()
            return True

    # Update grammar_on and caption_on with specific id
    @classmethod
    def update_flags(cls, User, app, db, id, grammar_on, caption_on, translation_on):
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
    @classmethod
    def select_data(cls, User, app, id):
        with app.app_context():
            user = User.query.get(id)
            if user:
                return {
                    "id": user.id,
                    "grammar_on": user.grammar_on,
                    "caption_on": user.caption_on,
                    "translation_on": user.translation_on
                }
            return False

    # Delete data with specific id
    @classmethod
    def delete_data(cls, User, app, db, id):
        with app.app_context():
            user = User.query.get(id)
            if user:
                db.session.delete(user)
                db.session.commit()
                return True
            return False


class SceneStateDBHelper(object):
    @classmethod
    def insert_data(cls, SceneState, app, db, id, scene):
        with app.app_context():
            new_state = SceneState(
                id=id,
                scene=scene,
                identity="",
                departmentGrade="",
                extracurricularActivities="",
                club="",
                personality="",
                interest="",
                )
            db.session.add(new_state)
            db.session.commit()
            return True

    # Select data with specific id
    @classmethod
    def select_data(cls, SceneState, app, id):
        with app.app_context():
            state = SceneState.query.get(id)
            if state:
                return {
                    "id": state.id,
                    "scene": state.scene,
                    "identity": state.identity,
                    "departmentGrade": state.departmentGrade,
                    "extracurricularActivities": state.extracurricularActivities,
                    "club": state.club,
                    "personality": state.personality,
                    "interest": state.interest,
                }
            return False
        
    # Update grammar_on and caption_on with specific id
    @classmethod
    def update_data(cls, SceneState, app, db, id, data):
        with app.app_context():
            state = SceneState.query.get(id)
            if state:
                state.identity = data["identity"]
                state.departmentGrade = data["departmentGrade"]
                state.extracurricularActivities = data["extracurricularActivities"]
                state.club = data["club"]
                state.personality = data["personality"]
                state.interest = data["interest"]
                db.session.commit()
                return True
            return False

    # Delete data with specific id
    @classmethod
    def delete_data(cls, SceneState, app, db, id):
        with app.app_context():
            state = SceneState.query.get(id)
            if state:
                db.session.delete(state)
                db.session.commit()
                return True
            return False
