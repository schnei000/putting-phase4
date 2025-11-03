from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, api, db
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            new_user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            # Utilise le setter pour hacher le mot de passe
            new_user.password_hash = data['password']
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return new_user.to_dict(), 201
        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return {'errors': ['validation errors: ' + str(e)]}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return user.to_dict(), 200
        return {'error': 'Not authorized'}, 401


class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password'}, 401


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return '', 204
        return {'error': 'Not authorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Not authorized'}, 401
        user = User.query.filter(User.id == user_id).first()
        if user:
            return [r.to_dict(rules=('-user.recipes',)) for r in Recipe.query.all()], 200
        return {'error': 'Not authorized'}, 401

    def post(self):
        if 'user_id' not in session:
            return {'error': 'Not authorized'}, 401
        data = request.get_json()
        try:
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=session['user_id']
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except ValueError as e:
            return {'errors': [str(e)]}, 422


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)