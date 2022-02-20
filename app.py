import os

from flask import Flask, request, jsonify, Response, make_response, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Resource, Api
from sqlalchemy.orm import backref
from datetime import datetime
from functools import wraps
from flask_cors import CORS, cross_origin
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# from werkzeug import secure_filename


# Set up translation service
apiKey = "OtU_So4WkmFiM5r8I4QKTYctCtyQnneUFn7sNVPe43OZ"
translatorURL = "https://api.eu-gb.language-translator.watson.cloud.ibm.com/instances/582b8da1-4753-4537-9871-84f1b0ab3e3f"
authenticator = IAMAuthenticator(apiKey)
languageTranslator = LanguageTranslatorV3(version='2018-05-01', authenticator=authenticator)
languageTranslator.set_service_url(translatorURL)

translation = languageTranslator.translate(text='I am doctor', model_id='en-es').get_result()['translations'][0][
    'translation']
print(translation)

# set up database
app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

api = Api(app)
app.config['JSON_SORT_KEYS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MovieFes.db'  # Specify database name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Set up upload folder
app.config['MAX_CONTENT_PATH'] = 2 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        fields = ('id', 'comment', 'userName')


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)


@app.route('/getMovies', methods=['GET'])
# @cross_origin()
def get_movies():
    try:
        movies = Movie.query.all()
        return make_response(jsonify(movies_schema.dump(movies)), 200)
    except Exception as ex:
        return make_response({'message': 'There is an internal issue.'}, 500)


@app.route('/getComments/<movie_id>', methods=['GET'])
def get_comments(movie_id):
    try:
        # comments = Comment.query.filter_by(movieId=movie_id)
        # for comment in comments:
        #     comment.comment = \
        #     languageTranslator.translate(text=comment.comment, model_id='en-es').get_result()['translations'][0][
        #         'translation']
        try:
            language = request.args.get('language')
        except Exception as ex:
            print('hihihi')
            language = 'en'
        print(language)
        if language is None:
            language = 'en'

        comments_db = Comment.query. \
            join(User, Comment.userId == User.id) \
            .add_columns(User.username, Comment.id, Comment.comment) \
            .filter(Comment.movieId == movie_id)

        comments = []
        for comment in comments_db:
            if language == 'en':
                comments.append({
                    "id": comment.id,
                    "username": comment.username,
                    "comment": comment.comment
                })
            else:
                comments.append({
                    "id": comment.id,
                    "username": comment.username,
                    "comment":
                        languageTranslator.translate(text=comment.comment, model_id='en-' + language).get_result()[
                            'translations'][0]['translation']
                })
        return make_response(jsonify({"comments": comments}), 200)

    except Exception as ex:
        return make_response({'message': ex}, 500)


@app.route('/addComment', methods=['POST'])
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


# @app.route('/uploader')
# def upload_file():
#     return render_template('upload.html')


@app.route('/uploadComment', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            f.save(f.filename)
            return 'file uploaded successfully'
        else:
            return 'file extension not allowed'
    return 'could not upload file'
    #
#
# @app.route('/uploadComment', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             print('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             print('No selected file')
#             return redirect(request.url)
#
#         filename = file.filename
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         return redirect(url_for('download_file', name=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''
