from flask_restful import reqparse
from flask import Flask, render_template, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/oushima/Documents/student-connect/app/student-connect.db'
db = SQLAlchemy(app)
api = Api(app)


class Receiver(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    sender_message_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    receiver_message_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    channel = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(4096), nullable=False)
    timestamp = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200), unique=True, nullable=False)
    avatar = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)


class UserConversation(Resource):
    def get(self):
        # Get sender_id, receiver_id, and channel from the query parameters in the URL
        sender_id = int(request.args.get('sender_id'))
        receiver_id = int(request.args.get('receiver_id'))
        # Use 'private' as the default value if not provided
        channel = request.args.get('channel', 'private')

        # Find the messages where the sender, receiver, and channel are matched
        messages = Message.query \
            .join(Receiver, (Message.user_id == Receiver.sender_message_id) | (Message.user_id == Receiver.receiver_message_id)) \
            .filter((Receiver.sender_message_id == sender_id) & (Receiver.receiver_message_id == receiver_id) & (Message.channel == channel)) \
            .all()

        result = [
            {
                'id': message.id,
                'channel': message.channel,
                'message': message.message,
                'timestamp': message.timestamp,
                'status': message.status,
                'user_id': message.user_id
            }
            for message in messages
        ]
        return {'messages': result}


class Chats(Resource):
    def get(self, user_id):
        # Find the users you have sent messages to
        subquery = db.session.query(Receiver.receiver_message_id).filter(
            Receiver.sender_message_id == user_id).subquery()
        users = User.query.filter(User.id.in_(subquery)).all()

        result = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.name,
                'avatar': user.avatar,

            }
            for user in users
        ]
        return result


class SendMessage(Resource):
    def post(self):
        message = request.form['message']

        # Save the message to the database
        new_message = Message(channel='private', message=message,
                              timestamp='', status='sent', user_id=1)
        db.session.add(new_message)
        db.session.commit()

        return {'message': 'Message sent successfully'}, 200


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chats.html')
def chats_template():
    resource = Chats()
    users = resource.get(1)
    return render_template('chats.html', users=users)


@app.route('/conversation.html')
def conversation_template():
    resource = UserConversation()
    conversations = resource.get()
    messages = conversations['messages']
    return render_template('conversation.html', messages=messages)


api.add_resource(Chats, '/chats')
api.add_resource(UserConversation, '/conversation')
api.add_resource(SendMessage, '/send-message')

if __name__ == '__main__':
    app.run(debug=True)


# http://localhost:5000/conversation.html?sender_id=1&receiver_id=2&channel=private
