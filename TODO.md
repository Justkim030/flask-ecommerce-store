# TODO: Implement Email Feedback for Login/Register

## Current Work
- User confirmed to proceed with adding email feedback for login and register attempts.
- This involves: Adding email to User model, updating registration form/route, installing/configuring Flask-Mail, and sending emails on success (welcome for register, login notification for login).

## Key Technical Concepts
- Flask-Mail for email sending.
- SQLAlchemy model update (add email column to User).
- Environment variables for SMTP config (.env).
- Flash messages remain for UI, emails added for backend notification.

## Relevant Files and Code
- ANORLD/app.py: Update User model, register/login routes, add Flask-Mail config and send functions.
- ANORLD/templates/register.html: Add email input field to form.
- ANORLD/requirements.txt: Add Flask-Mail.
- ANORLD/.env: Add SMTP placeholders (user to fill: MAIL_SERVER=smtp.gmail.com, MAIL_PORT=587, MAIL_USERNAME=your_email@gmail.com, MAIL_PASSWORD=your_app_password).

## Problem Solving
- Database migration: Adding email to existing User table. For dev (SQLite), run `flask init-db` to recreate DB (loses data; backup if needed). In production, use Alembic.
- SMTP: Using placeholders; user must provide real credentials (e.g., Gmail app password) to avoid errors.
- Email content: Simple text emails for now; can enhance with HTML later.

## Pending Tasks and Next Steps
1. [x] Update User model in app.py to add email field (unique, nullable=False).
   - In init_database(), ensure db.create_all() handles it.
   - Quote: "Add email to User model and registration form"

2. [x] Edit register.html to add email input in the form.
   - Place after username, before password.

3. [x] Update register route in app.py:
   - Collect email from form.
   - Validate (required, unique).
   - Store in new_user.email.
   - On success, send welcome email using Flask-Mail.
   - Note: Email collection, validation, storage, and sending complete.

4. [x] Add Flask-Mail configuration in app.py:
   - Import Flask-Mail.
   - Config from .env (MAIL_SERVER, etc.).
   - Initialize mail = Mail(app).

5. [x] Update login route in app.py:
   - On success, send login notification email (fetch user.email).

6. [x] Add email sending functions:
   - Def send_welcome_email(email, username).
   - Def send_login_notification(email, username).
   - Use mail.send() with Message.

7. [x] Update requirements.txt: Add Flask-Mail==0.9.1.

8. [ ] Followup steps:
   - [x] Install: `pip install -r requirements.txt`
   - [ ] Add SMTP to .env (user action).
   - [x] Recreate DB: `flask init-db` (if needed).
   - [ ] Test: Register new user (check email), login (check email).
   - [ ] Verify no errors in terminal.

Proceed step-by-step, confirming each tool use.
