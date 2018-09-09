from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Kontrol Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs )
        else:
            flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapınız...","danger")
            return redirect(url_for('giriş'))
    return decorated_function

#Kayıt Formu
class KayıtFormu(Form):
    
    name=StringField("İsim Soyisim",validators=[validators.DataRequired(),validators.Length(4,25)])
    username=StringField("Kullanıcı Adı",validators=[validators.DataRequired(),validators.Length(4,25)])
    name=StringField("İsim Soyisim",validators=[validators.DataRequired(),validators.Length(5,15)])
    email=StringField("Email",validators=[validators.DataRequired(),validators.Email(message="Lütfen Geçerli Bir E-mail Adresi Giriniz!")])
    password=PasswordField("Parola",validators=[validators.DataRequired("Lütfen Bir Parola Giriniz"),validators.equal_to(fieldname="confirm",message="Parolanız Uyuşmuyor.")])
    confirm=PasswordField("Parola Doğrula")


#Giriş Formu
class GirişFormu(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")


#Makale Formu
class MakaleFormu(Form):
    title=StringField("Makale Başlığı",validators=[validators.length(5,100)])
    content=TextAreaField("Makale İçerik",validators=[validators.length(100)])


app=Flask(__name__)

app.secret_key="blog"

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="blog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)


@app.route("/")
def anasayfa():
    return render_template("anasayfa.html")

@app.route("/kayıt",methods=["GET","POST"])
def kayıt():
    form=KayıtFormu(request.form)

    if(request.method=="POST" and form.validate()):
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu="INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...",category="success")

        return redirect(url_for("giriş"))
    else:
        return render_template("register.html",form=form)

@app.route("/giriş",methods=["GET","POST"])
def giriş():
    form=GirişFormu(request.form)

    if(request.method=="POST"):
        username=form.username.data
        password=form.password.data

        cursor=mysql.connection.cursor()
        sorgu="SELECT * FROM users where username=%s"

        result=cursor.execute(sorgu,(username,))

        if(result>0):
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(password,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")
                
                session["logged_in"]=True
                session["username"]=username

                
                return redirect(url_for("anasayfa"))
            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("giriş"))
        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor...","danger")
            redirect(url_for("giriş"))
            

    return render_template("giriş.html",form=form)

@app.route("/kontrol")
@login_required
def kontrol():
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM articles where author=%s"

    result=cursor.execute(sorgu,(session["username"],))

    if result>0:
        articles=cursor.fetchall()
        return render_template("kontrol.html",articles=articles)
    else: 
        return render_template("kontrol.html")

@app.route("/hakkımızda")
def hakkımızda():
    return render_template("hakkımızda.html")

@app.route("/makaleler/<string:id>")
def makale(id):
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM articles where id=%s"

    result=cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        return render_template("makale.html",article=article)  
    else:
        return render_template("makale.html")  

@app.route("/makaleler")
def makaleler():
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM articles"

    result=cursor.execute(sorgu)
    
    if result>0:
        makaleler=cursor.fetchall()
    
        return render_template("makaleler.html",makaleler=makaleler)
    else:
        return render_template("makaleler.html")

@app.route("/çıkış")
def çıkış():
    session.clear()
    return redirect(url_for("anasayfa"))

@app.route("/makaleekle",methods=["GET","POST"])
def makaleekle():   
    form=MakaleFormu(request.form)

    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()
        sorgu="INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        
        cursor=mysql.connection.cursor()
        sorgu="SELECT * FROM articles where author=%s"

        result=cursor.execute(sorgu,(session["username"],))
        
        flash("Makaleniz Başarıyla Eklendi","success")      
        articles=cursor.fetchall()
        if result>0:
            
            cursor.close()
            return render_template("kontrol.html",articles=articles)
        else: 
            return render_template("kontrol.html")



        

        

    return render_template("makaleekle.html",form=form)

@app.route("/sil/<string:id>")
@login_required
def sil(id):
    cursor=mysql.connection.cursor()
    sorgu="SELECT * FROM articles where author=%s and id=%s"

    result=cursor.execute(sorgu,(session["username"],id))
    
    if result>0:
        sorgu="DELETE FROM articles where id=%s"
        cursor.execute(sorgu,(id,))

        mysql.connection.commit()
        return redirect(url_for("kontrol"))
    else:
        flash("Böyle Bir Makale Yok veya Bu Makaleyi Silme Yetkiniz Yok...","danger")
        return redirect(url_for("anasayfa"))


@app.route("/düzenle/<string:id>",methods=["GET","POST"])
@login_required
def düzenle(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="SELECT * FROM articles where id=%s and author=%s"

        result=cursor.execute(sorgu,(id,session["username"]))
        
        if result>0:
            article=cursor.fetchone()
            form=MakaleFormu()

            form.title.data=article["title"]
            form.content.data=article["content"]

            return render_template("güncelle.html",form=form)
        else:
            flash("Böyle Bir Makale Yok veya Bu işleme Yetkiniz Yok")
            return redirect(url_for("anasayfa"))

    else:
        form=MakaleFormu(request.form)
        newTitle=form.title.data
        newContent=form.content.data

        sorgu2="UPDATE articles SET title=%s,content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()
        flash("Makale Başarıyla Güncellendi...","success")
        return redirect(url_for("kontrol"))

@app.route("/search", methods=["GET","POST"])
def ara():
    if request.method=="GET": 
        return redirect(url_for("anasayfa"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="SELECT * FROM articles where title like '%" +keyword +"%'"

        result=cursor.execute(sorgu)

        if result>0:
            articles=cursor.fetchall()
            return render_template("makaleler.html",makaleler=articles)
        else:
            flash("Aradığınız Kelimeye Uygun Makale Bulunamadı...","warning")
            return redirect(url_for("makaleler")) 
if(__name__=="__main__"):
    app.run(debug=True)

   