import ast
import re
from tkinter import *
from tkinter import font
from tkinter import filedialog, messagebox
from assets import Assets
from config import Config


class CodeReviewer:

    def __init__(self, window):
        self.result_text = None
        self.window = window

        BOLD_FONT = font.Font(family="Arial", size=10, weight="bold")
        REGULAR_FONT = font.Font(family="Arial", size=10)

        label = Label(window, text="Upload your Python file to detect code smell:", font=BOLD_FONT)
        label.grid(row=0, column=0, padx=5, pady=5)

        self.entry = Entry(window, width=50)

        uploadButton = Button(window, text="Upload File", command=self.upload_file, font=REGULAR_FONT)
        uploadButton.grid(row=0, column=2, padx=5, pady=5)

        self.detectCodeSmellButton = Button(window, text="Detect Code Smell", command=self.uiCode, state="disabled",font=REGULAR_FONT)

        self.result_text = StringVar()
        self.result_label = Label(window, textvariable=self.result_text, wraplength=400, justify="left", font=REGULAR_FONT)
        self.result_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        self.window.mainloop()

    def upload_file(self):
        filePath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        self.entry.delete(0, END)
        self.entry.insert(END, filePath)
        if filePath:
            messagebox.showinfo(Assets.UPLOAD_DIALOGUE_TITLE, Assets.UPLOAD_DIALOGUE_SUCCESS_MSG + filePath)
            self.detectCodeSmellButton.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
            self.detectCodeSmellButton.config(state="normal")
        else:
            messagebox.showerror(Assets.UPLOAD_DIALOGUE_TITLE, Assets.UPLOAD_DIALOGUE_FAIL_MSG)

    @staticmethod
    def remove_non_code_lines(filePath):
        with open(filePath, 'r') as file:
            lines = file.readlines()
            # Regex to detect lines with comments
            pattern = re.compile(r'\s*#.*$')
            filtered_lines = []
            for line in lines:
                if line.strip() and not re.match(pattern, line):
                    filtered_lines.append(line)
        return ''.join(filtered_lines)

    def detect_long_methods(self, filePath, threshold=Config.LONG_METHOD_THRESHOLD):
        tree = ast.parse(self.remove_non_code_lines(filePath))
        longMethods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                numLines = node.end_lineno - node.lineno + 1
                longMethods.append((node.name, numLines)) if numLines > threshold else None
        return longMethods

    def detect_long_para_list(self, filePath, threshold=Config.LONG_PARAMETER_THRESHOLD):
        tree = ast.parse(self.remove_non_code_lines(filePath))
        LongParameterList = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                numParameters = len(node.args.args) + len(node.args.kw_defaults) + len(node.args.kwonlyargs)
                LongParameterList.append((node.name, numParameters)) if numParameters > threshold else None
        return LongParameterList

    @staticmethod
    def check_jaccard_similarity(content1, content2):
        intersection = len(set(content1) & set(content2))
        union = len(set(content1) | set(content2))
        return intersection / union if union != 0 else 0

    def extract_tokens(self, node):
        tokens = set()
        self.extract_tokens_recursively(node, tokens)
        return tokens

    def extract_tokens_recursively(self, node, tokens):
        # Replace variable names with 'var'
        if isinstance(node, ast.Name): tokens.add("var" if isinstance(node.ctx, ast.Store) or isinstance(node.ctx, ast.Load) else node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
            self.extract_tokens_recursively(node.value, tokens)
        elif isinstance(node, ast.arg): tokens.add("var")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name): tokens.add(node.func.id)  # Retain function call names
            if isinstance(node.func, ast.Attribute): tokens.add(node.func.attr)
            for arg in node.args:
                if isinstance(arg, ast.Name): tokens.add("var")
                else: self.extract_tokens_recursively(arg, tokens)
        else:
            for child in ast.iter_child_nodes(node):
                self.extract_tokens_recursively(child, tokens)

    def detect_duplicate_functions(self, filePath, threshold=Config.JACCARD_SIMILARITY_THRESHOLD):
        tree = ast.parse(self.remove_non_code_lines(filePath))
        functions = {}
        duplicatFunctions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_name = node.name
                function_contents = self.extract_tokens(node)

                # Identify duplicate functions
                for name, tokens in functions.items():
                    similarity = self.check_jaccard_similarity(function_contents, tokens)
                    if similarity > threshold:
                        duplicatFunctions.append((function_name, name, similarity))

                functions[function_name] = function_contents

        return duplicatFunctions

    def remove_transitivity_duplicate_func_map(self, mapping, key):
        # Function to remove transitivity and find the final duplicate method in the map
        if key not in mapping:
            return key
        else:
            return self.remove_transitivity_duplicate_func_map(mapping, mapping[key])

    def replace_function_calls(self, node, duplicate_to_original):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # Check if the function call is to a duplicate function
            if node.func.id in duplicate_to_original:
                # Replace the function name with the original function
                node.func.id = duplicate_to_original[node.func.id]

        # Recursively call replace_function_calls on child nodes    
        for child_node in ast.iter_child_nodes(node):
            self.replace_function_calls(child_node, duplicate_to_original)

    def remove_duplicate_functions(self, node, duplicate_to_original):
        # Remove duplicate methods from original code while refactoring
        if isinstance(node, ast.FunctionDef) and node.name in duplicate_to_original:
            return None
        new_body = []
        for child_node in node.body:
            if isinstance(child_node, ast.FunctionDef):
                child_node = self.remove_duplicate_functions(child_node, duplicate_to_original)
            if child_node:
                new_body.append(child_node)
        node.body = new_body
        return node

    def refactor_code(self, filePath, duplicate_code):
        dup_func_map = {}
        for i in duplicate_code:
            dup_func_map[i[0]] = i[1]
        ultimate_unique_values = {key: self.remove_transitivity_duplicate_func_map(dup_func_map, key) for key in
                                  dup_func_map}

        parsed_code = ast.parse(self.remove_non_code_lines(filePath))
        self.replace_function_calls(parsed_code, ultimate_unique_values)
        self.remove_duplicate_functions(parsed_code, ultimate_unique_values)
        refactored_code = ast.unparse(parsed_code)
        refactored_file_name = filePath.replace('.py', '_refactored.py')
        with open(refactored_file_name, 'w') as file:
            file.write(refactored_code)
        return refactored_file_name

    @staticmethod
    def generate_message(long_list, type):
        # Function to show output in the Dialogbox in UI
        message = ""
        if long_list:
            message += Assets.LONG_FUNC_CODE_SMELL_MSG if type == 'method' else Assets.LONG_PARA_CODE_SMELL_MSG
            for idx, attr in enumerate(long_list, start=1):
                name, count = attr
                message += f"    {idx}. {name} - Number of {'Lines' if type == 'method' else 'Parameters'} : {count}\n"
        else:
            message += Assets.NO_LONG_FUNC_CODE_SMELL_MSG if type == 'method' else Assets.NO_LONG_PARA_CODE_SMELL_MSG

        return message

    @staticmethod
    def generate_duplicated_code_message(duplicatecode):
        # Function to show output in the Dialogbox in UI for duplicate code
        message = ""
        if duplicatecode:
            message += Assets.DUPLICATE_CODE_SMELL_MSG
            for idx, (func1, func2, similarity) in enumerate(duplicatecode, start=1):
                message += f"    {idx}. {func1} and {func2} have a similarity of {similarity}\n"
        else:
            message += Assets.NO_DUPLICATE_CODE_SMELL_MSG

        return message

    def uiCode(self):
        # Init GUI
        filename = self.entry.get()
        duplicate_code = self.detect_duplicate_functions(filename)
        longMethods = self.detect_long_methods(filename)
        longParaList = self.detect_long_para_list(filename)

        result_message = " Result of code smell :\n\n" + self.generate_message(longMethods,'method') + self.generate_message(
            longParaList, 'para') + self.generate_duplicated_code_message(duplicate_code)
        self.result_text.set(result_message)

        if duplicate_code:
            response = messagebox.askquestion(Assets.DIALOGUE_DUPLICATE_CODE_QUESTION_TITLE, Assets.DIALOGUE_DUPLICATE_CODE_QUESTION_MSG)
            if response == 'yes':
                refactor_filename = self.refactor_code(filename, duplicate_code)
                messagebox.showinfo(Assets.DIALOGUE_REFACTOR_QUESTION_TITLE, Assets.DIALOGUE_REFACTOR_QUESTION_MSG + " " + refactor_filename)
            else:
                messagebox.showinfo(Assets.DIALOGUE_NO_REFACTOR_QUESTION_TITLE, Assets.DIALOGUE_NO_REFACTOR_QUESTION_MSG)


if __name__ == "__main__":
    window = Tk()
    window.title("Code Reviewer")
    CodeReviewer(window)
