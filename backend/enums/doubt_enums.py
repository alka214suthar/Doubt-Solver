from enum import Enum
class DoubtStatus(str, Enum):
    CREATED = "created"
    SOLVED = "solved"
    NOT_SOLVED = "not_solved"

class Subjects(str, Enum):
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    HISTORY = "History"
    GEOGRAPHY = "Geography"
    ENGLISH = "English"
    COMPUTER_SCIENCE = "Computer Science"
    LOGICAL_REASONING = "Logical Reasoning"

class ErrorResponse(str, Enum):
    FAILED_TO_CREATE_DOUBT = "Something went wrong. Please try again."
    DOUBT_NOT_FOUND = "We couldn't find that doubt."
    SOLUTION_NOT_FOUND = "We couldn't find that solution."
    USER_NOT_FOUND = "We couldn't find your account."
    FAILED_TO_SOLVE_DOUBT = "Something went wrong. Please try again."
    NOT_AVAILABLE_FREE_DOUBT = "You've used all your free doubts."
    FAILED_TO_ADD_USER = "Something went wrong. Please try again."
    USER_ALREADY_EXISTS = "An account with this email already exists."
    PASSWORD_INCORRECT = "Invalid email or password"

