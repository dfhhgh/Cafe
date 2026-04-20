class Token:
 
    def __init__(self, type, value, columnNumber, lineNumber):
        self.type = type
        self.value = value
        self.columnNumber = columnNumber
        self.lineNumber = lineNumber

    def __repr__(self):
        return f"{self.type.name}('{self.value}') at line {self.lineNumber}, col {self.columnNumber}"