from app.config.security import require_roles

# ── Hospital roles ────────────────────────────────────────────────────────────
# Only admin can create / update / delete a hospital
admin_only              = require_roles("admin")

# Admin and doctor can create / update a clinic
admin_or_doctor         = require_roles("admin", "doctor")

# Admin, doctor and staff can manage departments
admin_doctor_staff      = require_roles("admin", "doctor", "staff")

# Anyone logged in can read
any_authenticated        = require_roles("admin", "doctor", "staff", "patient")