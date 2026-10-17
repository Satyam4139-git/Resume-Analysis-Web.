class ResumeAnalyzerError(Exception):
    """
    Base exception for the Resume Analyzer application.
    """
    pass


class AIServiceError(ResumeAnalyzerError):
    """
    Raised when AI service communication fails.
    """
    pass


class FileReaderError(ResumeAnalyzerError):
    """
    Raised when a resume file cannot be read.
    """
    pass


class ResumeValidationError(ResumeAnalyzerError):
    """
    Raised when AI output validation fails.
    """
    pass


class ResumeParserError(ResumeAnalyzerError):
    """
    Raised when resume parsing fails.
    """
    pass