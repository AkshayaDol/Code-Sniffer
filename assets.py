class Assets:
    LONG_FUNC_CODE_SMELL_MSG = "  • Long methods/functions code smell detected. :\n"
    LONG_PARA_CODE_SMELL_MSG = "\n  • Method/Function has a long parameter list detected :\n"

    NO_LONG_FUNC_CODE_SMELL_MSG = "  • No long methods/functions detected.\n\n"
    NO_LONG_PARA_CODE_SMELL_MSG = "\n  • No long parameter list detected.\n\n"

    DUPLICATE_CODE_SMELL_MSG = "\n  • Duplicated code detected.\n"
    NO_DUPLICATE_CODE_SMELL_MSG = "\n  • No duplicated code detected.\n\n"

    DIALOGUE_DUPLICATE_CODE_QUESTION_TITLE = "Duplicated Code Detected"
    DIALOGUE_DUPLICATE_CODE_QUESTION_MSG = "Duplicated code is detected. Do you want to refactor the code?"

    DIALOGUE_REFACTOR_QUESTION_TITLE = "Refactoring Complete"
    DIALOGUE_REFACTOR_QUESTION_MSG = "Code refactored successfully. Refactored code saved to a new file: \n"

    DIALOGUE_NO_REFACTOR_QUESTION_TITLE = "Refactoring Skipped"
    DIALOGUE_NO_REFACTOR_QUESTION_MSG = "No code refactoring performed."

    UPLOAD_DIALOGUE_TITLE = "Upload Status"
    UPLOAD_DIALOGUE_SUCCESS_MSG = "File uploaded successfully : "
    UPLOAD_DIALOGUE_FAIL_MSG = "Something went wrong. Please try to upload the file again."