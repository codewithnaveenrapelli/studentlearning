from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

# Single source of truth for the built-in categories: (key, display_name).
# Used to seed the Category table (app.py) and to build the upload form's
# <select> choices (forms.py) so the two never drift out of sync.
CATEGORY_SEED = [
    ("practical", "Practical Programs"),
    ("project", "Project Source Code"),
    ("seminar", "Seminar PPTs"),
    ("documentation", "Project Documentation"),
    ("coding", "Coding Practice"),
    ("interview", "Interview Preparation"),
    ("resume", "Resume Templates"),
    ("links", "Useful Learning Links"),
]

# Emoji icons for each category key (used in templates).
CATEGORY_ICONS = {
    "practical": "💻",
    "project": "🚀",
    "seminar": "📊",
    "documentation": "📄",
    "coding": "⌨️",
    "interview": "💡",
    "resume": "📝",
    "links": "🔗",
}

# Gradient CSS classes per category (used in templates).
CATEGORY_COLORS = {
    "practical": "cat-cyan",
    "project": "cat-blue",
    "seminar": "cat-purple",
    "documentation": "cat-green",
    "coding": "cat-orange",
    "interview": "cat-pink",
    "resume": "cat-yellow",
    "links": "cat-teal",
}


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Password-reset token (simulated — shown on-screen rather than emailed).
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    resources = db.relationship("Resource", back_populates="user", lazy=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    # Stable machine key used by <select> options / lookups (e.g. "practical").
    # Kept separate from the human-readable display name so renaming a
    # category never breaks category lookups or creates duplicate rows.
    key = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, default="")

    resources = db.relationship("Resource", back_populates="category", lazy=True)


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    stored_file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category", back_populates="resources")
    user = db.relationship("User", back_populates="resources")
