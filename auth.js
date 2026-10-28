/**
 * CEMS Static Demo Route Guard & Authentication Helper
 */
(function () {
    var raw = sessionStorage.getItem("cems_user");
    var user = null;
    try {
        user = raw ? JSON.parse(raw) : null;
    } catch (e) {
        user = null;
    }

    var path = window.location.pathname;
    var file = path.substring(path.lastIndexOf("/") + 1) || "index.html";

    // 1. If on login.html, authenticated users skip to their dashboard
    if (file === "login.html") {
        if (user && user.role) {
            window.location.replace(user.role === "admin" ? "admin.html" : "student.html");
        }
        return;
    }

    // 2. Unauthenticated users cannot access any internal page
    if (!user || !user.role) {
        window.location.replace("login.html");
        return;
    }

    // 3. index.html routes to the appropriate dashboard
    if (file === "" || file === "index.html") {
        window.location.replace(user.role === "admin" ? "admin.html" : "student.html");
        return;
    }

    // 4. Role Isolation Guards:
    // Students cannot access admin pages
    if (file.indexOf("admin") !== -1 && user.role !== "admin") {
        window.location.replace("student.html");
        return;
    }

    // Admins cannot access student pages
    if (file.indexOf("student") !== -1 && user.role !== "student") {
        window.location.replace("admin.html");
        return;
    }
})();

function getCurrentUser() {
    try {
        var raw = sessionStorage.getItem("cems_user");
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function signOut() {
    sessionStorage.removeItem("cems_user");
    window.location.replace("login.html");
}

