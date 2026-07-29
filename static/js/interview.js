/* AI Mock Interview Interactive Suite */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-update Target Role Title when Category changes
    const categorySelect = document.getElementById('category-select');
    const targetRoleInput = document.getElementById('target-role-input');

    if (categorySelect && targetRoleInput) {
        const categoryRoleMap = {
            'Python': 'Python Full Stack Developer',
            'SQL': 'SQL & Database Systems Engineer',
            'OOP': 'Software Engineer (OOP & System Design)',
            'ML': 'Data Scientist & Machine Learning Engineer',
            'HR': 'HR Specialist & Behavioral Lead'
        };

        categorySelect.addEventListener('change', () => {
            const selectedVal = categorySelect.value;
            if (categoryRoleMap[selectedVal]) {
                targetRoleInput.value = categoryRoleMap[selectedVal];
            }
        });
    }

    const questionCards = document.querySelectorAll('.question-card');
    if (!questionCards.length) return;

    // 2. Text To Speech helper
    const speakBtnList = document.querySelectorAll('.speak-question-btn');
    speakBtnList.forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.getAttribute('data-text');
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel(); // Stop any active speech
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            } else {
                alert('Text-to-speech is not supported in your browser.');
            }
        });
    });

    // 3. Answer AJAX Submission
    document.querySelectorAll('.submit-answer-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const responseId = btn.getAttribute('data-response-id');
            const sessionId = btn.getAttribute('data-session-id');
            const textarea = document.getElementById(`answer-input-${responseId}`);
            const userAnswer = textarea.value.trim();

            if (!userAnswer) {
                alert('Please type or dictate your answer before submitting.');
                return;
            }

            // Disable button & show spinner
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>AI Evaluating...`;

            try {
                const res = await fetch('/api/v1/interview/answer/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        response_id: responseId,
                        user_answer: userAnswer
                    })
                });

                const data = await res.json();
                if (data.success) {
                    // Render evaluation result card
                    const evalBox = document.getElementById(`eval-result-${responseId}`);
                    evalBox.style.display = 'block';

                    evalBox.innerHTML = `
                        <div class="alert alert-dark border-primary mt-3 glass-card p-4">
                            <div class="d-flex align-items-center justify-content-between mb-3">
                                <h5 class="text-primary mb-0"><i class="bi bi-cpu me-2"></i>AI Evaluation Result</h5>
                                <span class="badge bg-primary fs-6">Score: ${data.score}/100</span>
                            </div>
                            <p class="mb-2"><strong>Feedback:</strong> ${data.feedback}</p>
                            <div class="mb-3">
                                <strong>Missing Key Concepts:</strong><br>
                                ${data.missing_concepts.map(c => `<span class="skill-pill missing me-1 mt-1">${c}</span>`).join('')}
                            </div>
                            <div class="p-3 rounded bg-dark border border-secondary text-light">
                                <strong>Model Senior Answer:</strong><br>
                                <small class="text-muted">${data.model_answer}</small>
                            </div>
                        </div>
                    `;

                    btn.classList.remove('btn-primary-glow');
                    btn.classList.add('btn-success');
                    btn.innerHTML = `<i class="bi bi-check-circle me-1"></i> Answer Evaluated`;
                } else {
                    alert(data.error || 'Evaluation failed.');
                    btn.disabled = false;
                    btn.innerHTML = 'Submit Answer';
                }
            } catch (err) {
                console.error(err);
                alert('Network error occurred.');
                btn.disabled = false;
                btn.innerHTML = 'Submit Answer';
            }
        });
    });
});
