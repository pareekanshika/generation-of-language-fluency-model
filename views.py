from django.shortcuts import render
import mysql.connector as sql

# Create your views here.

na = ''
pn = ''
em = ''
pwd = ''

def SignupPage(request):
    global na, pn, em, pwd

    if request.method == "POST":
        m = sql.connect(host="localhost", user="anshi", password="root_anshi", database='project')
        cursor = m.cursor()

        d = request.POST
        for key, value in d.items():
            if key == "name":
                na = value
            elif key == "number":
                pn = value
            elif key == "email":
                em = value
            elif key == "psw":
                pwd = value

        # Use parameterized query to avoid SQL injection
        c="insert into user_details Values('{}','{}','{}','{}')".format(em,pwd,na,pn)
        cursor.execute(c)  
        m.commit()

    return render(request, 'signup.html')