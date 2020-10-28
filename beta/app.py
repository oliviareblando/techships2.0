from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify, Response)
from werkzeug.utils import secure_filename
from threading import Thread, Lock



import sys, os, random
import imghdr
import random
import cs304dbi as dbi
import sqlHelper
import bcrypt

app = Flask(__name__)

app.secret_key = 'Foldertennis00'

app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


# new for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1024*1024*1024 #1*1024*1024 is 1 MB

work = []                       # shared data structure ===
lock = Lock()                   # create lock =============

@app.route('/')
def index():
    '''Displays home page with most recent database.'''
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    internships = sqlHelper.getInternships(conn)
    total = sqlHelper.getTotal(conn)['count(*)']
    if (session.get('uid')):
        uid = session['uid']
        favorites = sqlHelper.getFavorites(conn, uid)
        return render_template('mainUID.html', internships = internships, total = total, favorites = favorites)
    else:
        return render_template('main.html', internships = internships, total = total)

@app.route('/upload/', methods=['GET','POST'])
def upload():
    '''Displays upload page, and allows user to submit an internship link to database.'''  
    conn = dbi.connect()
    try: 
        uid = session['uid']
        # These forms go to the upload route
        if (session.get('uid')): #if it exists
            if request.method == 'GET':
                return render_template('upload.html')

            else:
                compName = request.form['compName']
                link = request.form['link']
                city = request.form['location']
                role = request.form['role']
                seasonList = request.form.getlist('season')
                season= ','.join([str(elem) for elem in seasonList])
                year = request.form['year']
                experienceList = request.form.getlist('experience')
                experience = ','.join([str(elem) for elem in experienceList])
                print(experience)
                print(uid)
                # Insert to database
                lock.acquire()
                if sqlHelper.companyExists(compName) == 0:
                    sqlHelper.insertCompany(compName)
                lock.release()
                sqlHelper.insertApplication(link,compName,city,uid,role,season,year,experience)
                flash('Internship at ' + compName + ' was uploaded successfully')
                return render_template('upload.html')
            
            #User must login before uploading 
    except KeyError:
        flash('You must be logged in to upload information.')
        return redirect(url_for('index'))

@app.route('/search', methods=['GET','POST'])
def search():
    '''Displays search page, and then filters results based on user-given criteria.'''  
    conn = dbi.connect()
    if request.method =='GET':
        return render_template('search.html')
    else:
        role = request.form['role']
        appsList = sqlHelper.getByRole(conn, role)
        return render_template('searchResults.html', internships = appsList, criteria = "ROLE")

@app.route('/searchExp', methods = ['POST']) 
def searchExp():
    conn = dbi.connect()
    if request.method == 'POST':
        exp = request.form['experience']
        print("TEST!!!")
        print(exp)
        appsList = sqlHelper.getByExperience(conn, exp)
        return render_template('searchResults.html', internships = appsList, criteria = "EXPERIENCE")
    else:
        return render_template('search.html')


@app.route('/favorite/', methods=['POST'])
def favorite():
    '''Adds or removes application from list of favorites when button is clicked.'''
    ###This should be done with Ajax so we don't have to reload the entire page.
    conn = dbi.connect()
    if (session.get('uid')): #if it exists
        uid = session['uid']
        # Get data from form: 
        data = request.form
        link = data['link']
        print('Link:' + link)
        # Update database
        if sqlHelper.isFavorite(conn,uid,link) != True:
            sqlHelper.addFavorite(conn,uid, link)
        # response dictionary
            resp_dic = {'link': link}
            print("respLink:" + resp_dic['link'])
            return jsonify(resp_dic)
    else:
        flash('You must be logged in to add to your favorites.')
        return redirect(url_for('index'))


@app.route('/saved', methods=['GET','POST'])
def saved():
    conn = dbi.connect()
    if request.method == 'GET':
        if (session.get('uid')): #if it exists
            uid = session['uid']
            if request.method == "GET":
                saved = sqlHelper.getFavorites(conn, uid)
                return render_template('saved.html', internships = saved)
        else:
            flash('You must be logged in to add to your favorites.')
            return redirect(url_for('index'))
    else:
        if (session.get('uid')): #if it exists
            uid = session['uid']
            # Get data from form: 
            data = request.form
            link = data['link']
            print('Link:' + link)
            # Update database
            # remove from favs
            sqlHelper.removeFavorite(uid, link)
            # response dictionary
            resp_dic = {'link': link}
            print("respLink:" + resp_dic['link'])
            return jsonify(resp_dic)
    


@app.route('/login', methods = ['GET','POST'])
def login():
    '''Displays login page, and redirects to search page after user logs in successfully.'''
    if request.method == "POST":
        try:
            username = request.form['username']
            passwd = request.form['password']
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            curs.execute('''SELECT uid,password1
                        FROM user
                        WHERE uid = %s''',
                        [username])
            row = curs.fetchone()
            if row is None:
                # Same response as wrong password,
                # so no information about what went wrong
                flash('login incorrect. Try again or join')
                return redirect( url_for('index'))
            hashed = row['password1'] #was 'hashed'
            print('database has hashed: {} {}'.format(hashed,type(hashed)))
            print('form supplied passwd: {} {}'.format(passwd,type(passwd)))
            x = hashed.encode('utf-8')
            hashed2 = bcrypt.hashpw(passwd.encode('utf-8'), x)
            hashed2_str = hashed2.decode('utf-8')
            print('rehash is: {} {}'.format(hashed2_str,type(hashed2_str)))
            if hashed2_str == hashed:
                session['uid'] = request.form['username']
                flash('''Successfully logged in.''')
                return redirect(url_for('search'))
            else:
                flash('''Login failed. Invalid username or password.''')
                return redirect(url_for('login'))
        except Exception as err:
            flash('form submission error '+str(err))
            return redirect( url_for('index') )
    else:
        return render_template('login.html')

  
@app.route('/register', methods = ['GET','POST'])
def register():
    '''Displays register page, and redirects to search page after registration.'''  
    conn = dbi.connect()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        school = request.form['school']

        #Validate username, pw, email entries
        if not username:
            error = 'Username is required.'
            flash(error)
        elif not password:
            error = 'Password is required.'
            flash(error)
        elif not email:
            error = 'Email is required.'
            flash(error)
        else:
            lock.acquire()
            is_username_unique = sqlHelper.is_username_unique(conn,username)
            #Check for username uniqueness, register if it is unique
            if is_username_unique == True:
                try:
                    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    sqlHelper.register(conn, username, hashed, email, school)
                    lock.release()
                    flash('''Account has been created.''')
                    return redirect(url_for('login'))
                except:
                    error = '''This user is already registered.'''
                    flash(error)
                    lock.release()
                    return render_template('register.html')
            else:
                error = '''This username is already taken. 
                Please pick a new username'''
                flash(error)
                lock.release()
                return render_template('register.html')            
    
    else:
        return render_template('register.html')

@app.route("/company/<compName>", methods=["GET", "POST"])
def company(compName):
    conn = dbi.connect()
    if request.method == 'GET':
        appList = sqlHelper.getByCompany(conn, compName)
        return render_template('company.html', src=url_for('pic',nm=compName),
                                   nm=compName, comp = compName, internships = appList)
    else:
        appList = sqlHelper.getByCompany(conn, compName)
        if (session.get('uid')):
            uid = session['uid']
            try:
                #nm = int(request.form['nm']) # may throw error
                f = request.files['pic']
                user_filename = f.filename
                ext = user_filename.split('.')[-1]
                filename = secure_filename('{}.{}'.format(compName,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                f.save(pathname)
                curs = dbi.dict_cursor(conn)
                curs.execute(
                    '''insert into picfile(compName,filename) values (%s,%s)
                       on duplicate key update filename = %s''',
                    [compName, filename, filename])
                conn.commit()
                flash('Upload successful')
                return render_template('company.html',
                                    src=url_for('pic',nm=compName),
                                    nm=compName, comp = compName, internships = appList)
            except Exception as err:
                flash('Upload failed {why}'.format(why=err))
                return render_template('company.html',src='',nm='', comp = compName, internships = appList)
        else:
            flash('You must be logged in to add a photo.')
            return render_template('company.html',
                                    src=url_for('pic',nm=compName),
                                    nm=compName, comp = compName, internships = appList)
@app.route('/pic/<nm>')
def pic(nm):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    numrows = curs.execute(
        '''select filename from picfile where compName = %s''',
        [nm])
    if numrows == 0:
        flash('No picture for {}'.format(nm))
        return redirect(url_for('company', compName = nm))
    row = curs.fetchone()
    return send_from_directory(app.config['UPLOADS'],row['filename'])

            

@app.route("/logout")
def logout():
    uid = session['uid']
    session.pop('uid', None)
    session['uid'] = None

    flash('Successfully logged out.')
    return redirect(url_for('index'))

@app.before_first_request
def init_db():
    dbi.cache_cnf()
    dbi.use('techship_db')

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
