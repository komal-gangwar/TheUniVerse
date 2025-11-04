let currentMode = 'normal';
let isListening = false;
let recognition = null;
let synthesis = window.speechSynthesis;
let currentTopic = '';
let currentQuestionType = '';
let currentQuestionData = null;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('messageInput').value = transcript;
        sendMessage();
    };
    
    recognition.onend = function() {
        isListening = false;
        updateVoiceButton();
    };
}

// Auto-start in normal mode on page load
window.addEventListener('DOMContentLoaded', () => {
    currentMode = 'normal';
    updateModeUI('normal');
    addSystemMessage('👋 Welcome! I\'m your AI teacher. Ask me anything!');
});

function switchMode(mode) {
    currentMode = mode;
    
    // Hide practice flow when switching modes
    document.getElementById('practiceFlow').style.display = 'none';
    
    updateModeUI(mode);
    
    const messages = {
        'normal': 'Switched to Normal Chat Mode',
        'practice': 'Switched to Practice Mode - Let\'s start practicing!',
        'counseling': 'Switched to Counseling Mode'
    };
    
    addSystemMessage(messages[mode]);
    updateAvatarStatus(`${mode} mode active`);
    
    // Show/hide message input based on mode
    const messageInputContainer = document.querySelector('.flex.gap-2.items-center');
    
    // Show practice flow if in practice mode
    if (mode === 'practice') {
        document.getElementById('practiceFlow').style.display = 'block';
        resetPracticeFlow();
        // Hide message input in practice mode
        if (messageInputContainer) {
            messageInputContainer.style.display = 'none';
        }
    } else {
        // Show message input in normal and counseling modes
        if (messageInputContainer) {
            messageInputContainer.style.display = 'flex';
        }
    }
}

function updateModeUI(mode) {
    const header = document.getElementById('header');
    const normalBtn = document.getElementById('normalBtn');
    const practiceBtn = document.getElementById('practiceBtn');
    const counselingBtn = document.getElementById('counselingBtn');
    
    // Reset all buttons
    normalBtn.className = 'px-4 py-2 rounded-lg bg-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-300 transition';
    practiceBtn.className = 'px-4 py-2 rounded-lg bg-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-300 transition';
    counselingBtn.className = 'px-4 py-2 rounded-lg bg-gray-200 text-gray-700 text-sm font-medium hover:bg-gray-300 transition';
    
    if (mode === 'practice') {
        header.className = 'mode-practice text-white py-6 px-8 transition-all duration-500';
        practiceBtn.className = 'px-4 py-2 rounded-lg bg-pink-600 text-white text-sm font-medium hover:bg-pink-700 transition';
    } else if (mode === 'counseling') {
        header.className = 'mode-counseling text-white py-6 px-8 transition-all duration-500';
        counselingBtn.className = 'px-4 py-2 rounded-lg bg-cyan-600 text-white text-sm font-medium hover:bg-cyan-700 transition';
    } else {
        header.className = 'mode-normal text-white py-6 px-8 transition-all duration-500';
        normalBtn.className = 'px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 transition';
    }
}

function addSystemMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    
    if (chatMessages.children[0]?.textContent?.includes('Welcome!')) {
        chatMessages.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'text-center py-2 message-enter';
    messageDiv.innerHTML = `<span class="inline-block bg-gray-200 text-gray-700 px-4 py-2 rounded-full text-sm">${text}</span>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(text, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    
    if (chatMessages.children[0]?.textContent?.includes('Welcome!')) {
        chatMessages.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} message-enter`;
    
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    let content = text;
    let contentClass = 'text-sm message-content';
    
    if (!isUser && typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            }
        });
        
        content = marked.parse(text);
        contentClass = 'text-sm ai-response';
    }
    
    messageDiv.innerHTML = `
        <div class="max-w-2xl">
            <div class="${isUser ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-800'} rounded-2xl px-4 py-3">
                <div class="${contentClass}">${content}</div>
            </div>
            <p class="text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}">${time}</p>
        </div>
    `;
    
    if (!isUser) {
        addCopyButtonsToCodeBlocks(messageDiv);
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addCopyButtonsToCodeBlocks(container) {
    const codeBlocks = container.querySelectorAll('pre');
    codeBlocks.forEach((block) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        block.parentNode.insertBefore(wrapper, block);
        wrapper.appendChild(block);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy';
        copyBtn.onclick = () => {
            const code = block.textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            });
        };
        wrapper.appendChild(copyBtn);
    });
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'flex justify-start message-enter';
    typingDiv.innerHTML = `
        <div class="bg-gray-100 rounded-2xl typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Practice Flow Functions
function resetPracticeFlow() {
    currentTopic = '';
    currentQuestionType = '';
    currentQuestionData = null;
    
    // Hide all steps
    document.querySelectorAll('.practice-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Show topic step
    document.getElementById('topicStep').classList.add('active');
    document.getElementById('topicInput').value = '';
}

function submitTopic() {
    const topic = document.getElementById('topicInput').value.trim();
    if (!topic) {
        alert('Please enter a topic');
        return;
    }
    
    currentTopic = topic;
    
    // Check if topic is coding related
    const codingKeywords = ['javascript', 'python', 'java', 'c++', 'coding', 'programming', 'algorithm', 'data structure', 'dsa'];
    const isCodingTopic = codingKeywords.some(keyword => topic.toLowerCase().includes(keyword));
    
    // Show/hide coding option based on topic
    const codingOption = document.getElementById('codingOption');
    if (isCodingTopic) {
        codingOption.style.display = 'block';
    } else {
        codingOption.style.display = 'none';
    }
    
    // Move to question type selection
    document.getElementById('topicStep').classList.remove('active');
    document.getElementById('questionTypeStep').classList.add('active');
}

function backToTopic() {
    document.getElementById('questionTypeStep').classList.remove('active');
    document.getElementById('topicStep').classList.add('active');
}

async function selectQuestionType(type) {
    currentQuestionType = type;
    
    // Hide question type step
    document.getElementById('questionTypeStep').classList.remove('active');
    
    // Show loading
    updateAvatarStatus('Generating question...');
    showTypingIndicator();
    
    try {
        // Generate question based on type
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: `Generate a ${type} question about ${currentTopic}. Return only JSON with this structure:
                For MCQ: {"type":"mcq","question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"correct":"A","explanation":"..."}
                For subjective: {"type":"subjective","question":"...","answer":"..."}
                For coding: {"type":"coding","question":"...","test_cases":"...","solution":"..."}`,
                mode: 'practice'
            })
        });
        
        const data = await response.json();
        hideTypingIndicator();
        
        if (data.success) {
            try {
                // Try to parse JSON from response
                const jsonMatch = data.response.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    currentQuestionData = JSON.parse(jsonMatch[0]);
                    displayQuestionByType(type);
                } else {
                    // Fallback: use response as is
                    displaySimpleQuestion(type, data.response);
                }
            } catch (e) {
                displaySimpleQuestion(type, data.response);
            }
        } else {
            alert('Error generating question. Please try again.');
            backToTopic();
        }
    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        alert('Error generating question. Please try again.');
        backToTopic();
    }
}

function displayQuestionByType(type) {
    if (type === 'mcq') {
        displayMCQ();
    } else if (type === 'subjective') {
        displaySubjective();
    } else if (type === 'coding') {
        displayCoding();
    }
}

function displayMCQ() {
    const mcqQuestion = document.getElementById('mcqQuestion');
    const mcqOptions = document.getElementById('mcqOptions');
    
    mcqQuestion.innerHTML = currentQuestionData.question;
    
    let optionsHtml = '';
    currentQuestionData.options.forEach((option, index) => {
        const letter = String.fromCharCode(65 + index);
        optionsHtml += `
            <label class="flex items-center gap-2 p-3 bg-white rounded-lg cursor-pointer hover:bg-blue-50 border border-gray-200">
                <input type="radio" name="mcqOption" value="${letter}" class="text-blue-600">
                <span class="text-sm">${option}</span>
            </label>
        `;
    });
    mcqOptions.innerHTML = optionsHtml;
    
    document.getElementById('mcqDisplay').classList.add('active');
    document.getElementById('mcqResult').style.display = 'none';
}

function submitMCQ() {
    const selected = document.querySelector('input[name="mcqOption"]:checked');
    if (!selected) {
        alert('Please select an option');
        return;
    }
    
    const resultDiv = document.getElementById('mcqResult');
    const isCorrect = selected.value === currentQuestionData.correct;
    
    resultDiv.className = 'mt-3 p-3 rounded-lg ' + (isCorrect ? 'bg-green-100 border border-green-300' : 'bg-red-100 border border-red-300');
    
    let html = '<div class="font-semibold ' + (isCorrect ? 'text-green-800' : 'text-red-800') + ' mb-2">';
    html += isCorrect ? '✅ Correct!' : '❌ Incorrect';
    html += '</div>';
    html += '<div class="text-gray-700">';
    html += '<strong>Correct Answer:</strong> ' + currentQuestionData.correct;
    html += '</div>';
    
    if (currentQuestionData.explanation) {
        html += '<div class="text-gray-700 mt-2"><strong>Explanation:</strong> ' + currentQuestionData.explanation + '</div>';
    }
    
    resultDiv.innerHTML = html;
    resultDiv.style.display = 'block';
}

function displaySubjective() {
    const subjectiveQuestion = document.getElementById('subjectiveQuestion');
    subjectiveQuestion.innerHTML = currentQuestionData.question || 'Question not available';
    
    document.getElementById('subjectiveDisplay').classList.add('active');
    document.getElementById('subjectiveAnswer').style.display = 'none';
}

function showSubjectiveAnswer() {
    const answerDiv = document.getElementById('subjectiveAnswer');
    const answer = currentQuestionData.answer || currentQuestionData.explanation || 'Answer not available. Please try generating a new question.';
    answerDiv.innerHTML = `<div class="text-gray-800">${answer}</div>`;
    answerDiv.style.display = 'block';
}

function displayCoding() {
    const codingQuestion = document.getElementById('codingQuestion');
    const testCases = document.getElementById('testCases');
    
    codingQuestion.innerHTML = currentQuestionData.question;
    testCases.innerHTML = `<strong>Test Cases:</strong><br>${currentQuestionData.test_cases}`;
    
    document.getElementById('codingDisplay').classList.add('active');
    document.getElementById('codeOutput').style.display = 'none';
    document.getElementById('codeEditor').value = '';
}

function runCode() {
    const code = document.getElementById('codeEditor').value;
    const outputDiv = document.getElementById('codeOutput');
    
    if (!code.trim()) {
        alert('Please write some code first');
        return;
    }
    
    // Simulate code execution (in real app, would send to backend)
    outputDiv.innerHTML = `
        <div class="text-yellow-400">⚠️ Code execution simulation</div>
        <div class="text-gray-300 mt-2">Your code:</div>
        <pre class="text-gray-400 mt-1">${code}</pre>
    `;
    outputDiv.style.display = 'block';
}

function submitCode() {
    const code = document.getElementById('codeEditor').value;
    const outputDiv = document.getElementById('codeOutput');
    
    if (!code.trim()) {
        alert('Please write some code first');
        return;
    }
    
    // Show solution
    outputDiv.innerHTML = `
        <div class="text-green-400">✅ Submitted!</div>
        <div class="text-gray-300 mt-3"><strong>Solution:</strong></div>
        <pre class="text-gray-400 mt-1">${currentQuestionData.solution || 'Solution not available'}</pre>
    `;
    outputDiv.style.display = 'block';
}

function displaySimpleQuestion(type, questionText) {
    // Fallback for non-JSON responses
    if (type === 'mcq') {
        currentQuestionData = {
            question: questionText,
            options: ['A) Option A', 'B) Option B', 'C) Option C', 'D) Option D'],
            correct: 'A',
            explanation: ''
        };
        displayMCQ();
    } else if (type === 'subjective') {
        currentQuestionData = {
            question: questionText,
            answer: 'Answer will be shown when you click the button.'
        };
        displaySubjective();
    } else if (type === 'coding') {
        currentQuestionData = {
            question: questionText,
            test_cases: 'Test cases not provided',
            solution: 'Solution not provided'
        };
        displayCoding();
    }
}

function newQuestion() {
    // Reset all displays
    document.querySelectorAll('.practice-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Go back to topic or question type
    if (currentTopic) {
        document.getElementById('questionTypeStep').classList.add('active');
    } else {
        document.getElementById('topicStep').classList.add('active');
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, true);
    input.value = '';
    
    updateAvatarStatus('Thinking...');
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                mode: currentMode
            })
        });
        
        const data = await response.json();
        
        hideTypingIndicator();
        
        if (data.success) {
            addMessage(data.response, false);
            updateAvatarStatus('Ready to help!');
            
            if (document.getElementById('soundToggle').checked) {
                const plainText = data.response.replace(/[#*`\[\]]/g, '');
                speak(plainText);
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', false);
            updateAvatarStatus('Error occurred');
        }
    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessage('Sorry, I could not connect. Please try again.', false);
        updateAvatarStatus('Connection error');
    }
}

function toggleVoice() {
    if (!recognition) {
        alert('Voice recognition is not supported in your browser.');
        return;
    }
    
    if (isListening) {
        recognition.stop();
        isListening = false;
    } else {
        recognition.start();
        isListening = true;
        updateAvatarStatus('Listening...');
    }
    
    updateVoiceButton();
}

function updateVoiceButton() {
    const btn = document.getElementById('voiceBtn');
    if (isListening) {
        btn.innerHTML = '🔴';
        btn.classList.add('pulse-ring');
    } else {
        btn.innerHTML = '🎤';
        btn.classList.remove('pulse-ring');
    }
}

function speak(text) {
    if (synthesis.speaking) {
        synthesis.cancel();
    }
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    synthesis.speak(utterance);
}

function updateAvatarStatus(status) {
    document.getElementById('avatarStatus').textContent = status;
}
