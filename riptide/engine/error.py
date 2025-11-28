class NonInteractiveCommandRunError(Exception):
    """
    Exception to be thrown when a pre start or other non-interactive command exits with a non-zero exit code
    """

    def __init__(self, exit_status: int, stdout: str, stderr: str):
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return (
            f"Command returned non-zero exit status {self.exit_status}."
            f"\n## Stdout:\n{self.stdout}\n\n## Stderr:\n{self.stderr}"
        )
