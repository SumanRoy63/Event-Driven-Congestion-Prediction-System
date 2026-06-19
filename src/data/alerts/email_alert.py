import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_alert(
    subject,
    message,
    receiver_email
):

    sender_email = "roysuman892749@gmail.com"

    app_password = "tucd slas dflt dchr"

    msg = MIMEMultipart()

    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(
        MIMEText(
            message,
            "plain"
        )
    )

    try:

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

        print(
            "Email Sent Successfully"
        )

    except Exception as e:

        print(
            "Email Error:",
            e
        )