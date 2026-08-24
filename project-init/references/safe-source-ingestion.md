# Safe Source Ingestion

Inventory before interpretation. Never execute a supplied file merely to understand it. Reject archive path traversal, absolute paths and symlink entries. Treat macro-enabled documents and executable/script inputs as inspect-only. Preserve originals. Any unsupported or ambiguous source becomes UNKNOWN and is escalated rather than guessed.
