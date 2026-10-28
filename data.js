/**
 * CEMS Shared Data & State Management for Static Demo
 * Mirrors seed_data.py and sample_data.json
 */

const STORAGE_KEY_EVENTS = "cems_events_v1";
const STORAGE_KEY_REGS = "cems_registrations_v1";
const STORAGE_KEY_STUDENTS = "cems_students_v1";

const DEFAULT_STUDENTS = [
    {
        id: 1,
        username: "alice",
        name: "Alice Sharma",
        roll_no: "CS2026-001",
        department: "Computer Engineering",
        email: "alice@college.edu"
    },
    {
        id: 2,
        username: "bob",
        name: "Bob Patel",
        roll_no: "IT2026-014",
        department: "Information Technology",
        email: "bob@college.edu"
    },
    {
        id: 3,
        username: "charlie",
        name: "Charlie Gupta",
        roll_no: "AI2026-022",
        department: "Artificial Intelligence & Data Science",
        email: "charlie@college.edu"
    },
    {
        id: 4,
        username: "diana",
        name: "Diana Dsouza",
        roll_no: "EXTC2026-035",
        department: "Electronics & Telecommunication",
        email: "diana@college.edu"
    }
];

function getInitialEvents() {
    const today = new Date();
    const addDays = (d, n) => {
        const copy = new Date(d);
        copy.setDate(copy.getDate() + n);
        const y = copy.getFullYear();
        const m = String(copy.getMonth() + 1).padStart(2, "0");
        const day = String(copy.getDate()).padStart(2, "0");
        return `${y}-${m}-${day}`;
    };

    return [
        {
            id: 1,
            title: "AI & Machine Learning 24h Hackathon",
            category: "Technical",
            event_date: addDays(today, 10),
            venue: "Main Turing Auditorium & Lab 401",
            description: "24-hour flagship hackathon solving real-world challenges in GenAI, autonomous systems, and edge computing. Catering, Wi-Fi, and mentor support provided.",
            fee: 0,
            capacity: 60
        },
        {
            id: 2,
            title: "Aura 2026: Annual Cultural Fiesta",
            category: "Cultural",
            event_date: addDays(today, 18),
            venue: "Open Air Amphitheatre",
            description: "The campus's biggest cultural extravaganza featuring music battles, classical and modern dance competitions, theatrical plays, and star evening shows.",
            fee: 150,
            capacity: 150
        },
        {
            id: 3,
            title: "Inter-College 7-a-Side Football Cup",
            category: "Sports",
            event_date: addDays(today, 25),
            venue: "University Sports Complex Turf",
            description: "High-octane knockouts with teams from across state colleges. Official referees, live commentary, trophies, and cash prizes for champions.",
            fee: 50,
            capacity: 80
        },
        {
            id: 4,
            title: "Cloud Native & DevOps Hands-on Bootcamp",
            category: "Workshop",
            event_date: addDays(today, 14),
            venue: "Seminar Hall B & Hybrid Live Stream",
            description: "Deep-dive workshop on Docker containers, Kubernetes orchestrations, Terraform infrastructure-as-code, and GitHub Actions CI/CD pipelines.",
            fee: 99,
            capacity: 45
        },
        {
            id: 5,
            title: "Big Tech Career & System Design Seminar",
            category: "Seminar",
            event_date: addDays(today, 32),
            venue: "Executive Conference Hall 1",
            description: "Alumni keynote speakers from Google, Microsoft, and Uber discussing technical interviews, scalable system design, and open-source contributions.",
            fee: 0,
            capacity: 120
        },
        {
            id: 6,
            title: "Autonomous Drone & Robotics Expo (Past Edition)",
            category: "Workshop",
            event_date: addDays(today, -20),
            venue: "Robotics Lab & Indoor Field",
            description: "Hands-on flight controller programming and autonomous navigation demo. Successfully concluded with student showcase.",
            fee: 120,
            capacity: 40
        }
    ];
}

function getInitialRegistrations() {
    return [
        { id: 101, event_id: 1, user: "Alice Sharma", username: "alice", roll_no: "CS2026-001", department: "Computer Engineering", status: "registered", date: "2026-10-24 14:30" },
        { id: 102, event_id: 4, user: "Alice Sharma", username: "alice", roll_no: "CS2026-001", department: "Computer Engineering", status: "registered", date: "2026-10-25 09:15" },
        { id: 103, event_id: 1, user: "Bob Patel", username: "bob", roll_no: "IT2026-014", department: "Information Technology", status: "registered", date: "2026-10-24 15:00" },
        { id: 104, event_id: 2, user: "Bob Patel", username: "bob", roll_no: "IT2026-014", department: "Information Technology", status: "registered", date: "2026-10-26 10:20" },
        { id: 105, event_id: 1, user: "Charlie Gupta", username: "charlie", roll_no: "AI2026-022", department: "Artificial Intelligence & Data Science", status: "registered", date: "2026-10-24 16:45" },
        { id: 106, event_id: 3, user: "Charlie Gupta", username: "charlie", roll_no: "AI2026-022", department: "Artificial Intelligence & Data Science", status: "registered", date: "2026-10-26 11:30" },
        { id: 107, event_id: 4, user: "Charlie Gupta", username: "charlie", roll_no: "AI2026-022", department: "Artificial Intelligence & Data Science", status: "cancelled", date: "2026-10-25 18:00" },
        { id: 108, event_id: 2, user: "Diana Dsouza", username: "diana", roll_no: "EXTC2026-035", department: "Electronics & Telecommunication", status: "registered", date: "2026-10-26 14:10" },
        { id: 109, event_id: 5, user: "Diana Dsouza", username: "diana", roll_no: "EXTC2026-035", department: "Electronics & Telecommunication", status: "registered", date: "2026-10-27 09:50" },
        { id: 110, event_id: 6, user: "Alice Sharma", username: "alice", roll_no: "CS2026-001", department: "Computer Engineering", status: "registered", date: "2026-10-05 12:00" }
    ];
}

function parseLocalDate(dateStr) {
    if (!dateStr) return new Date();
    if (typeof dateStr === "string" && dateStr.includes("-")) {
        const parts = dateStr.split(" ")[0].split("-").map(Number);
        if (parts.length === 3) {
            return new Date(parts[0], parts[1] - 1, parts[2]);
        }
    }
    return new Date(dateStr);
}

function isPast(dateStr) {
    const d = parseLocalDate(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return d < today;
}

function formatDate(dateStr) {
    const d = parseLocalDate(dateStr);
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

function formatFee(fee) {
    const num = Number(fee);
    return isNaN(num) || num === 0 ? "Free" : `₹${Math.round(num)}`;
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getInitials(name) {
    if (!name) return "U";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
