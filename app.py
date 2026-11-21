import os
import secrets
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from config import Config
from database import init_db
from models import (
    get_user_by_id,
    verify_user_login,
    create_outpass,
    get_outpass_by_id,
    get_outpass_by_token,
    get_outpass_by_code,
    get_student_outpasses,
    approve_outpass,
    reject_outpass,
    record_gate_exit,
    record_gate_entry,
    get_recent_gate_logs,
    get_all_movements,
    get_warden_kpis,
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    format_ist_display,
    format_time_only,
    get_now_ist_str,
    evaluate_late_status,
    get_all_students
)
from analyze_data import analyze_outpass_csv

def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure database is initialized on startup
    with app.app_context():
        init_db(app.config.get("DATABASE_PATH"))

    # ---------------------------------------------------------
    # Template Filters & Context Processors
    # ---------------------------------------------------------
    @app.template_filter("ist_date")
    def ist_date_filter(dt_str):
        return format_ist_display(dt_str)

    @app.template_filter("time_only")
    def time_only_filter(dt_str):
        return format_time_only(dt_str)

    @app.context_processor
    def inject_global_context():
        """Inject current authenticated user and unread notification count."""
        user = None
        unread_count = 0
        csrf_token = session.get("_csrf_token")
        if not csrf_token:
            csrf_token = secrets.token_hex(16)
            session["_csrf_token"] = csrf_token

        if "user_id" in session:
            user = get_user_by_id(session["user_id"], custom_path=app.config.get("DATABASE_PATH"))
            if user:
                unread_count = get_unread_notification_count(user["id"], custom_path=app.config.get("DATABASE_PATH"))
                
        return {
            "current_user": user,
            "unread_notifications_count": unread_count,
            "csrf_token": csrf_token,
            "campus_gates": Config.CAMPUS_GATES,
            "now_ist_str": get_now_ist_str()
        }

    # ---------------------------------------------------------
    # CSRF & Authorization Helpers
    # ---------------------------------------------------------
    def validate_csrf(token):
        expected = session.get("_csrf_token")
        return bool(expected and token and secrets.compare_digest(str(expected), str(token)))

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            return f(*args, **kwargs)
        return decorated

    def role_required(*allowed_roles):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if "user_id" not in session:
                    flash("Please log in to continue.", "warning")
                    return redirect(url_for("login"))
                user_role = session.get("role")
                if user_role not in allowed_roles:
                    flash("Unauthorized: You do not have permission to view that page.", "danger")
                    # Redirect to appropriate home for their role
                    if user_role == Config.ROLE_STUDENT:
                        return redirect(url_for("student_dashboard"))
                    elif user_role == Config.ROLE_WARDEN:
                        return redirect(url_for("warden_dashboard"))
                    elif user_role == Config.ROLE_GUARD:
                        return redirect(url_for("guard_dashboard"))
                    return redirect(url_for("login"))
                return f(*args, **kwargs)
            return decorated
        return decorator

    # ---------------------------------------------------------
    # Authentication Routes
    # ---------------------------------------------------------
    @app.route("/")
    def index():
        if "user_id" in session:
            role = session.get("role")
            if role == Config.ROLE_STUDENT:
                return redirect(url_for("student_dashboard"))
            elif role == Config.ROLE_WARDEN:
                return redirect(url_for("warden_dashboard"))
            elif role == Config.ROLE_GUARD:
                return redirect(url_for("guard_dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            # CSRF check
            form_csrf = request.form.get("csrf_token")
            if not validate_csrf(form_csrf):
                flash("Invalid security token. Please try again.", "danger")
                return redirect(url_for("login"))

            roll_or_user = request.form.get("roll_number", "").strip()
            password = request.form.get("password", "")

            user = verify_user_login(roll_or_user, password, custom_path=app.config.get("DATABASE_PATH"))
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["role"] = user["role"]
                session["name"] = user["name"]
                session["roll_number"] = user["roll_number"]
                session["gate_name"] = user.get("gate_name")
                session["_csrf_token"] = secrets.token_hex(16)

                flash(f"Welcome back, {user['name']}!", "success")
                if user["role"] == Config.ROLE_STUDENT:
                    return redirect(url_for("student_dashboard"))
                elif user["role"] == Config.ROLE_WARDEN:
                    return redirect(url_for("warden_dashboard"))
                elif user["role"] == Config.ROLE_GUARD:
                    return redirect(url_for("guard_dashboard"))
            else:
                flash("Invalid roll number/username or password. Check demo credentials below.", "danger")

        all_students = get_all_students(custom_path=app.config.get("DATABASE_PATH"))
        return render_template("login.html", all_students=all_students)

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been securely logged out.", "info")
        return redirect(url_for("login"))

    # ---------------------------------------------------------
    # Student Routes
    # ---------------------------------------------------------
    @app.route("/student/dashboard")
    @login_required
    @role_required(Config.ROLE_STUDENT)
    def student_dashboard():
        student_id = session["user_id"]
        outpasses = get_student_outpasses(student_id, custom_path=app.config.get("DATABASE_PATH"))
        
        # Calculate stats
        active_pass = next((p for p in outpasses if p["status"] in (Config.STATUS_APPROVED, Config.STATUS_OUTSIDE)), None)
        pending_count = sum(1 for p in outpasses if p["status"] == Config.STATUS_PENDING)
        approved_count = sum(1 for p in outpasses if p["status"] in (Config.STATUS_APPROVED, Config.STATUS_OUTSIDE, Config.STATUS_COMPLETED))
        rejected_count = sum(1 for p in outpasses if p["status"] == Config.STATUS_REJECTED)

        # Full pass data with QR image if active pass exists
        active_pass_data = get_outpass_by_id(active_pass["id"], custom_path=app.config.get("DATABASE_PATH")) if active_pass else None

        return render_template(
            "student/dashboard.html",
            outpasses=outpasses[:5],
            active_pass=active_pass_data,
            total_count=len(outpasses),
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count
        )

    @app.route("/student/apply", methods=["GET", "POST"])
    @login_required
    @role_required(Config.ROLE_STUDENT)
    def student_apply():
        if request.method == "POST":
            form_csrf = request.form.get("csrf_token")
            if not validate_csrf(form_csrf):
                flash("Security token mismatch. Please try again.", "danger")
                return redirect(url_for("student_apply"))

            destination = request.form.get("destination", "").strip()
            purpose = request.form.get("purpose", "").strip()
            dep_date = request.form.get("departure_date", "").strip()
            dep_time = request.form.get("departure_time", "").strip()
            exp_return_time = request.form.get("expected_return_time", "").strip()
            declaration = request.form.get("declaration")

            # Validation
            if not (destination and purpose and dep_date and dep_time and exp_return_time):
                flash("All fields are mandatory. Please fill out the full application.", "danger")
                return redirect(url_for("student_apply"))

            if not declaration:
                flash("You must agree to the hostel outpass declaration before submitting.", "danger")
                return redirect(url_for("student_apply"))

            planned_exit_dt = f"{dep_date} {dep_time}:00"
            expected_return_dt = f"{dep_date} {exp_return_time}:00"

            # Check chronological sanity
            try:
                dt_exit = datetime.strptime(planned_exit_dt, "%Y-%m-%d %H:%M:%S")
                dt_return = datetime.strptime(expected_return_dt, "%Y-%m-%d %H:%M:%S")
                if dt_return <= dt_exit:
                    flash("Expected return time must be strictly after planned departure time.", "danger")
                    return redirect(url_for("student_apply"))
            except ValueError:
                flash("Invalid date or time format provided.", "danger")
                return redirect(url_for("student_apply"))

            student_id = session["user_id"]
            outpass_id, pass_code = create_outpass(
                student_id=student_id,
                destination=destination,
                purpose=purpose,
                departure_date=dep_date,
                departure_time=dep_time,
                planned_exit_dt=planned_exit_dt,
                expected_return_dt=expected_return_dt,
                declaration_agreed=1,
                custom_path=app.config.get("DATABASE_PATH")
            )

            flash(f"Outpass application #{pass_code} submitted successfully to the Warden!", "success")
            return redirect(url_for("student_pass_view", outpass_id=outpass_id))

        today_date = get_now_ist_str().split()[0]
        return render_template("student/apply.html", today_date=today_date)

    @app.route("/student/history")
    @login_required
    @role_required(Config.ROLE_STUDENT)
    def student_history():
        student_id = session["user_id"]
        status_filter = request.args.get("status")
        all_outpasses = get_student_outpasses(student_id, custom_path=app.config.get("DATABASE_PATH"))
        
        if status_filter:
            filtered_passes = [p for p in all_outpasses if p["status"] == status_filter.upper()]
        else:
            filtered_passes = all_outpasses

        return render_template(
            "student/history.html",
            outpasses=filtered_passes,
            selected_status=status_filter or ""
        )

    @app.route("/student/pass/<int:outpass_id>")
    @login_required
    def student_pass_view(outpass_id):
        pass_data = get_outpass_by_id(outpass_id, custom_path=app.config.get("DATABASE_PATH"))
        if not pass_data:
            flash("Outpass record not found.", "danger")
            return redirect(url_for("student_dashboard"))

        # Access check: Only the owner student, any warden, or any guard can view the pass
        user_role = session.get("role")
        user_id = session.get("user_id")
        if user_role == Config.ROLE_STUDENT and pass_data["student_id"] != user_id:
            flash("Unauthorized: You cannot access another student's pass.", "danger")
            return redirect(url_for("student_dashboard"))

        return render_template("student/pass_view.html", pass_data=pass_data)

    # ---------------------------------------------------------
    # Warden Routes
    # ---------------------------------------------------------
    @app.route("/warden/dashboard")
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_dashboard():
        kpis = get_warden_kpis(custom_path=app.config.get("DATABASE_PATH"))
        # Get urgent pending requests (top 5)
        pending_requests = get_all_movements(status_filter=Config.STATUS_PENDING, custom_path=app.config.get("DATABASE_PATH"))[:5]
        return render_template("warden/dashboard.html", kpis=kpis, pending_requests=pending_requests)

    @app.route("/warden/approvals")
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_approvals():
        search = request.args.get("search")
        program = request.args.get("program")
        pending_list = get_all_movements(
            search=search,
            program=program,
            status_filter=Config.STATUS_PENDING,
            custom_path=app.config.get("DATABASE_PATH")
        )
        return render_template("warden/approvals.html", pending_list=pending_list, search=search or "", program=program or "")

    @app.route("/warden/approve/<int:outpass_id>", methods=["POST"])
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_approve_action(outpass_id):
        form_csrf = request.form.get("csrf_token")
        if not validate_csrf(form_csrf):
            flash("Security check failed.", "danger")
            return redirect(url_for("warden_approvals"))

        warden_id = session["user_id"]
        ok, msg = approve_outpass(outpass_id, warden_id, custom_path=app.config.get("DATABASE_PATH"))
        if ok:
            flash(f"Application approved. QR Verification Pass generated.", "success")
        else:
            flash(f"Approval failed: {msg}", "danger")
        return redirect(request.referrer or url_for("warden_approvals"))

    @app.route("/warden/reject/<int:outpass_id>", methods=["POST"])
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_reject_action(outpass_id):
        form_csrf = request.form.get("csrf_token")
        if not validate_csrf(form_csrf):
            flash("Security check failed.", "danger")
            return redirect(url_for("warden_approvals"))

        reason = request.form.get("reason", "Declined by hostel administration")
        warden_id = session["user_id"]
        ok, msg = reject_outpass(outpass_id, warden_id, reason=reason, custom_path=app.config.get("DATABASE_PATH"))
        if ok:
            flash("Application has been rejected with feedback.", "info")
        else:
            flash(f"Rejection failed: {msg}", "danger")
        return redirect(request.referrer or url_for("warden_approvals"))

    @app.route("/warden/movements")
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_movements():
        search = request.args.get("search")
        program = request.args.get("program")
        status_filter = request.args.get("status")
        date_filter = request.args.get("date")

        movements = get_all_movements(
            search=search,
            program=program,
            status_filter=status_filter,
            date_filter=date_filter,
            custom_path=app.config.get("DATABASE_PATH")
        )
        return render_template(
            "warden/movements.html",
            movements=movements,
            search=search or "",
            program=program or "",
            status_filter=status_filter or "",
            date_filter=date_filter or ""
        )

    @app.route("/warden/analytics")
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_analytics():
        csv_path = os.path.join(Config.BASE_DIR, "data.csv")
        csv_analytics = analyze_outpass_csv(csv_path)
        live_kpis = get_warden_kpis(custom_path=app.config.get("DATABASE_PATH"))
        return render_template("warden/analytics.html", analytics=csv_analytics, live_kpis=live_kpis)

    @app.route("/warden/students")
    @login_required
    @role_required(Config.ROLE_WARDEN)
    def warden_students():
        search = request.args.get("search")
        program = request.args.get("program")
        students = get_all_students(search=search, program=program, custom_path=app.config.get("DATABASE_PATH"))
        return render_template("warden/students.html", students=students, search=search or "", program=program or "")

    # ---------------------------------------------------------
    # Guard Routes
    # ---------------------------------------------------------
    @app.route("/guard/dashboard")
    @login_required
    @role_required(Config.ROLE_GUARD)
    def guard_dashboard():
        guard_gate = session.get("gate_name", "Gate 1")
        recent_logs = get_recent_gate_logs(gate_name=guard_gate, limit=15, custom_path=app.config.get("DATABASE_PATH"))
        
        # Calculate today's gate counts
        today = get_now_ist_str().split()[0]
        today_exits = sum(1 for l in recent_logs if l["movement_type"] == "EXIT" and l["timestamp"].startswith(today))
        today_entries = sum(1 for l in recent_logs if l["movement_type"] == "ENTRY" and l["timestamp"].startswith(today))

        return render_template(
            "guard/dashboard.html",
            guard_gate=guard_gate,
            recent_logs=recent_logs,
            today_exits=today_exits,
            today_entries=today_entries
        )

    @app.route("/guard/verify", methods=["GET", "POST"])
    @login_required
    @role_required(Config.ROLE_GUARD)
    def guard_verify():
        pass_data = None
        search_query = request.args.get("query", "").strip()
        error_msg = None

        if search_query:
            # Query might be verification token (from QR scan) or pass code (manual fallback e.g. GP-2026-0001)
            pass_data = get_outpass_by_token(search_query, custom_path=app.config.get("DATABASE_PATH"))
            if not pass_data:
                pass_data = get_outpass_by_code(search_query, custom_path=app.config.get("DATABASE_PATH"))
            if not pass_data:
                error_msg = f"No active pass found matching token/code '{search_query}'. Please re-check."

        return render_template(
            "guard/verify.html",
            pass_data=pass_data,
            search_query=search_query,
            error_msg=error_msg,
            guard_gate=session.get("gate_name", "Gate 1")
        )

    @app.route("/guard/record/exit", methods=["POST"])
    @login_required
    @role_required(Config.ROLE_GUARD)
    def guard_record_exit():
        form_csrf = request.form.get("csrf_token")
        if not validate_csrf(form_csrf):
            flash("Security check failed.", "danger")
            return redirect(url_for("guard_verify"))

        outpass_id = request.form.get("outpass_id")
        guard_id = session["user_id"]
        gate_name = session.get("gate_name", "Gate 1")
        notes = request.form.get("notes", "Photo verified by security guard.")

        ok, msg = record_gate_exit(
            outpass_id=int(outpass_id),
            guard_id=guard_id,
            gate_name=gate_name,
            notes=notes,
            custom_path=app.config.get("DATABASE_PATH")
        )

        if ok:
            flash(f"SUCCESS: {msg}", "success")
        else:
            flash(f"ERROR: {msg}", "danger")

        return redirect(url_for("guard_verify", query=request.form.get("return_query", "")))

    @app.route("/guard/record/entry", methods=["POST"])
    @login_required
    @role_required(Config.ROLE_GUARD)
    def guard_record_entry():
        form_csrf = request.form.get("csrf_token")
        if not validate_csrf(form_csrf):
            flash("Security check failed.", "danger")
            return redirect(url_for("guard_verify"))

        outpass_id = request.form.get("outpass_id")
        guard_id = session["user_id"]
        gate_name = session.get("gate_name", "Gate 1")
        notes = request.form.get("notes", "Student returned safely; photo confirmed.")

        ok, msg = record_gate_entry(
            outpass_id=int(outpass_id),
            guard_id=guard_id,
            gate_name=gate_name,
            notes=notes,
            custom_path=app.config.get("DATABASE_PATH")
        )

        if ok:
            flash(f"SUCCESS: {msg}", "success")
        else:
            flash(f"ERROR: {msg}", "danger")

        return redirect(url_for("guard_verify", query=request.form.get("return_query", "")))

    # ---------------------------------------------------------
    # In-App Notifications Center
    # ---------------------------------------------------------
    @app.route("/notifications")
    @login_required
    def notifications_view():
        user_id = session["user_id"]
        notifications = get_user_notifications(user_id, limit=50, custom_path=app.config.get("DATABASE_PATH"))
        return render_template("notifications.html", notifications=notifications)

    @app.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
    @login_required
    def mark_notification_read(notification_id):
        mark_notification_as_read(notification_id, session["user_id"], custom_path=app.config.get("DATABASE_PATH"))
        return redirect(request.referrer or url_for("notifications_view"))

    @app.route("/notifications/mark-all-read", methods=["POST"])
    @login_required
    def mark_all_notifications_read():
        mark_all_notifications_as_read(session["user_id"], custom_path=app.config.get("DATABASE_PATH"))
        flash("All notifications marked as read.", "info")
        return redirect(url_for("notifications_view"))

    @app.route("/api/notifications/unread-count")
    @login_required
    def api_unread_count():
        count = get_unread_notification_count(session["user_id"], custom_path=app.config.get("DATABASE_PATH"))
        return jsonify({"unread_count": count})

    # ---------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_code="404", error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("base.html", error_code="500", error_message="Internal Server Error"), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
