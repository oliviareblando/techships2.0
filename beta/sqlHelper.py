# Techships 
# queries
import cs304dbi as dbi

uid = "testuser" #for now, until we implement logins

# ==========================================================
# The functions that do most of the work.


# assuming the form has a dropdown of companies and the value stored is the cid.
# if it's a text field, then change this to inner join company and modify query
def getInternships(conn):
    # Returns all internship application information
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from application''')
    return curs.fetchall()

def getByCompany(conn, compName):
    # Returns the link, cid, uid, role, season, experience, city, state, and country
    # of all applications for a specified company, as a list of dictionaries.
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from application
    where compName = %s;''', [compName])
    return curs.fetchall()

def getByRole(conn, role):
    # Returns the link, cid, uid, role, season, experience, city, state, and country
    # of all applications for a specified role, as a list of dictionaries.
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from application
    where role = %s;''', [role])
    return curs.fetchall()

def getByExperience(conn, exp):
    # Returns the link, cid, uid, role, season, experience, city, state, and country
    # of all applications needing specified experience/year, as a list of dictionaries.
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from application
    where experience like %s;''', ['%' + exp+ '%'])
    return curs.fetchall()

def getByLocation(conn, location):
    # Returns the link, cid, uid, role, season, experience, city, state, and country
    # of all applications needing specified location, as a list of dictionaries.
    curs = dbi.dict_cursor(conn)
    curs.execute('''select application.link, uid, role, season, experience, city 
    from appLocation, application where city = %s;''', [location])
    return curs.fetchall()

def getTotal(conn):
    # Returns the total number of internship postings
    curs = dbi.dict_cursor(conn)
    curs.execute('''select count(*) from application''')
    return curs.fetchone()

def companyExists(compName):
    # Given a company name, checks if it's already in the company table, 
    # returns a boolean
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''select count(*) from company
    where compName = %s;''',[compName])
    result = curs.fetchone()
    return result[0]==1

def insertCompany(compName):
    # Given a company name, inserts it into the company table
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''INSERT INTO company(compName) 
                values (%s);''', [compName])
    conn.commit()

def insertApplication(link,compName,city,uid,role,season,year,experience): 
    # Given the link, compName, location, role, season, yr, experience, inserts an
    # application into the database.
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''insert into application(link,compName, uid, role,season,yr,experience) 
                values (%s, %s, %s, %s, %s, %s, %s);''', [link, compName, uid, role, season, 
                year, experience])            
    conn.commit()
    curs.execute('''insert into appLocation(city, link) values (%s,%s);''',[city, link])
    conn.commit()

def insertReview(uid, compName, reviewText):
    #Given the uid, compName, and review, inserts a review into the database.
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''insert into review(uid, compName, reviewText) values (%s, %s, %s);''', 
                [uid, compName, reviewText])
    conn.commit()

def deleteReview(uid, compName):
    #Given the uid and compName, deletes a review from the database. 
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''delete from review where uid = %s and compName = %s;''', 
                [uid, compName])
    conn.commit()


def addFavorite(conn, uid, link):
    # Adds application to users' list of favorites, or removes if needed
    curs = dbi.cursor(conn)
    curs.execute('''insert into favorites(uid, link)
                values (%s, %s);''', [uid, link])
    conn.commit()

def removeFavorite(uid, link):
    # Removes application from users' list of favorites'''
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    sql = '''delete from favorites where uid = %s and link = %s'''
    curs.execute(sql, [uid, link])
    conn.commit()
     
def getFavorites(conn, uid):
    # Gets list of all favorited internships
    curs = dbi.dict_cursor(conn)
    sql = '''select link,compName,role,season,yr,experience
    from application inner join favorites using (link) where favorites.uid = %s;'''
    curs.execute(sql, [uid])
    return curs.fetchall()

def isFavorite(conn, uid, link):
    # Checks if a link is a favorite
    curs = dbi.cursor(conn)
    sql = '''select * from favorites where uid = %s and link = %s'''
    curs.execute(sql, [uid, link])
    result = curs.fetchone()
    if result == None:
        return False
    else:
        return True

def validateLogin(conn, username, password):
    # Given username and password, checks if username + password combo
    # exist within database.
    curs = dbi.cursor(conn)
    sql = '''select * from user where uid = %s and password1 = %s;'''
    result = curs.execute(sql, [username, password])
    print(result)
    if result == None:
        return False
    else:
        return True 

def register(conn, username, password, email, school):
    # Insert movie into database with tt, title, and release year.
    curs = dbi.cursor(conn)
    sql = '''insert into user (uid, password1, email, school) values(%s, %s, %s, %s)'''
    curs.execute(sql, [username, password, email, school])
    conn.commit()

def is_username_unique(conn, username):
    # Checks if username is unique while user is registering.
    curs = dbi.cursor(conn)
    sql = '''select * from user where uid = %s;'''
    result = curs.execute(sql, [username])
    conn.commit()
    if result == None: 
        #username doesn't exist in db, so we can continue with registration
        return False
    else:
        return True

def getPassword(conn, username):
    #Given uid, get username and hashed password."
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    curs.execute('''SELECT uid,password1
                      FROM user
                      WHERE uid = %s''',
                     [username])
    row = curs.fetchone()

    if row is None:
        return False
    else:
        return row 

if __name__ == '__main__':
    dbi.cache_cnf()   # defaults to ~/.my.cnf
    dbi.use('techship_db') 
    conn = dbi.connect()
    # print("By Company:")
    # print(getByCompany(conn,"Google"))
    # print("By Role:")
    # print(getByRole(conn,"Software Engineering"))
    # print("By Experience:")
    
    # fav = handleFavorite('jamie', 'https://careers.google.com/jobs/results/100877793807475398-software-engineering-intern-associates-summer-2021/')

    # test = getFavorites(conn, 'jamie')
    # print(test)

    # print(getByExperience(conn, "Senior"))
    # insertApplication("http://www.test.com","test","Data Science","Fall","2022","Freshman")
    # insertCompany("test2")
    # insertApplication("http://www.test2.com","test2","Data Science","Spring","2023","Freshman")
    # use for testing once our tables are populated
