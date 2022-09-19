import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """ This class represents the trivia test case """

    def setUp(self):
        """ Define test variables and initialize app. """
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
        
        self.new_question = {
            'question': 'How is the weather today?',
            'answer': 'beautiful',
            'category': 3,
            'difficulty': 1
        }
    
    def tearDown(self):
        """ Executed after reach test """
        pass

    def test_retrieve_categories(self):
        """ Get all categories using /categories endpoint """
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])

    def test_404_get_invalid_category(self):
        """ Attempt to get an invalid category """
        res = self.client().post('/categories/1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_retrieve_questions(self):
        """ Get all questions using /questions endpoint """
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])

    def test_404_retrieve_questions_invalid_page_number(self):
        """ Attempt to get quesitons on an invalid page """
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_question(self):
        """ Delete a question using /questions/<int:question_id> endpoint """
        question_id = 11
        res = self.client().delete(f'/questions/{question_id}')
        data = json.loads(res.data)
        question = Question.query.get(question_id)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)
        self.assertEqual(question, None)

    def test_422_delete_invalid_question(self):
        """ Attempt to delete a question that does not exist """
        res = self.client().delete('/questions/9999')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_create_question(self):
        """ Create a new question using the /questions endpoint """
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])

    def test_404_create_question(self):
        """ Attempt to create a new question without sending any data """
        res = self.client().post('/questions', json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 400)
        self.assertEqual(data['message'], "bad request")

    def test_search_question(self):
        """ Search the database for questions containing a keyword """
        search_term = 'soccer'
        res = self.client().post('/questions', json={'searchTerm': search_term})
        data = json.loads(res.data)

        selection = Question.query.order_by(Question.id).filter(
            Question.question.ilike(f"%{search_term}%")
        ).all()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertEqual(data['total_questions'], len(selection))

    def test_404_search_question(self):
        """ Attempt to search for questions with an empty request """
        res = self.client().post('/questions', json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 400)
        self.assertEqual(data['message'], "bad request")

    def test_play_quiz(self):
        """ Play the quiz using the /quizzes endpoint """
        res = self.client().post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {'id': 1, 'type': 'Science'}
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
    
    def test_400_play_quiz_missing_category(self):
        """ Attemp to play the quiz without quiz_category request """
        res = self.client().post('/quizzes', json={
            'previous_questions': []
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

    def test_400_play_quiz_missing_previous(self):
        """ Attempt to play the quiz without the previous questions request """
        res = self.client().post('/quizzes', json={
            'quiz_category': {'id': 1, 'type': 'Science'}
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()