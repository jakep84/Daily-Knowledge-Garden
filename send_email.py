import os, sys, smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

# Load .env locally; safe no-op in Actions
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def main():
    if len(sys.argv) != 3:
        print("Usage: send_email.py <subject_file> <html_file>")
        sys.exit(2)

    subject_path, html_path = sys.argv[1], sys.argv[2]
    subject = open(subject_path, "r", encoding="utf-8").read().strip()
    html = open(html_path, "r", encoding="utf-8").read()

    username = os.getenv("SMTP_USERNAME")  # e.g., your full Gmail address
    password = os.getenv("SMTP_PASSWORD")  # Gmail App Password
    from_email = os.getenv("FROM_EMAIL", username)
    to_email = os.getenv("TO_EMAIL", "priddyjacob84@gmail.com")

    if not (username and password and to_email):
        print("Missing SMTP_USERNAME / SMTP_PASSWORD / TO_EMAIL env vars.")
        sys.exit(3)

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Daily Knowledge Garden", from_email))
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo()
        s.starttls()
        s.login(username, password)
        s.sendmail(from_email, [to_email], msg.as_string())

    print("[email] Sent OK.")

if __name__ == "__main__":
    main()
