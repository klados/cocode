from flask import Flask, render_template, flash, request, redirect, url_for, session
# import sqlite3
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from hashlib import md5
from functools import wraps
from flask_socketio import SocketIO, emit
from waitress import serve
import html.parser as htmlparser


app = Flask(__name__)
app.secret_key = 'this is a TeSt'
socketio = SocketIO(app)
# DATABASE = 'test.db'

mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1Random_password'
app.config['MYSQL_DB'] = 'cocode'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)

live_projects = {}
parser = htmlparser.HTMLParser()



class newProjectForm(Form):
    language = StringField('language', [validators.Length(min=2, max=35)])
    title = StringField('title', [validators.Length(min=2, max=35)])
    description = StringField('description', [validators.Length(min=0, max=200)])


class RegistrationForm(Form):
    username = StringField('username', [validators.Length(min=2, max=35)])
    fullname = StringField('fullname', [validators.Length(min=2, max=35)])
    companyName = StringField('companyName', [validators.Length(min=0, max=35)])
    email = StringField('email', [validators.Length(min=6, max=35)])
    password = PasswordField('password', [
        validators.DataRequired(),
        validators.EqualTo('confirmPassword', message='Passwords must match')
    ])
    confirmPassword = PasswordField('confirmPassword')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedIn' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap
#


@app.route('/')
def index():
    return render_template('home.html')
#


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/projects')
@is_logged_in
def projects():
    email = session.get('email')
    cur = mysql.connection.cursor()
    cur.execute('''select md5(id) as id, title, description, language,
        DATE_FORMAT(created_day, '%%d/%%m/%%Y') as day
        from projects where owner_email = %s order by created_day desc''', (email, ))

    projects = cur.fetchall()
    return render_template('projects.html', projects=projects)


@app.route('/editor')
def wrongPage():
    flash('You have to provide a token', 'danger')
    return redirect(url_for('index'))


@app.route('/editor/<token>')
# @app.route('/editor/<token>/<src_code>')
def editor(token):
    if token in live_projects:
        return render_template('editor.html', token=token,\
                               language=live_projects[token]['language'],\
                               title=live_projects[token]['title'])
    else:
        flash('The token is inactive', 'danger')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if(request.method == 'POST'):
        email = request.form['email']
        passport_input = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute('select * from users where email = %s', (email, ))

        data = cur.fetchone()
        print('result', data)
        if result > 0:

            password = data['password']  # password

            if sha256_crypt.verify(passport_input, password):
                app.logger.info('password matched!')

                session['loggedIn'] = True
                session['username'] = data['username']
                session['email'] = data['email']

                flash('You have successfully logged in', 'success')
                return redirect(url_for('index'))
            else:
                flash('Unknown user or wrong password', 'danger')
                return redirect(url_for('login'))

            #  flash('Welcome to our platform', 'success')
        else:  # no math username
            flash('Unknown user or wrong password', 'danger')
            return redirect(url_for('login'))

    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)

    print('>>>>', form.validate())

    valid = form.validate()
    if(request.method == 'POST' and valid):
        print('new user!', form.fullname.data)
        fullname = form.fullname.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        companyName = form.companyName.data

        try:
            cur = mysql.connection.cursor()
            cur.execute('''
            insert into users (fullname, username, email, password, companyName)
            values(%s,%s,%s,%s,%s)''', (fullname, username, email, password, companyName))
            mysql.connection.commit()

            session['loggedIn'] = True
            session['username'] = username
            session['email'] = email

            flash('Welcome to our platform', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Error account was not created:'+str(e), 'danger')
            print('>>>>>', str(e))
            return redirect(url_for('register'))

    # get request or invalide form
    if valid is False and request.method == 'POST':
        flash('Error account was not created check your inputs', 'danger')

    return render_template('register.html')
# eof


@app.route('/deleteProject', methods=['POST'])
@is_logged_in
def deleteProject():
    projectId = request.get_json()['projectId']
    owner_email = session.get('email')

    print('delete project', projectId, owner_email)

    if projectId is None:
        return '0'
    else:
        try:
            cur = mysql.connection.cursor()
            cur.execute('''delete from projects where md5(id) = %s
                        and owner_email = %s ''', (projectId, owner_email))
            mysql.connection.commit()
            return '1'
        except Exception as e:
            print('exception', e)
            return '0'


@app.route('/openExistingProject', methods=['GET'])
@is_logged_in
def openExistingProject():
    if request.method == 'GET':

        projectId = request.args.get('projectId')
        owner_email = session['email']

        try:
            cur = mysql.connection.cursor()
            numOfRows = cur.execute('''
                select md5(concat(id,owner_email)) as token, title,
                language, src_code from projects where md5(id)=%s
                and owner_email=%s''', (projectId, owner_email))
            mysql.connection.commit()

            if numOfRows != 1:
                raise NameError('Project does not found')
                return '0'
            else:
                data = cur.fetchone()
                token = data['token']

                if token in live_projects:
                    flash('Project is already open', 'danger')
                    return redirect(url_for('projects'))
                else:
                    live_projects[token] = {'language': data['language'], 'title': data['title']}
                    session[token] = data['src_code']
                    return redirect(url_for('editor', token=token))

                    # src_code = parser.unescape(src_code)
                    # print('>>src code ', src_code)
                    #
                    # return render_template('editor.html', token=token,\
                    #     language=live_projects[token]['language'],\
                    #     title=live_projects[token]['title'], src_code=src_code)

            # flash('Send the token to your coworker', 'success')
        except Exception as e:
            print('exeption' + str(e))
            flash('Error retrieving your project: '+str(e), 'danger')
            return redirect(url_for('projects'))
    else:
        flash('Error retrieving your project', 'danger')
        return redirect(url_for('projects'))


@app.route('/saveProject', methods=['POST'])
@is_logged_in
def saveProject():
    src_code = request.get_json()['src']
    token = request.get_json()['token']
    # language = request.get_json()['language']
    owner_email = session.get('email')
    print('>>>>>>', token, owner_email, src_code)

    if token is None:
        return '0'
    else:
        try:
            cur = mysql.connection.cursor()
            numOfRow = cur.execute('''update projects set src_code = %s, updated_day= now()
             where md5(concat(id,%s))= %s and owner_email = %s
            ''', (src_code, owner_email, token, owner_email))
            mysql.connection.commit()
            if numOfRow == 1:
                return '0'
            else:
                return '1'
        except Exception as e:
            print('exception', e)
            return '2'


@app.route('/newProject', methods=['POST'])
@is_logged_in
def newProject():
    form = newProjectForm(request.form)

    if request.method == 'POST' and form.validate():
        owner_email = session['email']
        title = form.title.data
        language = form.language.data
        description = form.description.data

        try:
            cur = mysql.connection.cursor()
            cur.execute('''
                insert into projects(owner_email, title, language, description)
                values (%s,%s,%s,%s)''', (owner_email, title, language, description))
            mysql.connection.commit()

            token = str(cur.lastrowid) + owner_email
            token = md5(token.encode('utf-8')).hexdigest()
            print('>>>>> token generated:', token)
            live_projects[token] = {'language': language, 'title': title}

            flash('Send the token to your coworker', 'success')
            return redirect(url_for('editor', token=token ))
        except Exception as e:
            print('exeption'+ str(e))
            flash('Error project was not created: '+str(e), 'danger')
            return redirect(url_for('index'))
    else:
        flash('Error project was not created!', 'danger')
        return redirect(url_for('index'))
#


@socketio.on('connect')  # ,namespace='/globalChat'
def connect():
    print('>>>>>> new connection!', request.sid)


@socketio.on('disconnect')
def disconnect():
    print('>>> user disconnected ', request.sid)
    for pro in live_projects:
        if 'slaveId' in live_projects[pro] and live_projects[pro]['slaveId'] == str(request.sid):
            if 'masterId' in live_projects[pro] and live_projects[pro]['masterIsLive'] is False:
                del live_projects[pro]
                # print('delete session1')
            else:
                live_projects[pro]['slaveIsLive'] = False
                if 'masterId' in live_projects[pro]:
                    socketio.emit('coworkerConnectionStatus', {'status':'disconnected'}, \
                                room=live_projects[pro]['masterId'])
            break
        elif 'masterId' in live_projects[pro] and live_projects[pro]['masterId'] == str(request.sid):
            if 'slaveIsLive' in live_projects[pro]:
                if live_projects[pro]['slaveIsLive'] is False:
                    del live_projects[pro]
                    # print('delete session2')
                else:
                    live_projects[pro]['masterIsLive'] = False
                    if 'slaveId' in live_projects[pro]:
                        socketio.emit('coworkerConnectionStatus', {'status':'disconnected'}, \
                                room=live_projects[pro]['slaveId'])
            else:
                del live_projects[pro]
                # print('delete session3')
            break

    print('>>> remaining projects :', live_projects)
    return '1'
    # live_projects


@socketio.on('globalChat')
@is_logged_in
def globalChat(txt):
    print('received json: ' + str(txt))
    if len(txt) == 0:
        return
    else:
        # droadcast the message
        emit('globalChat', {"username": session['username'],"txt": str(txt)}, broadcast=True)


def setToken(level, invLevel, token, uniqueId):
    """ level -> master/slave"""
    if (level+'Id') in live_projects[token]:
        if (level+'IsLive') in live_projects[token]:
            if live_projects[token][level+'IsLive'] is False:
                live_projects[token][level+'Id'] = uniqueId
                live_projects[token][level+'IsLive'] = True

                if (invLevel+'Id') in live_projects[token]:
                    socketio.emit('coworkerConnectionStatus', {'status': 'connected'}, \
                                room=live_projects[token][invLevel+'Id'])
            else:
                return -1  # nothing to do
        else:
            live_projects[token][level+'IsLive'] = True
            live_projects[token][level+'Id'] = uniqueId

            if (invLevel+'Id') in live_projects[token]:
                socketio.emit('coworkerConnectionStatus', {'status': 'connected'}, \
                                room=live_projects[token][invLevel+'Id'])

    else:  # first time master/slave
        live_projects[token][level+'Id'] = uniqueId
        live_projects[token][level+'IsLive'] = True

        if (invLevel+'Id') in live_projects[token]:
            socketio.emit('coworkerConnectionStatus', {'status': 'connected'}, \
                                room=live_projects[token][invLevel+'Id'])


@socketio.on('establishEditorConnection')
def establishEditorConnection(token):

    # check if the connected user is the master/owner or the slave
    if 'loggedIn' in session:
        # check if user can recreate the token (prove that he is the master)
        try:
            cur = mysql.connection.cursor()
            numOfRows = cur.execute('''
                       select id from projects where md5(concat(id,%s))= %s
                        ''', (session.get('email'), token))

            if numOfRows != 1:
                print('>>>>>> editor auth slave:', numOfRows, cur.rowcount, session.get('email'))
                setToken('slave', 'master', token, request.sid)
            else:
                print(">>>>> editor master!")
                setToken('master', 'slave', token, request.sid)

        except Exception as e:
            print('>>>>>>>> exception:' + str(e))
            return 1

    else:  # is the slave user
        print('>>> editor not auth slave')
        setToken('slave', 'master', token, request.sid)

    print('>>>>>>> editor estalish connection receive token ', token, 'sid', request.sid, 'live project', live_projects[token])


@socketio.on('shareCode')
def shareCode(data):
    print('>>> sharecode data', data, live_projects[data['token']])
    # check if token exist and if the sender is allowed to send
    if data['token'] in live_projects:
        if 'masterId' in live_projects[data['token']]:
            if live_projects[data['token']]['masterId'] == request.sid:
                # socketio.emit('shareCode', data, room=data['token'])
                socketio.emit('shareCode', data, room=live_projects[data['token']]['slaveId'])
        if 'slaveId' in live_projects[data['token']]:
            if live_projects[data['token']]['slaveId'] == request.sid:
                socketio.emit('shareCode', data, room=live_projects[data['token']]['masterId'])

    # print('>>>> send to room', data, request.sid)
    return 0


@socketio.on('syncSrcCode')
def syncSrcCode(data):
    print('>>> sync data', data)
    if data['token'] in live_projects:
        if live_projects[data['token']]['masterId'] == request.sid:
            socketio.emit('syncSrcCode', {'action': 'receiver', 'src': data['src']}, \
                          room=live_projects[data['token']]['slaveId'] )
        elif live_projects[data['token']]['slaveId'] == request.sid:
            socketio.emit('syncSrcCode', {'action': 'receiver', 'src': data['src']}, \
                          room=live_projects[data['token']]['masterId'] )


@socketio.on('privateChat')
def privateChat(data):
    print(data)
    if data['token'] in live_projects:
        try:
            socketio.emit('privateChat', {'username': session.get('username') or \
                                'anonymous', 'txt': data['msg']}, \
                                room=live_projects[data['token']]['slaveId'])
            socketio.emit('privateChat', {'username': session.get('username') or \
                                'anonymous', 'txt': data['msg']}, \
                                room=live_projects[data['token']]['masterId'])
            return 1
        except Exception as e:
            print('>>> private messages exception',e)
            return 0


if __name__ == '__main__':
    # app.run(debug=True)
    # socketio.run(app, debug=True)
    serve(socketio.run(app, host='0.0.0.0', debug=True), port=5000)


# Flask-WTF passlib
