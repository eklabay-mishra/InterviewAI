/* Chart.js Visualizations for Candidate & Recruiter Dashboards */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Candidate Dashboard Charts
    const candidateProgressionCanvas = document.getElementById('candidateProgressionChart');
    const candidateSkillsCanvas = document.getElementById('candidateSkillsChart');

    if (candidateProgressionCanvas && candidateSkillsCanvas) {
        fetch('/api/v1/analytics/candidate')
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;

                new Chart(candidateProgressionCanvas, {
                    type: 'line',
                    data: {
                        labels: data.progression.labels,
                        datasets: [{
                            label: 'AI Interview Score (%)',
                            data: data.progression.scores,
                            borderColor: '#6366F1',
                            backgroundColor: 'rgba(99, 102, 241, 0.15)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 6,
                            pointBackgroundColor: '#6366F1'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: '#CBD5E1' } } },
                        scales: {
                            y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } },
                            x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } }
                        }
                    }
                });

                new Chart(candidateSkillsCanvas, {
                    type: 'radar',
                    data: {
                        labels: data.skills.labels,
                        datasets: [{
                            label: 'Skill Proficiency',
                            data: data.skills.scores,
                            borderColor: '#06B6D4',
                            backgroundColor: 'rgba(6, 182, 212, 0.25)',
                            pointBackgroundColor: '#06B6D4'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            r: {
                                angleLines: { color: 'rgba(255,255,255,0.15)' },
                                grid: { color: 'rgba(255,255,255,0.15)' },
                                pointLabels: { color: '#F8FAFC', font: { size: 12 } },
                                ticks: { display: false }
                            }
                        },
                        plugins: { legend: { labels: { color: '#CBD5E1' } } }
                    }
                });
            });
    }

    // 2. Recruiter SaaS Dashboard - 4 Real DB Charts
    const recruiterTrendCanvas = document.getElementById('recruiterTrendChart');
    const recruiterPerformanceCanvas = document.getElementById('recruiterPerformanceChart');
    const recruiterDistributionCanvas = document.getElementById('recruiterDistributionChart');
    const recruiterSkillsCanvas = document.getElementById('recruiterSkillsChart');
    const recruiterExpCanvas = document.getElementById('recruiterExpChart');
    const recruiterCompletionCanvas = document.getElementById('recruiterCompletionChart');
    const recruiterDeptCanvas = document.getElementById('recruiterDeptChart');

    if (recruiterTrendCanvas || recruiterPerformanceCanvas || recruiterDistributionCanvas || recruiterSkillsCanvas || recruiterDeptCanvas) {
        fetch('/api/v1/analytics/recruiter')
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;

                // Resume Scores by Department Bar Chart (Reference Design)
                if (recruiterDeptCanvas && data.department_scores) {
                    new Chart(recruiterDeptCanvas, {
                        type: 'bar',
                        data: {
                            labels: data.department_scores.labels,
                            datasets: [{
                                label: 'Avg Resume Score',
                                data: data.department_scores.data,
                                backgroundColor: ['#06B6D4', '#818CF8', '#F59E0B', '#10B981', '#EC4899'],
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } },
                                x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } }
                            }
                        }
                    });
                }

                // 1. Interview Trend Line Chart
                if (recruiterTrendCanvas) {
                    new Chart(recruiterTrendCanvas, {
                        type: 'line',
                        data: {
                            labels: data.interview_trend.labels,
                            datasets: [{
                                label: 'Interviews Conducted',
                                data: data.interview_trend.data,
                                borderColor: '#6366F1',
                                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                                fill: true,
                                tension: 0.35,
                                pointRadius: 5,
                                pointBackgroundColor: '#818CF8'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1', precision: 0 } },
                                x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } }
                            }
                        }
                    });
                }

                // 2. Candidate Performance Bar Chart
                if (recruiterPerformanceCanvas) {
                    new Chart(recruiterPerformanceCanvas, {
                        type: 'bar',
                        data: {
                            labels: data.candidate_performance.labels,
                            datasets: [{
                                label: 'Avg Interview Score (%)',
                                data: data.candidate_performance.data,
                                backgroundColor: '#06B6D4',
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } },
                                x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } }
                            }
                        }
                    });
                }

                // 3. Resume Score Distribution Doughnut Chart
                if (recruiterDistributionCanvas) {
                    new Chart(recruiterDistributionCanvas, {
                        type: 'doughnut',
                        data: {
                            labels: data.score_distribution.labels,
                            datasets: [{
                                data: data.score_distribution.data,
                                backgroundColor: ['#10B981', '#6366F1', '#F59E0B', '#EF4444'],
                                borderWidth: 2,
                                borderColor: '#0B0F19'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'bottom', labels: { color: '#CBD5E1' } } }
                        }
                    });
                }

                // 4. Top Technical Skills Bar Chart
                if (recruiterSkillsCanvas) {
                    new Chart(recruiterSkillsCanvas, {
                        type: 'bar',
                        data: {
                            labels: data.top_skills.labels,
                            datasets: [{
                                label: 'Candidates Count',
                                data: data.top_skills.data,
                                backgroundColor: '#8B5CF6',
                                borderRadius: 6
                            }]
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1', precision: 0 } },
                                y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#CBD5E1' } }
                            }
                        }
                    });
                }

                // 5. Candidate Experience Distribution Pie Chart
                if (recruiterExpCanvas && data.experience_distribution) {
                    new Chart(recruiterExpCanvas, {
                        type: 'pie',
                        data: {
                            labels: data.experience_distribution.labels,
                            datasets: [{
                                data: data.experience_distribution.data,
                                backgroundColor: ['#3B82F6', '#10B981', '#F59E0B'],
                                borderWidth: 2,
                                borderColor: '#0B0F19'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'bottom', labels: { color: '#CBD5E1' } } }
                        }
                    });
                }

                // 6. Interview Completion Rate Semi-Gauge Doughnut Chart
                if (recruiterCompletionCanvas && data.completion_rate) {
                    new Chart(recruiterCompletionCanvas, {
                        type: 'doughnut',
                        data: {
                            labels: ['Completed', 'In Progress'],
                            datasets: [{
                                data: [data.completion_rate.completed, data.completion_rate.in_progress],
                                backgroundColor: ['#10B981', '#F59E0B'],
                                borderWidth: 2,
                                borderColor: '#0B0F19'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'bottom', labels: { color: '#CBD5E1' } } }
                        }
                    });
                }
            });
    }
});
