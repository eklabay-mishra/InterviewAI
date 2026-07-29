/* MCQ Timed Test Suite with Next/Previous Navigation & Question Palette */

document.addEventListener('DOMContentLoaded', () => {
    const mcqForm = document.getElementById('mcq-test-form');
    if (!mcqForm) return;

    const durationMinutes = parseInt(mcqForm.getAttribute('data-duration') || '30', 10);
    const testId = mcqForm.getAttribute('data-test-id');
    const totalQuestions = parseInt(mcqForm.getAttribute('data-total-questions') || '20', 10);
    const timerDisplay = document.getElementById('timer-countdown');

    const prevBtn = document.getElementById('prev-q-btn');
    const nextBtn = document.getElementById('next-q-btn');
    const submitBtn = document.getElementById('submit-mcq-btn');
    const currentQNumSpan = document.getElementById('current-q-num');
    const answeredCountSpan = document.getElementById('answered-count-status');

    let currentQuestionIndex = 0;
    const answeredQuestions = new Set();

    // Show specified question index (0-based)
    function showQuestion(index) {
        if (index < 0 || index >= totalQuestions) return;

        // Hide all cards
        document.querySelectorAll('.question-card').forEach((card, idx) => {
            card.style.display = (idx === index) ? 'block' : 'none';
        });

        currentQuestionIndex = index;
        const currentNum = index + 1;

        if (currentQNumSpan) {
            currentQNumSpan.textContent = currentNum;
        }

        // Update Previous Button
        if (prevBtn) {
            prevBtn.disabled = (index === 0);
        }

        // Update Next / Submit Buttons
        if (index === totalQuestions - 1) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (submitBtn) submitBtn.style.display = 'inline-block';
        } else {
            if (nextBtn) nextBtn.style.display = 'inline-block';
            if (submitBtn) submitBtn.style.display = 'none';
        }

        // Update Question Palette Pills
        document.querySelectorAll('.q-palette-pill').forEach((btn, idx) => {
            btn.classList.remove('btn-primary', 'active-q');
            if (idx === index) {
                btn.classList.add('btn-primary', 'active-q');
            } else if (answeredQuestions.has(idx + 1)) {
                btn.classList.remove('btn-outline-secondary');
                btn.classList.add('btn-success');
            } else {
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-secondary');
            }
        });
    }

    // Button event listeners
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentQuestionIndex < totalQuestions - 1) {
                showQuestion(currentQuestionIndex + 1);
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentQuestionIndex > 0) {
                showQuestion(currentQuestionIndex - 1);
            }
        });
    }

    // Palette pill click delegation
    document.querySelectorAll('.q-palette-pill').forEach((pill) => {
        pill.addEventListener('click', () => {
            const qIndex = parseInt(pill.getAttribute('data-q-index'), 10);
            showQuestion(qIndex);
        });
    });

    // Track answer selections
    document.querySelectorAll('.mcq-radio').forEach((radio) => {
        radio.addEventListener('change', () => {
            const qNum = parseInt(radio.getAttribute('data-q-num'), 10);
            answeredQuestions.add(qNum);

            // Update palette pill styling
            const paletteBtn = document.getElementById(`palette-btn-${qNum}`);
            if (paletteBtn && qNum - 1 !== currentQuestionIndex) {
                paletteBtn.classList.remove('btn-outline-secondary');
                paletteBtn.classList.add('btn-success');
            }

            if (answeredCountSpan) {
                answeredCountSpan.textContent = `${answeredQuestions.size} of ${totalQuestions} Questions Answered`;
            }
        });
    });

    // Timer countdown
    let totalSeconds = durationMinutes * 60;
    const timerInterval = setInterval(() => {
        if (totalSeconds <= 0) {
            clearInterval(timerInterval);
            alert('Time is up! Auto-submitting your test...');
            submitMcqForm();
            return;
        }

        totalSeconds--;
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        if (timerDisplay) {
            timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }, 1000);

    async function submitMcqForm() {
        const answers = {};
        const inputs = mcqForm.querySelectorAll('input[type="radio"]:checked');
        inputs.forEach(input => {
            const qId = input.name.replace('question_', '');
            answers[qId] = input.value;
        });

        try {
            const res = await fetch('/api/v1/mcq/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    test_id: testId,
                    answers: answers
                })
            });

            const data = await res.json();
            if (data.success) {
                const resultsContainer = document.getElementById('mcq-results-container');
                mcqForm.style.display = 'none';
                if (resultsContainer) {
                    resultsContainer.style.display = 'block';
                    resultsContainer.innerHTML = `
                        <div class="glass-card p-5 text-center my-4">
                            <div class="mb-3">
                                <i class="bi bi-trophy text-warning display-3"></i>
                            </div>
                            <h2 class="text-white font-weight-bold">MCQ Assessment Completed!</h2>
                            <p class="text-muted">Here is your automated score summary for ${data.total_questions} questions:</p>
                            
                            <div class="d-flex justify-content-center gap-4 my-4">
                                <div class="p-3 bg-dark rounded border border-secondary text-center" style="min-width: 140px;">
                                    <div class="fs-2 text-primary font-weight-bold">${data.score}%</div>
                                    <div class="text-muted small">Final Score</div>
                                </div>
                                <div class="p-3 bg-dark rounded border border-secondary text-center" style="min-width: 140px;">
                                    <div class="fs-2 text-success font-weight-bold">${data.correct_answers} / ${data.total_questions}</div>
                                    <div class="text-muted small">Correct Answers</div>
                                </div>
                            </div>

                            <a href="/candidate/mcq-tests" class="btn btn-primary-glow px-4">Back to MCQ Library</a>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error(err);
            alert('Failed to submit test.');
        }
    }

    mcqForm.addEventListener('submit', (e) => {
        e.preventDefault();
        clearInterval(timerInterval);
        submitMcqForm();
    });

    // Initialize first question
    showQuestion(0);
});
