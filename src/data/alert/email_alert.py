import smtplib
from email.mime.text import MIMEText


def send_email_alert(
    subject,
    body,
    receiver_email
):

    sender_email = "roysuman892749@gmail.com"

    app_password = "jsrn vsvi zoer mvtz"

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        sender_email,
        app_password
    )

    server.send_message(msg)

    server.quit()