from flask import Flask, render_template , request,redirect,session,send_file 
from reportlab.pdfgen import canvas
import random
import smtplib 
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="airport_db"
)

def send_email(to_email, passenger_name, pnr,flight_name,from_city,to_city,departure_date,seat):

    sender_email = "skyportairlines9@gmail.com"
    app_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "SkyPort Flight Booking Confirmation"

    html = f"""
<html>
<body style="font-family: Arial; background-color:#f4f6f9; padding:20px;">

<div style="max-width:600px; margin:auto; background:white;
padding:20px; border-radius:10px;">

<h1 style="color:#0077cc; text-align:center;">
✈ SkyPort Airlines
</h1>

<h2 style="text-align:center; color:green;">
Booking Confirmed ✅
</h2>

<p>Hello <b>{passenger_name}</b>,</p>

<p>
Thank you for choosing <b>SkyPort Airlines</b>.
Your flight booking has been confirmed.
</p>

<hr>

<p><b>🎫 PNR:</b> {pnr}</p>
<p><b>Passenger:</b> {passenger_name}</p>
<p><b>Flight:</b> {flight_name}</p>
<p><b>Route:</b> {from_city} → {to_city}</p>
<p><b>Date:</b> {departure_date}</p>
<p><b>Seat:</b> {seat}</p>





<p>
We wish you a safe and pleasant journey.
</p>

<br>

<p style="color:gray;">
SkyPort Airlines Team ✈
</p>

</div>

</body>
</html>
"""
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender_email, app_password)

    server.send_message(msg)

    server.quit()

def send_cancel_email(to_email, passenger_name, pnr):

    sender_email = "skyportairlines9@gmail.com"
    app_password = "yoay mylb asiy junn"

    msg = MIMEMultipart()

    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "SkyPort Flight Cancellation"

    html = f"""
    <html>
    <body>

    <h2 style="color:red;">
    ❌ Flight Booking Cancelled
    </h2>

    <p>Hello <b>{passenger_name}</b>,</p>

    <p>
    Your booking has been cancelled successfully.
    </p>

    <p>
    <b>PNR:</b> {pnr}
    </p>

    <p>
    Refund will be processed as per airline policy.
    </p>

    <br>

    <p>
    SkyPort Airlines Team ✈️
    </p>

    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender_email, app_password)

    server.send_message(msg)

    server.quit()

@app.route('/') #/= jub user website kholega ye page open ho ga
def home():
    return render_template("index.html") #homepage open hone par index.html show hoga

@app.route('/register', methods=['GET', 'POST'])
def register():
    

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        cursor = db.cursor()

        query = """
        INSERT INTO users (name, email, phone, password)
        VALUES (%s, %s, %s, %s)
        """

        values = (name, email, phone, password)

        cursor.execute(query, values)
        db.commit()

        return redirect('/login')

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        query = "SELECT * FROM users WHERE email=%s AND password=%s"
        values = (email, password)

        cursor.execute(query, values)

        user = cursor.fetchone()

        if user:
            session['email'] = email
            if email =="admin@gmail.com":
                session['admin']=True
                return redirect('/admin')
            print("Login email",session.get('email'))
            return redirect('/dashboard')
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM bookings")

    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")

    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback")

    total_feedback = cursor.fetchone()[0]

    
    return render_template(
        "dashboard.html",
        total_bookings=total_bookings,
        total_users=total_users,
        total_feedback=total_feedback
    )


@app.route('/search', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':
        

        source = request.form['source']
        destination = request.form['destination']
    
        

        cursor = db.cursor()

        query = """
        SELECT * FROM flights
        WHERE source=%s AND destination=%s
        """

        cursor.execute(query, (source, destination))

        flights = cursor.fetchall()

        return render_template("results.html",flights=flights)

    return render_template("search.html")

@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):

    cursor = db.cursor()

    query = "SELECT * FROM flights WHERE id=%s"
    cursor.execute(query, (flight_id,))
    flight = cursor.fetchone()

    if request.method == 'POST':

        passenger_count = request.form['passenger_count']
        class_type = request.form['class_type']

        return render_template("passenger_details.html",
passenger_count=int(passenger_count),class_type=class_type,flight=flight)

    return render_template("booking_form.html",flight=flight)

@app.route('/seat-selection', methods=['POST'])
def seat_selection():

    passenger_count = int(request.form['passenger_count'])
    class_type = request.form['class_type']
    flight_name = request.form.get('flight_name','unknown flight')
    from_city = request.form.get('from_city','N/A')
    to_city = request.form.get('to_city','N/A')
    departure_date = request.form.get('departure_date')
    price = request.form.get('price')

    price = int(price)
    if class_type == "Premium Economy":
        price+=2000
    elif class_type== "Business":
        price+=5000
    elif class_type=="First Class":
        price+=10000

    if class_type=="First Class":
        seats=["1A","1B","1C","1D","2A","2B","2C","2D"]
    elif class_type=="Business":
        seats=["3A","3B","3C","3D","4A","4B","4C","4D","5A","5B","5C","5D"]
    elif class_type=="Premium Economy":
        seats=["6A","6B","6C","6D","6E","6F","7A","7B","7C","7D","7E","7F"]
    else:
        seats=["8A","8B","8C","8D","8E","8F","9A","9B","9C","9D","9E","9F","10A","10B","10C","10D","10E","10F"]

    print(request.form)
    passengers=[]
    for i in range(passenger_count):
        passengers.append(request.form[f'passenger_name_{i}'])
        print("seat page passengers=",passengers)
    cursor = db.cursor()

    cursor.execute(
            "SELECT seat_no FROM bookings WHERE flight_name=%s AND departure_date=%s",
            (flight_name, departure_date)
    
)


    booked_seats = [row[0] for row in cursor.fetchall()]
    
    return render_template(
            "seat_selection.html",
            passenger_count=passenger_count,
            class_type=class_type,
            passengers=passengers,
            flight_name=flight_name,
            from_city=from_city,
            to_city=to_city,
            departure_date=departure_date,
            price=price,
            booked_seats=booked_seats,
            seats=seats
    )

@app.route('/payment', methods=['POST'])
def payment():
    print("passenger count=",request.form.get("passenger_count"))
    print(request.form)


    seats = []
    for i in range(int(request.form.get("passenger_count"))):
        seats.append(request.form.get(f"seat_{i}"))
        price= int(request.form.get("price"))
        price=price*int(request.form.get("passenger_count"))

    return render_template(
        "payment.html",
        flight_name=request.form.get("flight_name"),
        from_city=request.form.get("from_city"),
        to_city=request.form.get("to_city"),
        class_type=request.form.get("class_type"),
        departure_date=request.form.get("departure_date"),
        price=price,
        passengers=request.form.get("passengers"),
        passenger_count=request.form.get("passenger_count"),
        seats=seats,
    )
@app.route('/payment-success', methods=['POST'])
def payment_success():
    seats=[]
    for i in range(int(request.form.get("passenger_count"))):
        seats.append(request.form.get(f"seat_{i}"))
    
    return render_template(
        "payment-success.html",
        flight_name=request.form.get("flight_name"),
        from_city=request.form.get("from_city"),
        to_city=request.form.get("to_city"),
        class_type=request.form.get("class_type"),
        departure_date=request.form.get("departure_date"),
        price=request.form.get("price"),
        passengers=request.form.get("passengers"),
        payment_method=request.form.get("payment_method"),
        seats=seats
    )

@app.route('/final-ticket', methods=['GET','POST'])
def final_ticket():
    print("SESSION =", dict(session))
    print("Final Ticket")
    print("Email=",session.get("email"))
    
    flight_name = request.form.get("flight_name")
    from_city = request.form.get("from_city")
    to_city = request.form.get("to_city")
    class_type = request.form.get("class_type")
    departure_date = request.form.get("departure_date")
    price = request.form.get("price")
    passengers = request.form.get("passengers")
    price=int(price)
    passenger_list=eval(passengers)
    price=price*len(passenger_list)
    payment_method=request.form.get("payment_method")
    print("PAYMENT METHOD=",payment_method)
    print("PASSENGERS=",passengers)
    print("seat_0=",request.form.get("seat_0"))
    print("seat_1=",request.form.get("seat_1"))
    print("PASSENGER LIST=",passenger_list)
    ticket_passengers = ""
    seat_list=[]

    for i in range(len(passenger_list)):
        seat = request.form.get(f"seat_{i}")
        print("seat=",seat)
        seat_list.append(seat)
    seat_numbers=", ".join(seat_list)
    

    ticket_passengers += f"""
        <div class="row">
        Passenger {i+1} : {passenger_list[i]}
        </div>

        <div class="row">
        Seat : {seat}
        </div>

        <br>
        """
    
    seat=request.form.get("seat_0")
    

    pnr="SKY"+ str(random.randint(10000,99999))
    print(session)
    print("EMAIL =", session.get('email'))


    cursor=db.cursor()
    query = """
    INSERT INTO bookings
    (flight_name, source, destination,departure_date,price, passenger_name, email,seat_no,pnr,payment_method)
    VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s,%s)
    """
    print("SESSION=",session)
    print("EMAIL=",session.get("email"))
    cursor.execute(
    query,
    (
        flight_name,
        from_city,
        to_city,
        departure_date,
        price,
        ", ".join(passenger_list),
        session.get('email'),
        seat_numbers,
        pnr,
        payment_method
    )
)
    db.commit()
    print("Email=",session.get('email'))
    
    send_email(
        session.get('email'),
        ", ".join(passenger_list),
        pnr,
        flight_name,
        from_city,
        to_city,
        departure_date,
        seat
    )
    booking_id=cursor.lastrowid
    return redirect(f'/ticket/{booking_id}')
    return f"""
    <html>
    <head>
    <title>E-Ticket</title>
    <style>

    body{{
        font-family:Arial;
        background:linear-gradient(135deg,#001f54,#00c6ff);
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
    }}

    .ticket{{
        background:white;
        width:500px;
        padding:30px;
        border-radius:20px;
        box-shadow:0 10px 25px rgba(0,0,0,0.3);
    }}

    h1{{
        text-align:center;
        color:#003366;
    }}

    .row{{
        margin:15px 0;
        font-size:20px;
    }}

    </style>
    </head>

    <body>

    <div class="ticket">

    <h1>✈️ Flight Ticket</h1>

    <div class="row">
    Flight : {flight_name}
    </div>

    <div class="row">
    From : {from_city}
    </div>

    <div class="row">
    To : {to_city}
    </div>

    <div class="row">
    Class : {class_type}
    </div>

<br>

    {ticket_passengers}

    <div class="row">
    Status : Confirmed ✅
    </div>

    <div class="row">
    PNR : {pnr}
    </div>

    </div>

    </body>
    </html>
    """

@app.route('/mybookings')
def my_bookings():
    if 'email' not in session:
        return redirect('/login')

    cursor = db.cursor()

    cursor.execute("SELECT * FROM bookings WHERE email=%s",(session['email'],))

    bookings = cursor.fetchall()

    return render_template("mybookings.html", bookings=bookings)

@app.route('/cancel/<int:id>')
def cancel_booking(id):

    cursor = db.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id=%s", (id,))
    booking = cursor.fetchone()
    print(booking)
    send_cancel_email(booking[7],booking[6],booking[9])


    query = "DELETE FROM bookings WHERE id=%s"
    

    cursor.execute(query, (id,))
    print("EMAIL=",booking[7])

    db.commit()

    return redirect('/mybookings')

@app.route('/ticket/<int:id>')
def ticket(id):

    cursor = db.cursor()

    query = "SELECT * FROM bookings WHERE id=%s"

    cursor.execute(query, (id,))

    booking = cursor.fetchone()
    print(booking)

    return render_template('ticket.html', booking=booking)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/feedback', methods=['GET','POST'])
def feedback():

    if request.method == "POST":

        name = request.form['name']
        message = request.form['message']

        cursor = db.cursor()

        query = "INSERT INTO feedback(name, message) VALUES(%s, %s)"

        cursor.execute(query, (name, message))

        db.commit()

        return "Thank You For Your Feedback ❤️"

    return render_template('feedback.html')
@app.route('/viewfeedback')
def viewfeedback():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM feedback")

    feedbacks = cursor.fetchall()

    return render_template('viewfeedback.html', feedbacks=feedbacks)

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback")
    total_feedback = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM flights")
    total_flights=cursor.fetchone()[0]

    cursor.execute("SELECT * FROM bookings Limit 5")
    bookings=cursor.fetchall()



    return render_template(
        "admin.html",
        total_users=total_users,
        total_bookings=total_bookings,
        total_feedback=total_feedback,
        total_flights=total_flights,
        bookings=bookings
    )

@app.route('/manageflights')
def manage_flights():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM flights")

    flights = cursor.fetchall()

    return render_template(
        "manageflights.html",
        flights=flights
    )

@app.route('/deleteflight/<int:id>')
def deleteflight(id):

    cursor = db.cursor()

    cursor.execute("DELETE FROM flights WHERE id=%s", (id,))

    db.commit()

    return redirect('/manageflights')

@app.route('/editflight/<int:id>', methods=['GET', 'POST'])
def editflight(id):

    cursor = db.cursor()

    if request.method == 'POST':

        flight_name = request.form['flight_name']
        source = request.form['source']
        destination = request.form['destination']
        departure_date = request.form['departure_date']
        price = request.form['price']

        cursor.execute("""
        UPDATE flights
        SET flight_name=%s,
            source=%s,
            destination=%s,
            departure_date=%s,
            price=%s
        WHERE id=%s
        """, (flight_name, source, destination,
              departure_date, price, id))

        db.commit()

        return redirect('/manageflights')

    cursor.execute("SELECT * FROM flights WHERE id=%s", (id,))
    flight = cursor.fetchone()

    return render_template('editflight.html', flight=flight)

@app.route('/addflight', methods=['GET', 'POST'])
def addflight():

    if request.method == 'POST':

        flight_name = request.form['flight_name']
        source = request.form['source']
        destination = request.form['destination']
        departure_date = request.form['departure_date']
        price = request.form['price']

        cursor = db.cursor()

        cursor.execute("""
        INSERT INTO flights
        (flight_name, source, destination, departure_date, price)
        VALUES (%s, %s, %s, %s, %s)
        """, (flight_name, source, destination, departure_date, price))

        db.commit()

        return redirect('/manageflights')

    return render_template("addflight.html")


@app.route('/viewbookings')
def viewbookings():

    cursor = db.cursor()

    cursor.execute("SELECT * FROM bookings")

    bookings = cursor.fetchall()

    return render_template(
        "viewbookings.html",
        bookings=bookings
    )

@app.route('/deletebooking/<int:id>')
def deletebooking(id):

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM bookings WHERE id=%s",
        (id,)
    )

    db.commit()

    return redirect('/viewbookings')

@app.route('/download-pdf/<int:id>')
def download_pdf(id):
    cursor=db.cursor()
    query="SELECT * FROM bookings WHERE id=%s"
    cursor.execute(query,(id,))
    booking= cursor.fetchone()

    pdf = canvas.Canvas("ticket.pdf")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 800, "Flight Ticket")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, f"Flight: {booking[1]}")
    pdf.drawString(100, 720, f"From: {booking[2]}")
    pdf.drawString(100, 690, f"To: {booking[3]}")
    pdf.drawString(100, 660, f"Date: {booking[4]}")
    pdf.drawString(100, 630, f"Price: ₹{booking[5]}")
    pdf.drawString(100, 600, f"Passenger: {booking[6]}")
    pdf.drawString(100, 570, f"Seat: {booking[8]}")
    pdf.drawString(100, 540, f"PNR: {booking[9]}")
    pdf.drawString(100, 510, "Status: Confirmed")

    pdf.save()

    return send_file("ticket.pdf", as_attachment=True)

@app.route("/boarding-pass/<int:booking_id>")
def boarding_pass(booking_id):

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM bookings WHERE id=%s",
        (booking_id,)
    )

    booking = cursor.fetchone()
    qr_data=f"""
    PNR:{booking[9]}
    Passenger:{booking[6]}
    Seat:{booking[8]}
    Gate:A12
    Terminal:T1
    Boarding Time:8:30 Am
    """

    return render_template(
        "boarding-pass.html",
        booking=booking,
        gate="A12",
        terminal="T1",
        boarding_time="08:30 AM",
        qr_data=qr_data
    )

@app.route("/update-status/<int:booking_id>", methods=["POST"])
def update_status(booking_id):
    status = request.form.get("status")

    cursor = db.cursor()
    cursor.execute(
        "UPDATE bookings SET flight_status=%s WHERE id=%s",
        (status, booking_id)
    )
    db.commit()

    return redirect("/viewbookings")

@app.route('/generate-flights')
def generate_flights():

    cursor = db.cursor(buffered=True)

    cursor.execute("SELECT city_name FROM cities")
    cities = cursor.fetchall()

    for source in cities:
        for destination in cities:

            if source[0] != destination[0]:
                for day in range(1,31):
                    departure_date= f"2026-07-{day:02d}"

                    cursor.execute("""
                    SELECT id FROM flights
                    WHERE source=%s AND destination=%s AND departure_date=%s
                    """, (source[0], destination[0], departure_date))

                    existing = cursor.fetchone()

                    if existing:
                        continue

                    flight_name = f"SkyPort {source[0][:2]}{destination[0][:2]}"
                    cursor.execute("""
                    SELECT distance FROM routes
                    WHERE source=%s AND destination=%s
                    """, (source[0], destination[0]))

                    route = cursor.fetchone()

                    if route:
                        distance = route[0]
                        price = 2000 + (distance * 3)
                    else:
                        distance=random.randint(300,2500)
                        price=2000+(distance*3)


                    cursor.execute("""
                    INSERT INTO flights
                    (flight_name, source, destination, departure_date, price)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        flight_name,
                        source[0],
                        destination[0],
                        departure_date,
                        price
                    ))

    db.commit()

    return redirect('/manageflights')



if __name__ == "__main__":
    app.run(debug=True) #flask website ko run krna