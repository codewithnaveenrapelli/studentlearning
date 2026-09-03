from flask import (
    Flask, render_template, request, redirect, url_for, flash, session,
    send_from_directory, abort,
)
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, Category, Resource, CATEGORY_SEED, CATEGORY_ICONS, CATEGORY_COLORS
from forms import (
    RegisterForm, LoginForm, ResourceForm, ChangePasswordForm,
    ForgotPasswordForm, ResetPasswordForm, EditProfileForm,
)
import os
import uuid
import mimetypes
from datetime import datetime, timedelta

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

RESOURCES_PER_PAGE = 12


def create_app(config_overrides=None):
    app = Flask(__name__, template_folder="template", static_folder="static")
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
    db.init_app(app)
    csrf.init_app(app)

    # Disabled under pytest/TESTING so repeated test requests never get
    # throttled; real usage still gets brute-force protection on /auth.
    app.config.setdefault("RATELIMIT_ENABLED", not app.config.get("TESTING", False))
    limiter.init_app(app)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    with app.app_context():
        db.create_all()

        if Category.query.count() == 0:
            for key, name in CATEGORY_SEED:
                db.session.add(Category(key=key, name=name, description=name))
            db.session.commit()

    # ── Helpers ──────────────────────────────────────────────────────

    def allowed_file(filename):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in app.config["ALLOWED_UPLOAD_EXTENSIONS"]

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        user = db.session.get(User, user_id)
        if user is None:
            # Session refers to a user that no longer exists (e.g. DB reset).
            session.clear()
        return user

    # Inject helpers into every template automatically.
    @app.context_processor
    def inject_globals():
        return {
            "user": current_user(),
            "category_icons": CATEGORY_ICONS,
            "category_colors": CATEGORY_COLORS,
        }

    # ── Public routes ────────────────────────────────────────────────

    @app.route("/")
    @app.route("/index")
    def index():
        latest_resources = Resource.query.order_by(Resource.created_at.desc()).limit(5).all()
        categories_list = Category.query.order_by(Category.name.asc()).all()
        return render_template("index.html", latest_resources=latest_resources, categories_list=categories_list)

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/categories")
    def categories():
        categories_list = Category.query.order_by(Category.name.asc()).all()
        return render_template("categories.html", categories_list=categories_list)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if name and email and subject and message:
                flash("Thank you for your message! We'll get back to you soon.", "success")
                return redirect(url_for("contact"))
            else:
                flash("Please fill in all required fields.", "danger")

        return render_template("contact.html")

    # ── Authentication ───────────────────────────────────────────────

    @app.route("/auth", methods=["GET", "POST"])
    @limiter.limit("10 per minute", methods=["POST"])
    def auth():
        login_form = LoginForm()
        register_form = RegisterForm()

        if request.method == "POST":
            if "register_submit" in request.form:
                if register_form.validate_on_submit():
                    email = register_form.email.data.strip().lower()
                    if User.query.filter_by(email=email).first():
                        flash("Email already exists.", "danger")
                    else:
                        user = User(
                            name=register_form.name.data.strip(),
                            email=email,
                            password=generate_password_hash(register_form.password.data),
                        )
                        db.session.add(user)
                        db.session.commit()
                        flash("Registration successful! Please log in.", "success")
                        return redirect(url_for("auth"))
            elif "login_submit" in request.form:
                if login_form.validate_on_submit():
                    email = login_form.email.data.strip().lower()
                    user = User.query.filter_by(email=email).first()
                    if user and check_password_hash(user.password, login_form.password.data):
                        session["user_id"] = user.id
                        session["user_name"] = user.name
                        session["user_role"] = user.role
                        flash("Login successful!", "success")
                        return redirect(url_for("dashboard"))
                    flash("Invalid email or password.", "danger")

        return render_template("auth.html", login_form=login_form, register_form=register_form)

    # ── Forgot / Reset Password (simulated — no email sent) ─────────

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        form = ForgotPasswordForm()
        reset_link = None

        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            user = User.query.filter_by(email=email).first()
            if user:
                token = uuid.uuid4().hex
                user.reset_token = token
                user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
                db.session.commit()
                # Simulated: show the link on-screen instead of emailing it.
                reset_link = url_for("reset_password", token=token, _external=True)
                flash("Reset link generated! Copy the link below to reset your password.", "success")
            else:
                # Don't reveal whether the email exists.
                flash("If that email is registered, a reset link has been generated.", "info")

        return render_template("forgot_password.html", form=form, reset_link=reset_link)

    @app.route("/reset-password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        user = User.query.filter_by(reset_token=token).first()
        if not user or (user.reset_token_expires and user.reset_token_expires < datetime.utcnow()):
            flash("Invalid or expired reset link.", "danger")
            return redirect(url_for("forgot_password"))

        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.password = generate_password_hash(form.new_password.data)
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            flash("Password reset successful! Please log in with your new password.", "success")
            return redirect(url_for("auth"))

        return render_template("reset_password.html", form=form, token=token)

    # ── Resources ────────────────────────────────────────────────────

    @app.route("/resources")
    def resources():
        search_query = request.args.get("search", "").strip()
        category_key = request.args.get("category", "").strip()
        page = request.args.get("page", 1, type=int)
        if page < 1:
            page = 1

        query = Resource.query
        if search_query:
            like_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(Resource.title.ilike(like_pattern), Resource.description.ilike(like_pattern))
            )
        if category_key:
            query = query.join(Category).filter(Category.key == category_key)
        query = query.order_by(Resource.created_at.desc())

        total_count = query.count()
        total_pages = max(1, (total_count + RESOURCES_PER_PAGE - 1) // RESOURCES_PER_PAGE)
        page = min(page, total_pages)
        resources_list = query.offset((page - 1) * RESOURCES_PER_PAGE).limit(RESOURCES_PER_PAGE).all()

        return render_template(
            "resources.html",
            resources_list=resources_list,
            search_query=search_query,
            selected_category=category_key,
            categories_list=Category.query.order_by(Category.name.asc()).all(),
            page=page,
            total_pages=total_pages,
        )

    @app.route("/resource/<int:resource_id>")
    def resource(resource_id):
        user = current_user()
        if user is None:
            flash("Please login to view resource details.", "warning")
            return redirect(url_for("auth"))
        resource_item = db.session.get(Resource, resource_id)
        if resource_item is None:
            abort(404)
        return render_template("resource.html", resource=resource_item)

    @app.route("/resource/<int:resource_id>/download")
    def download_resource(resource_id):
        if current_user() is None:
            flash("Please login to download resources.", "warning")
            return redirect(url_for("auth"))
        resource_item = db.session.get(Resource, resource_id)
        if resource_item is None:
            abort(404)
        upload_dir = os.path.join(app.root_path, "static", "uploads")
        return send_from_directory(
            upload_dir, resource_item.stored_file_name,
            as_attachment=True, download_name=resource_item.file_name,
        )

    @app.route("/resource/<int:resource_id>/preview")
    def preview_resource(resource_id):
        if current_user() is None:
            flash("Please login to preview resources.", "warning")
            return redirect(url_for("auth"))
        resource_item = db.session.get(Resource, resource_id)
        if resource_item is None:
            abort(404)
        mime_type = mimetypes.guess_type(resource_item.file_name)[0] or "application/octet-stream"
        return send_from_directory(
            os.path.join(app.root_path, "static", "uploads"),
            resource_item.stored_file_name,
            mimetype=mime_type,
            as_attachment=False,
        )

    @app.route("/resource/<int:resource_id>/delete", methods=["POST"])
    def delete_resource(resource_id):
        user = current_user()
        if user is None:
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth"))

        resource_item = db.session.get(Resource, resource_id)
        if resource_item is None:
            abort(404)

        if resource_item.uploaded_by != user.id and user.role != "admin":
            abort(403)

        upload_dir = os.path.join(app.root_path, "static", "uploads")
        file_path = os.path.join(upload_dir, resource_item.stored_file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.session.delete(resource_item)
        db.session.commit()
        flash("Resource deleted.", "success")

        return redirect(url_for("admin") if user.role == "admin" else url_for("dashboard"))

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        user = current_user()
        if user is None:
            flash("Please login to upload a resource.", "warning")
            return redirect(url_for("auth"))

        form = ResourceForm()
        if form.validate_on_submit():

            file = request.files.get("resource_file")
            original_filename = secure_filename(file.filename) if file and file.filename else ""
            if not original_filename:
                flash("Please choose a file to upload.", "danger")
                return render_template("upload.html", form=form)

            if not allowed_file(original_filename):
                flash("That file type is not allowed.", "danger")
                return render_template("upload.html", form=form)

            ext = original_filename.rsplit(".", 1)[-1].lower()
            stored_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_dir = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, stored_filename))

            category = Category.query.filter_by(key=form.category.data).first()
            if category is None:
                category = Category(
                    key=form.category.data,
                    name=form.category.data.title(),
                    description=form.category.data,
                )
                db.session.add(category)
                db.session.commit()

            resource_item = Resource(
                title=form.title.data.strip(),
                description=form.description.data.strip(),
                file_name=original_filename,
                stored_file_name=stored_filename,
                file_path=os.path.join("static", "uploads", stored_filename),
                category_id=category.id,
                uploaded_by=user.id,
            )
            db.session.add(resource_item)
            db.session.commit()
            flash("Resource uploaded successfully!", "success")
            return redirect(url_for("dashboard"))

        return render_template("upload.html", form=form)

    # ── Dashboard & Account ──────────────────────────────────────────

    @app.route("/dashboard")
    def dashboard():
        user = current_user()
        if user is None:
            return redirect(url_for("auth"))

        user_resources = Resource.query.filter_by(uploaded_by=user.id).order_by(Resource.created_at.desc()).all()
        password_form = ChangePasswordForm()
        profile_form = EditProfileForm(obj=user)
        return render_template(
            "dashboard.html", user_resources=user_resources,
            password_form=password_form, profile_form=profile_form,
        )

    @app.route("/account/password", methods=["POST"])
    def change_password():
        user = current_user()
        if user is None:
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth"))

        password_form = ChangePasswordForm()
        if password_form.validate_on_submit():
            if not check_password_hash(user.password, password_form.current_password.data):
                flash("Current password is incorrect.", "danger")
            else:
                user.password = generate_password_hash(password_form.new_password.data)
                db.session.commit()
                flash("Password changed successfully.", "success")
        else:
            for error_messages in password_form.errors.values():
                for error_message in error_messages:
                    flash(error_message, "danger")

        return redirect(url_for("dashboard"))

    @app.route("/account/profile", methods=["POST"])
    def edit_profile():
        user = current_user()
        if user is None:
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth"))

        form = EditProfileForm()
        if form.validate_on_submit():
            new_email = form.email.data.strip().lower()
            # Check if new email is taken by another user.
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != user.id:
                flash("That email is already in use.", "danger")
            else:
                user.name = form.name.data.strip()
                user.email = new_email
                session["user_name"] = user.name
                db.session.commit()
                flash("Profile updated successfully.", "success")
        else:
            for error_messages in form.errors.values():
                for msg in error_messages:
                    flash(msg, "danger")

        return redirect(url_for("dashboard"))

    # ── Admin ────────────────────────────────────────────────────────

    @app.route("/admin")
    def admin():
        user = current_user()
        if user is None or user.role != "admin":
            return redirect(url_for("auth"))

        page = request.args.get("page", 1, type=int)
        if page < 1:
            page = 1

        resources_query = Resource.query.order_by(Resource.created_at.desc())
        total_count = resources_query.count()
        total_pages = max(1, (total_count + RESOURCES_PER_PAGE - 1) // RESOURCES_PER_PAGE)
        page = min(page, total_pages)
        resources_list = resources_query.offset((page - 1) * RESOURCES_PER_PAGE).limit(RESOURCES_PER_PAGE).all()

        users = User.query.order_by(User.created_at.desc()).all()
        categories_list = Category.query.order_by(Category.id.asc()).all()
        return render_template(
            "admin.html", resources_list=resources_list, users=users, categories=categories_list,
            total_resource_count=total_count, page=page, total_pages=total_pages,
        )

    @app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
    def delete_user(user_id):
        admin = current_user()
        if admin is None or admin.role != "admin":
            abort(403)

        target = db.session.get(User, user_id)
        if target is None:
            abort(404)
        if target.id == admin.id:
            flash("You cannot delete your own account.", "danger")
            return redirect(url_for("admin"))

        # Delete user's uploaded files from disk.
        upload_dir = os.path.join(app.root_path, "static", "uploads")
        for res in target.resources:
            file_path = os.path.join(upload_dir, res.stored_file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(res)

        db.session.delete(target)
        db.session.commit()
        flash(f"User '{target.name}' and their resources have been deleted.", "success")
        return redirect(url_for("admin"))

    # ── Logout ───────────────────────────────────────────────────────

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("auth"))

    # ── Error handlers ───────────────────────────────────────────────

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template(
            "error.html", code=404,
            title="Page Not Found", message="The page you're looking for doesn't exist.",
        ), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template(
            "error.html", code=403,
            title="Access Forbidden", message="You don't have permission to do that.",
        ), 403

    @app.errorhandler(429)
    def rate_limited_error(error):
        return render_template(
            "error.html", code=429,
            title="Too Many Attempts", message="Please wait a bit before trying again.",
        ), 429

    @app.errorhandler(500)
    def server_error(error):
        return render_template(
            "error.html", code=500,
            title="Something Went Wrong", message="An unexpected error occurred. Please try again.",
        ), 500

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
