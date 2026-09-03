/* ══════════════════════════════════════════════════════════
   StudentLearningHub — Interactive JavaScript
   ══════════════════════════════════════════════════════════ */

// ── DOMContentLoaded ────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    initHamburgerMenu();
    initAutoToasts();
    initScrollAnimations();
});


// ── Hamburger Menu Toggle ───────────────────────────────

function initHamburgerMenu() {
    const toggle = document.getElementById('hamburger-toggle');
    const navCollapse = document.getElementById('nav-collapse');

    if (!toggle || !navCollapse) return;

    toggle.addEventListener('click', function () {
        toggle.classList.toggle('active');
        navCollapse.classList.toggle('open');
    });

    // Close menu when clicking a nav link (mobile).
    navCollapse.querySelectorAll('.main-nav a').forEach(function (link) {
        link.addEventListener('click', function () {
            toggle.classList.remove('active');
            navCollapse.classList.remove('open');
        });
    });

    // Close menu on outside click.
    document.addEventListener('click', function (e) {
        if (!toggle.contains(e.target) && !navCollapse.contains(e.target)) {
            toggle.classList.remove('active');
            navCollapse.classList.remove('open');
        }
    });
}


// ── Auto-dismiss Toast Notifications ────────────────────

function initAutoToasts() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(function (toast, index) {
        // Stagger entry animations.
        toast.style.animationDelay = (index * 0.1) + 's';

        // Auto-dismiss after 5 seconds.
        setTimeout(function () {
            toast.classList.add('toast-hide');
            setTimeout(function () {
                toast.remove();
                // Remove container if empty.
                const container = document.getElementById('toast-container');
                if (container && container.children.length === 0) {
                    container.remove();
                }
            }, 300);
        }, 5000 + (index * 500));
    });
}


// ── Scroll-triggered Animations ─────────────────────────

function initScrollAnimations() {
    if (!('IntersectionObserver' in window)) return;

    const elements = document.querySelectorAll('.animate-fade-up');
    // Reset initial state so the animation triggers on scroll.
    elements.forEach(function (el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(28px)';
        el.style.animation = 'none';
    });

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.style.animation = '';
                entry.target.style.opacity = '';
                entry.target.style.transform = '';
                entry.target.classList.add('animate-fade-up');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    elements.forEach(function (el) { observer.observe(el); });
}


// ── Auth Page: Login / Register Tab Switching ───────────

function showLogin() {
    var loginBox = document.getElementById("login-box");
    var registerBox = document.getElementById("register-box");
    var loginTab = document.getElementById("login-tab");
    var registerTab = document.getElementById("register-tab");

    if (loginBox) loginBox.style.display = "block";
    if (registerBox) registerBox.style.display = "none";
    if (loginTab) loginTab.classList.add("active");
    if (registerTab) registerTab.classList.remove("active");
}

function showRegister() {
    var loginBox = document.getElementById("login-box");
    var registerBox = document.getElementById("register-box");
    var loginTab = document.getElementById("login-tab");
    var registerTab = document.getElementById("register-tab");

    if (loginBox) loginBox.style.display = "none";
    if (registerBox) registerBox.style.display = "block";
    if (registerTab) registerTab.classList.add("active");
    if (loginTab) loginTab.classList.remove("active");
}


// ── Registration Validation ─────────────────────────────

function validateRegistration() {
    var name = document.getElementById("name");
    var email = document.getElementById("register-email");
    var password = document.getElementById("register-password");
    var confirmPassword = document.getElementById("confirm-password");

    if (name && name.value.trim() === "") {
        alert("Please enter your full name.");
        return false;
    }

    if (email && email.value.trim() === "") {
        alert("Please enter your email.");
        return false;
    }

    if (password && password.value.length < 6) {
        alert("Password must contain at least 6 characters.");
        return false;
    }

    if (password && confirmPassword && password.value !== confirmPassword.value) {
        alert("Passwords do not match.");
        return false;
    }

    return true;
}


// ── Login Validation ────────────────────────────────────

function validateLogin() {
    var email = document.getElementById("login-email");
    var password = document.getElementById("login-password");

    if (email && email.value.trim() === "") {
        alert("Please enter your email or username.");
        return false;
    }

    if (password && password.value === "") {
        alert("Please enter your password.");
        return false;
    }

    return true;
}