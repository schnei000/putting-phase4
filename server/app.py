from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
 
from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        try:
            data = request.get_json()
            user = User(
                username=data['username'],
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data['password']

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return user.to_dict(), 201

        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422
        except (KeyError, ValueError) as e:
            db.session.rollback()
            return {'error': str(e)}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401


class Login(Resource):
    def post(self):
        data = request.get_json()
        try:
            username = data['username']
            password = data['password']
            
            user = User.query.filter(User.username == username).first()
            
            if user and user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
            else:
                return {'error': 'Invalid username or password'}, 401
        except Exception:
            return {'error': 'Invalid username or password'}, 401


class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if user_id:
            session.pop('user_id', None)
            return {}, 204
        else:
            return {'error': 'Unauthorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        else:
            return {'error': 'Unauthorized'}, 401
    
    def post(self):
        user_id = session.get('user_id')
        if user_id:
            try:
                data = request.get_json()
                
                recipe = Recipe(
                    title=data['title'],
                    instructions=data['instructions'],
                    minutes_to_complete=data['minutes_to_complete'],
                    user_id=user_id
                )
                
                db.session.add(recipe)
                db.session.commit()
                
                return recipe.to_dict(), 201
            except Exception as e:
                db.session.rollback()
                return {'error': str(e)}, 422
        else:
            return {'error': 'Unauthorized'}, 401

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)