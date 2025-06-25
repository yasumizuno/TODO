import os
import re
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import docx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'docx'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_file(file_path):
    """Extract text from various file formats"""
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    elif file_extension == 'pdf':
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    
    elif file_extension == 'docx':
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    return ""

def extract_todos(text):
    """Extract ToDo items using rule-based patterns"""
    todos = []
    
    # Pattern 1: Lines containing "TODO", "TO-DO", "To Do", etc.
    todo_pattern1 = re.compile(r'(?i)(?:^|\s)(?:TODO|TO-DO|To Do|ToDo)(?:\s*:|\s+)(.+?)(?:\n|$)')
    matches = todo_pattern1.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 2: Lines starting with "- [ ]" or "* [ ]" (Markdown-style tasks)
    todo_pattern2 = re.compile(r'(?:^|\n)\s*[-*]\s*\[\s*\]\s*(.+?)(?:\n|$)')
    matches = todo_pattern2.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 3: Lines containing "タスク:" or "タスク："
    todo_pattern3 = re.compile(r'(?:^|\s)(?:タスク|課題)(?::|：)\s*(.+?)(?:\n|$)')
    matches = todo_pattern3.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 4: Lines containing "要対応" or "対応必要"
    todo_pattern4 = re.compile(r'(?:要対応|対応必要)(?::|：)?\s*(.+?)(?:\n|$)')
    matches = todo_pattern4.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 5: Lines with deadline patterns (期限、締切、〆切、due date, etc.)
    deadline_pattern = re.compile(r'(?:期限|締切|〆切|しめきり|デッドライン|due date|deadline)(?::|：|\s*は|\s*=|\s+)?\s*(.+?)(?:\n|$)', re.IGNORECASE)
    matches = deadline_pattern.findall(text)
    todos.extend([f"期限: {match.strip()}" for match in matches])
    
    # Pattern 6: Lines with date patterns that look like tasks (MM/DD or YYYY/MM/DD followed by task description)
    date_task_pattern = re.compile(r'(?:^|\n)\s*(?:\d{4}[/-])?\d{1,2}[/-]\d{1,2}(?:\s*[(（]?(?:月|火|水|木|金|土|日|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[)）]?)?\s*[:：]?\s*(.+?)(?:\n|$)')
    matches = date_task_pattern.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 7: Lines with "まで" followed by a task description
    made_pattern = re.compile(r'(\d{1,2}月\d{1,2}日|(?:\d{4}[/-])?\d{1,2}[/-]\d{1,2})(?:\s*[(（]?(?:月|火|水|木|金|土|日|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[)）]?)?\s*まで(?:に|は|で)?\s*(.+?)(?:\n|$)')
    matches = made_pattern.findall(text)
    todos.extend([f"{date}まで: {task.strip()}" for date, task in matches])
    
    # Pattern 8: Lines with action verbs followed by object (common in Japanese task descriptions)
    action_pattern = re.compile(r'(?:^|\n|\s)(?:する|作成する|準備する|確認する|レビューする|送付する|提出する|連絡する|報告する)(?:こと)?(?::|：)?\s*(.+?)(?:\n|$)')
    matches = action_pattern.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 9: Lines with "必要" or "必須" (indicating required actions)
    required_pattern = re.compile(r'(?:^|\n|\s)(.+?)\s*(?:が|は)\s*(?:必要|必須)(?:\n|$)')
    matches = required_pattern.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Pattern 10: Lines with "予定" followed by a task description
    schedule_pattern = re.compile(r'(?:予定|スケジュール)(?::|：|\s+)\s*(.+?)(?:\n|$)')
    matches = schedule_pattern.findall(text)
    todos.extend([match.strip() for match in matches])
    
    # Remove duplicates while preserving order
    unique_todos = []
    for todo in todos:
        if todo and todo not in unique_todos:
            unique_todos.append(todo)
    
    return unique_todos

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            text = extract_text_from_file(file_path)
            todos = extract_todos(text)
            
            # Clean up the file after processing
            os.remove(file_path)
            
            return jsonify({'todos': todos})
        except Exception as e:
            # Clean up the file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12001, debug=True)