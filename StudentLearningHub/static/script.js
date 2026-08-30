function showLogin() {

    document.getElementById("login-box").style.display = "block";

    document.getElementById("register-box").style.display = "none";

    document.getElementById("login-tab").classList.add("active");

    document.getElementById("register-tab").classList.remove("active");
}


function showRegister() {

    document.getElementById("login-box").style.display = "none";

    document.getElementById("register-box").style.display = "block";

    document.getElementById("register-tab").classList.add("active");

    document.getElementById("login-tab").classList.remove("active");
}

// Registration Validation

function validateRegistration() {

    let name = document.getElementById("name").value.trim();
    let email = document.getElementById("register-email").value.trim();
    let password = document.getElementById("register-password").value;
    let confirmPassword = document.getElementById("confirm-password").value;

    if (name === "") {
        alert("Please enter your full name.");
        return false;
    }

    if (email === "") {
        alert("Please enter your email.");
        return false;
    }

    if (password.length < 6) {
        alert("Password must contain at least 6 characters.");
        return false;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return false;
    }

    return true;
}

// Login Validation

function validateLogin() {

    let email = document.getElementById("login-email").value.trim();
    let password = document.getElementById("login-password").value;

    if (email === "") {
        alert("Please enter your email or username.");
        return false;
    }

    if (password === "") {
        alert("Please enter your password.");
        return false;
    }

    return true;
}