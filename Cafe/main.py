from Scanner.Scanner import Scanner

# قراءة ملف cafe
with open("test.cafe", "r") as file:
    source_code = file.read()

# إنشاء scanner
scanner = Scanner(source_code)

# تحليل التوكنز
tokens = scanner.scan_tokens()

# طباعة النتيجة
for token in tokens:
    print(token)