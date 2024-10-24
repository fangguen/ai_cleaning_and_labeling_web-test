function handleErrors(response) {
    if (!response.ok) {
        throw Error(response.statusText);
    }
    return response;
}

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const originalData = document.getElementById('originalData');
    const processedData = document.getElementById('processedData');
    const resultTable = document.getElementById('resultTable');
    const downloadBtn = document.getElementById('downloadBtn');
    const addDimensionBtn = document.getElementById('addDimensionBtn');
    const dimensionsContainer = document.getElementById('dimensionsContainer');
    const chatContainer = document.getElementById('chatContainer');
    const toggleChatBtn = document.getElementById('toggleChatBtn');
    const chatMessages = document.querySelector('.chat-messages');
    const userInput = document.getElementById('userInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const instructionsBtn = document.getElementById('instructionsBtn');
    const instructionsModal = new bootstrap.Modal(document.getElementById('instructionsModal'));

    let currentProcessType = 'cleaning';

    // 初始化维度
    function initDimensions() {
        const defaultDimensions = currentProcessType === 'cleaning' 
            ? defaultCleaningDimensions 
            : defaultAnnotationDimensions;
        defaultDimensions.forEach(dim => addDimension(dim));
    }

    // 添加维度
    function addDimension(value = '') {
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.innerHTML = `
            <input type="text" class="form-control dimension-input" value="${value}">
            <button class="btn btn-outline-danger remove-dimension">删除</button>
        `;
        dimensionsContainer.appendChild(div);

        div.querySelector('.remove-dimension').addEventListener('click', function() {
            dimensionsContainer.removeChild(div);
        });
    }

    // 获取所有维度
    function getDimensions() {
        return Array.from(document.querySelectorAll('.dimension-input')).map(input => input.value);
    }

    // 文件上传和处理
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) {
            alert('请选择文件');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload-file/', {
            method: 'POST',
            body: formData
        })
        .then(handleErrors)
        .then(response => response.json())
        .then(data => {
            originalData.value = data.content;
            const processType = document.querySelector('input[name="processType"]:checked').value;
            const dimensions = getDimensions();

            showLoading();

            return fetch('/process-file/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    content: data.content,
                    process_type: processType,
                    dimensions: dimensions
                })
            });
        })
        .then(handleErrors)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            processedData.value = JSON.stringify(data.result, null, 2);
            displayResults(data.result);
            downloadBtn.disabled = false;
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('处理文件时出错：' + error.message);
        });
    });

    // 处理数据
    function processData(content) {
        const processType = document.querySelector('input[name="processType"]:checked').value;
        const dimensions = getDimensions();

        showLoading();

        fetch('/process-file/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                process_type: processType,
                content: content,
                dimensions: dimensions
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.error) {
                alert('处理出错: ' + data.error);
            } else {
                displayResults(data.result);
                processedData.value = JSON.stringify(data.result, null, 2);
                downloadBtn.disabled = false;
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('发生错误: ' + error.message);
        });
    }

    // 显示结果
    function displayResults(results) {
        processedData.value = JSON.stringify(results, null, 2);
        
        let tableHTML = '<table class="table"><thead><tr><th>维度</th><th>结果</th></tr></thead><tbody>';
        results.forEach(result => {
            for (const [key, value] of Object.entries(result)) {
                tableHTML += `<tr><td>${key}</td><td>${value}</td></tr>`;
            }
        });
        tableHTML += '</tbody></table>';
        resultTable.innerHTML = tableHTML;
    }

    // 下载结果
    downloadBtn.addEventListener('click', function() {
        const blob = new Blob([processedData.value], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'processed_data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // 切换处理类型
    document.querySelectorAll('input[name="processType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            currentProcessType = this.value;
            dimensionsContainer.innerHTML = '';
            initDimensions();
        });
    });

    // 聊天功能
    toggleChatBtn.addEventListener('click', function() {
        chatContainer.classList.toggle('minimized');
        const icon = toggleChatBtn.querySelector('i');
        icon.classList.toggle('fa-chevron-up');
        icon.classList.toggle('fa-chevron-down');
    });

    sendMessageBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            appendMessage('user', message);
            fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                if (data.reply) {
                    appendMessage('ai', data.reply);
                } else {
                    appendMessage('ai', '抱歉，我现在无法回答。请稍后再试。');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                appendMessage('ai', '发生错误，请稍后再试。');
            });
            userInput.value = '';
        }
    }

    function appendMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 使用说明
    instructionsBtn.addEventListener('click', function() {
        instructionsModal.show();
    });

    // 获取CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 初始化
    initDimensions();
    addDimensionBtn.addEventListener('click', () => addDimension());

    // 事件监听器
    sendMessageBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // 防止表单提交
            sendMessage();
        }
    });

    // 添加这些新函数显示和隐藏加载指示器
    function showLoading() {
        // 创建或显示加载指示器
        const loader = document.getElementById('loader') || createLoader();
        loader.style.display = 'block';
    }

    function hideLoading() {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    function createLoader() {
        const loader = document.createElement('div');
        loader.id = 'loader';
        loader.innerHTML = '处理中...';
        loader.style.position = 'fixed';
        loader.style.top = '50%';
        loader.style.left = '50%';
        loader.style.transform = 'translate(-50%, -50%)';
        loader.style.padding = '20px';
        loader.style.background = 'rgba(0,0,0,0.5)';
        loader.style.color = 'white';
        loader.style.borderRadius = '5px';
        loader.style.zIndex = '1000';
        document.body.appendChild(loader);
        return loader;
    }
});
