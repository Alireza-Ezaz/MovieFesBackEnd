from flask import Flask, request, jsonify, Response, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Resource, Api
from sqlalchemy.orm import backref
from datetime import datetime
from functools import wraps

app = Flask(__name__)

api = Api(app)
app.config['JSON_SORT_KEYS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MovieFes.db'  # Specify database name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Movie(db.Model):
    __tablename__ = 'Movie'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    director = db.Column(db.String)
    poster = db.Column(db.String)

    def __init__(self, name, director, poster):
        self.name = name
        self.director = director
        self.poster = poster


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)

    def __init__(self, username):
        self.username = username


class Comment(db.Model):
    __tablename__ = 'Comment'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('User.id'))
    user = db.relationship("User", backref=backref("User", uselist=False))
    movieId = db.Column(db.Integer, db.ForeignKey('Movie.id'), nullable=False)
    movie = db.relationship("Movie", backref=backref("Movie", uselist=False))

    def __init__(self, userId, movieId, comment_body):
        self.userId = userId
        self.movieId = movieId
        self.comment = comment_body


class MovieSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'director', 'poster')


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username')


class CommentSchema(ma.Schema):
    class Meta:
        fields = ('id', 'comment', 'userId', 'movieId')


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)


@app.route('/getMovies', methods=['GET'])
def get_movies():
    try:
        movies = Movie.query.all()
        return make_response(jsonify(movies_schema.dump(movies)), 200)
    except Exception as ex:
        return make_response({'message': 'There is an internal issue.'}, 500)


@app.route('/getComments', methods=['GET'])
def get_comments():
    try:
        comments = Comment.query.all()
        return make_response(jsonify(comments_schema.dump(comments)), 200)
    except Exception as ex:
        return make_response({'message': 'There is an internal issue.'}, 500)

@app.route('addComment', methods=['POST'])
def add_comment():
    try:
        data = request.get_json()
        userId = data['userId']
        movieId = data['movieId']
        comment_body = data['comment']
        comment = Comment(userId, movieId, comment_body)
        db.session.add(comment)
        db.session.commit()
        return make_response(jsonify(comment_schema.dump(comment)), 200)
    except Exception as ex:
        return make_response({'message': 'There is an internal issue.'}, 500)
