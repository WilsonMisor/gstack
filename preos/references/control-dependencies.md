# Control Dependency Policy

Controls form a dependency graph. A downstream control cannot be GREEN if a prerequisite is RED, UNKNOWN or HUMAN REVIEW. Examples: disaster recovery depends on restorable backup, which depends on complete data/storage inventory; tenant-isolation testing depends on a defined tenant/authorization model. Record prerequisite IDs, detect missing/circular dependencies, and version/review the graph when architecture changes.
