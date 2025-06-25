document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const todoList = document.getElementById('todo-list');
    const noTodos = document.getElementById('no-todos');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const copyAllButton = document.getElementById('copy-all');
    const downloadCsvButton = document.getElementById('download-csv');
    
    // Update file name when file is selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileName.textContent = fileInput.files[0].name;
        } else {
            fileName.textContent = 'ファイルが選択されていません';
        }
    });
    
    // Handle form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (fileInput.files.length === 0) {
            showError('ファイルを選択してください');
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        // Show loading spinner
        resetUI();
        loading.classList.remove('hidden');
        uploadButton.disabled = true;
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'ファイルのアップロードに失敗しました');
            }
            
            displayResults(data.todos);
        } catch (error) {
            showError(error.message);
        } finally {
            loading.classList.add('hidden');
            uploadButton.disabled = false;
        }
    });
    
    // Copy all todos to clipboard
    copyAllButton.addEventListener('click', () => {
        const todos = Array.from(todoList.querySelectorAll('li')).map(li => li.textContent);
        
        if (todos.length === 0) {
            return;
        }
        
        const text = todos.join('\\n');
        navigator.clipboard.writeText(text)
            .then(() => {
                const originalText = copyAllButton.textContent;
                copyAllButton.textContent = 'コピーしました！';
                setTimeout(() => {
                    copyAllButton.textContent = originalText;
                }, 2000);
            })
            .catch(err => {
                showError('クリップボードへのコピーに失敗しました: ' + err.message);
            });
    });
    
    // Download todos as CSV
    downloadCsvButton.addEventListener('click', () => {
        const todos = Array.from(todoList.querySelectorAll('li')).map(li => li.textContent);
        
        if (todos.length === 0) {
            return;
        }
        
        // Escape quotes and wrap each todo in quotes
        const csvContent = todos.map(todo => `"${todo.replace(/"/g, '""')}"`).join('\\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'todos.csv');
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
    
    function displayResults(todos) {
        results.classList.remove('hidden');
        todoList.innerHTML = '';
        
        if (todos.length === 0) {
            noTodos.classList.remove('hidden');
            return;
        }
        
        noTodos.classList.add('hidden');
        
        todos.forEach(todo => {
            const li = document.createElement('li');
            li.textContent = todo;
            todoList.appendChild(li);
        });
    }
    
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
    }
    
    function resetUI() {
        results.classList.add('hidden');
        errorMessage.classList.add('hidden');
        todoList.innerHTML = '';
    }
});