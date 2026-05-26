import streamlit as st
import sqlite3
import random
import yagmail

st.markdown("""
<style>
body {
    background-color: #000;
}
.card {
    background: linear-gradient(135deg,#1f1f1f,#2c2c2c);
    padding:20px;
    border-radius:15px;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Wallet App", layout="centered")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

# USERS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT,
    balance INTEGER
)
""")

# TRANSACTION TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    amount INTEGER,
    status TEXT
)
""")

conn.commit()

# ---------------- FUNCTIONS ----------------
import yagmail

def send_email_otp(receiver_email, otp):
    sender_email = "yourgmail@gmail.com"
    app_password = "your_app_password"

    yag = yagmail.SMTP(sender_email, app_password)

    yag.send(
        to=receiver_email,
        subject="Your OTP Code",
        contents=f"Your OTP is {otp}"
    )

def register_user(email, password):
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (email, password, 1000))
        conn.commit()
        return True
    except:
        return False

def check_user(email, password):
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def get_balance(email):
    c.execute("SELECT balance FROM users WHERE email=?", (email,))
    result = c.fetchone()
    return result[0] if result else 0

def update_balance(email, amount):
    c.execute("UPDATE users SET balance=? WHERE email=?", (amount, email))
    conn.commit()

def save_transaction(sender, receiver, amount, status):
    c.execute(
        "INSERT INTO transactions (sender, receiver, amount, status) VALUES (?, ?, ?, ?)",
        (sender, receiver, amount, status)
    )
    conn.commit()

# ✅ FRAUD CHECK FUNCTION
def fraud_check(amount):
    return amount > 5000


# ---------------- LOGIN ----------------
def login():
    st.title("💳 Wallet Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    # REGISTER
    with col1:
        if st.button("Register"):
            if register_user(email, password):
                st.success("Registered successfully ✅")
            else:
                st.warning("User already exists ⚠️")

    # SEND OTP
    with col2:
        if st.button("Send OTP"):
            user = check_user(email, password)
            if user:
                otp = random.randint(1000, 9999)
                st.session_state["otp"] = otp
                st.session_state["email"] = email
                st.session_state["otp_sent"] = True
                send_email_otp(email, otp)
                st.success("OTP sent to your email 📩")
            else:
                st.error("Invalid credentials ❌")

    # VERIFY OTP
    if st.session_state.get("otp_sent"):
        user_otp = st.text_input("Enter OTP")

        if st.button("Verify OTP"):
            if str(user_otp) == str(st.session_state.get("otp")):
                st.session_state["logged_in"] = True
                st.success("Login successful ✅")
            else:
                st.error("Wrong OTP ❌")


# ---------------- DASHBOARD ----------------
def dashboard():
    email = st.session_state.get("email")
    balance = get_balance(email)

    st.title("💳 Dashboard")
    st.subheader("👤 Profile")

    st.write(f"Email: {email}")
    st.write(f"Balance: ₹{balance}")

    # ✅ GPay Style UI
    st.markdown(f"""
<div class='card'>
<h3>💰 Balance</h3>
<h1>₹{balance}</h1>
</div>
""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📤 Pay")

    with col2:
        st.button("📥 Request")

    with col3:
        st.button("📜 History")

    st.subheader("💸 Send Money")

    receiver = st.text_input("Receiver Email")
    amount = st.number_input("Amount", min_value=1)

    # ✅ FIXED SEND MONEY (NO ERRORS)
    if st.button("Send Money"):
        try:
            receiver_balance = get_balance(receiver)

            # FRAUD CHECK
            if fraud_check(amount):
                st.warning("⚠️ Fraud detected! Transaction blocked")
                save_transaction(email, receiver, amount, "Fraud Blocked")

            else:
                if balance >= amount:
                    update_balance(email, balance - amount)
                    update_balance(receiver, receiver_balance + amount)

                    save_transaction(email, receiver, amount, "Success")
                    st.success("Money Sent ✅")

                else:
                    save_transaction(email, receiver, amount, "Failed")
                    st.error("Insufficient balance ❌")

        except:
            st.error("Receiver not found ❌")

    # TRANSACTION HISTORY
    st.subheader("📜 Transactions")
    c.execute(
        "SELECT sender, receiver, amount, status FROM transactions WHERE sender=? OR receiver=?",
        (email, email)
    )
    data = c.fetchall()

    for row in data:
        for sender, receiver, amount, status in data:
            st.markdown(f"""
    <div class='card'>
    <b>{sender}</b> → <b>{receiver}</b><br>
    ₹{amount} <br>
    Status: {status}
    </div>
    """, unsafe_allow_html=True)

    # LOGOUT
    if st.button("Logout"):
        st.session_state.clear()


# ---------------- MAIN ----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    dashboard()
else:
    login()