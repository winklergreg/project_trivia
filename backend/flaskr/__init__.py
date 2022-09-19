from nis import cat
import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [q.format() for q in selection]
    current_questions = questions[start:end]

    return current_questions

def get_question(questions):
    return questions[random.randrange(0, len(questions), 1)]

def check_if_question_used(question, previous_questions):
    used = False
    for q in previous_questions:
        if q == question.id:
            used = True
            break
    
    return used

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    ###################################################################
    ######                     Endpoint Routes                   ######
    ###################################################################
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.type).all()

        if len(categories) == 0:
            abort(404)
        
        return jsonify({
            'success': True,
            'categories': {c.id: c.type for c in categories}
        })

    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.type).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': [q for q in current_questions],
            'total_questions': len(selection),
            'categories': {c.id: c.type for c in categories},
            'current_category': None
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('searchTerm', None)
        
        if 'searchTerm' in body:
            try:
                if not search:
                    selection = Question.query.order_by(Question.id).all()
                else:      
                    selection = Question.query.order_by(Question.id).filter(
                        Question.question.ilike(f"%{search}%")
                    ).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': [q for q in current_questions],
                    'total_questions': len(selection),
                    'current_category': None
                })
            except:
                abort(404)
        elif 'question' in body:
            try:
                question = Question(
                    question=new_question, 
                    answer=new_answer, 
                    category=new_category, 
                    difficulty=new_difficulty
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': question.id
                })
            except:
                abort(404)
        else:
            abort(400)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        try:
            selection = Question.query.filter_by(category=category_id).all()
            current_questions = paginate_questions(request, selection)

            if len(current_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': category_id
            })
        except:
            abort(404)

    @app.route('/quizzes', methods=['POST'])
    def get_random_quiz_question():
        try:
            body = request.get_json()

            previous_questions = body.get('previous_questions', None)
            category = body.get('quiz_category', None)

            if category.get('id') == 0:
                questions = Question.query.all()
            else:
                questions = Question.query.filter_by(
                    category=category.get('id')
                ).all()

            total_questions = len(questions)
            question = get_question(questions)
            while check_if_question_used(question, previous_questions):
                question = get_question(questions)

                if len(previous_questions) == total_questions:
                    return jsonify({
                        'success': True
                    })

            return jsonify({
                'success': True,
                'question': question.format()
            })
        except:
            abort(400)


    ###################################################################
    ######                      ERROR HANDLING                   ######
    ###################################################################
    @app.errorhandler(400)
    def bad_request(error):
        return(
            jsonify({
                'success': False,
                'error': 400,
                'message': 'bad request'
            }), 400
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                'success': False,
                'error': 404,
                'message': 'resource not found'
            }), 404
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                'success': False,
                'error': 422,
                'message': 'unprocessable'
            }), 422
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        return (
            jsonify({
                'success': False,
                'error': 500,
                'message': 'internal server error'
            }), 500
        )

    return app

