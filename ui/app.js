// JD Automation System - Frontend Application

// Sample job description
const SAMPLE_JD = `Senior Full-Stack Software Engineer

About the Role:
We're seeking an experienced Full-Stack Software Engineer to join our growing team. You'll be responsible for building scalable web applications and APIs.

Requirements:
- 5+ years of professional software development experience
- Strong proficiency in Python and modern JavaScript
- Experience with React and Node.js
- Database design and optimization (PostgreSQL, MongoDB)
- RESTful API development
- Cloud platforms (AWS preferred)
- Git version control
- Agile/Scrum methodologies

Responsibilities:
- Design and implement new features
- Write clean, maintainable code
- Participate in code reviews
- Collaborate with cross-functional teams
- Optimize application performance
- Mentor junior developers

Nice to Have:
- Docker and Kubernetes experience
- CI/CD pipeline setup
- Machine learning basics
- TypeScript
- GraphQL`;

// Tech keywords for skill extraction
const TECH_KEYWORDS = [
    "python", "javascript", "java", "c++", "c#", "go", "rust", "ruby", "php",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "git", "ci/cd", "jenkins", "github actions",
    "machine learning", "deep learning", "ai", "nlp", "computer vision",
    "rest", "graphql", "microservices", "api",
    "agile", "scrum", "tdd", "unit testing",
    "typescript", "html", "css"
];

// Project templates
const PROJECT_TEMPLATES = {
    web: [
        { title: "Real-time Collaboration Platform", description: "Full-stack web app with real-time features" },
        { title: "E-Commerce Product Dashboard", description: "Complete e-commerce backend with inventory management" },
        { title: "Task Management System", description: "Feature-rich project management tool" }
    ],
    data: [
        { title: "Predictive Analytics Dashboard", description: "ML-powered analytics platform" },
        { title: "NLP Sentiment Analysis API", description: "Natural language processing service" }
    ],
    cloud: [
        { title: "Multi-Cloud Infrastructure Manager", description: "IaC solution for managing cloud resources" },
        { title: "Automated CI/CD Pipeline", description: "Complete DevOps pipeline" }
    ]
};

// State
let runHistory = JSON.parse(localStorage.getItem('runHistory') || '[]');
let settings = JSON.parse(localStorage.getItem('settings') || '{}');
let currentRun = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    updateDashboard();
    setupNavigation();
});

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            showView(view);
        });
    });
}

function showView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`)?.classList.add('active');

    // Update header
    const titles = {
        'dashboard': 'Dashboard',
        'new-run': 'New Automation Run',
        'history': 'Run History',
        'settings': 'Settings'
    };
    document.querySelector('.header-title h1').textContent = titles[viewName] || 'Dashboard';

    // Load specific view data
    if (viewName === 'history') loadHistory();
    if (viewName === 'settings') loadSettingsForm();
}

// Dashboard
function updateDashboard() {
    const total = runHistory.length;
    const successful = runHistory.filter(r => r.status === 'success').length;
    const avgTime = total > 0
        ? (runHistory.reduce((sum, r) => sum + (r.elapsedTime || 0), 0) / total).toFixed(1)
        : 0;
    const totalSkills = runHistory.reduce((sum, r) => sum + (r.skills?.length || 0), 0);

    document.getElementById('total-runs').textContent = total;
    document.getElementById('successful-runs').textContent = successful;
    document.getElementById('avg-time').textContent = `${avgTime}s`;
    document.getElementById('skills-extracted').textContent = totalSkills;

    // Recent runs
    const recentRuns = document.getElementById('recent-runs');
    if (runHistory.length === 0) {
        recentRuns.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📭</span>
                <p>No runs yet. Start your first automation!</p>
                <button class="btn btn-primary" onclick="showView('new-run')">Create New Run</button>
            </div>
        `;
    } else {
        recentRuns.innerHTML = runHistory.slice(-5).reverse().map(run => `
            <div class="run-item">
                <div class="run-status-icon ${run.status}">
                    ${run.status === 'success' ? '✅' : '❌'}
                </div>
                <div class="run-info">
                    <div class="run-title">${run.project || 'Unknown Project'}</div>
                    <div class="run-meta">${run.timestamp} • ${run.elapsedTime || 0}s</div>
                </div>
                ${run.repoUrl ? `<div class="run-actions"><a href="${run.repoUrl}" target="_blank">View Repo →</a></div>` : ''}
            </div>
        `).join('');
    }
}

// Load sample JD
function loadSampleJD() {
    document.getElementById('jd-input').value = SAMPLE_JD;
}

// Extract skills
function extractSkills(jd) {
    const jdLower = jd.toLowerCase();
    const skills = [];

    TECH_KEYWORDS.forEach(keyword => {
        if (jdLower.includes(keyword)) {
            skills.push(properCase(keyword));
        }
    });

    return [...new Set(skills)].sort();
}

function properCase(keyword) {
    const casing = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "node.js": "Node.js",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "graphql": "GraphQL",
        "ci/cd": "CI/CD",
        "aws": "AWS",
        "gcp": "GCP",
        "api": "API",
        "nlp": "NLP",
        "ai": "AI",
        "tdd": "TDD"
    };
    return casing[keyword.toLowerCase()] || keyword.charAt(0).toUpperCase() + keyword.slice(1);
}

// Generate project idea
function generateProjectIdea(skills) {
    const skillsLower = skills.map(s => s.toLowerCase());

    // Categorize
    const mlCount = skillsLower.filter(s =>
        ["python", "machine learning", "deep learning", "ai", "nlp"].includes(s)).length;
    const cloudCount = skillsLower.filter(s =>
        ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"].includes(s)).length;

    let category = 'web';
    if (mlCount >= 2) category = 'data';
    else if (cloudCount >= 2) category = 'cloud';

    const templates = PROJECT_TEMPLATES[category];
    return templates[Math.floor(Math.random() * templates.length)];
}

// Start run
async function startRun() {
    const jd = document.getElementById('jd-input').value.trim();

    if (!jd) {
        alert('Please enter a job description');
        return;
    }

    // Show progress section
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';

    const startTime = Date.now();
    currentRun = {
        id: `run_${startTime}`,
        timestamp: new Date().toLocaleString(),
        status: 'running'
    };

    try {
        // Step 1: Extract skills
        await simulateStep('step-analysis', 'Analyzing job description...', 1000);
        const skills = extractSkills(jd);
        currentRun.skills = skills;
        updateStepStatus('step-analysis', 'completed', `✓ Found ${skills.length} skills`);
        updateProgress(16);

        // Step 2: Generate project idea
        await simulateStep('step-ideation', 'Generating project idea...', 800);
        const project = generateProjectIdea(skills);
        currentRun.project = project.title;
        currentRun.description = project.description;
        updateStepStatus('step-ideation', 'completed', `✓ ${project.title}`);
        updateProgress(33);

        // Step 3: Create GitHub repo (simulated)
        await simulateStep('step-github', 'Creating GitHub repository...', 1200);
        const repoName = project.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
        currentRun.repoUrl = `https://github.com/${settings.githubUsername || 'user'}/${repoName}`;
        updateStepStatus('step-github', 'completed', '✓ Repository created');
        updateProgress(50);

        // Step 4: Generate spec (simulated)
        await simulateStep('step-spec', 'Generating specification with Gemini...', 2000);
        updateStepStatus('step-spec', 'completed', '✓ Specification generated');
        updateProgress(66);

        // Step 5: Implementation (simulated)
        await simulateStep('step-implement', 'AI implementing project...', 3000);
        updateStepStatus('step-implement', 'completed', '✓ Implementation complete');
        updateProgress(83);

        // Step 6: Publish
        await simulateStep('step-publish', 'Publishing to GitHub...', 1000);
        updateStepStatus('step-publish', 'completed', '✓ Published');
        updateProgress(100);

        // Complete
        currentRun.status = 'success';
        currentRun.elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);

        showResults(currentRun);

    } catch (error) {
        currentRun.status = 'failed';
        currentRun.error = error.message;
        document.getElementById('current-status').innerHTML = `<span style="color: var(--error)">❌ Error: ${error.message}</span>`;
    }

    // Save to history
    runHistory.push(currentRun);
    localStorage.setItem('runHistory', JSON.stringify(runHistory));
    updateDashboard();
}

async function simulateStep(stepId, message, duration) {
    updateStepStatus(stepId, 'active', 'Running...');
    document.getElementById('current-status').textContent = message;
    await sleep(duration);
}

function updateStepStatus(stepId, status, text) {
    const step = document.getElementById(stepId);
    step.classList.remove('active', 'completed', 'error');
    step.classList.add(status);

    const statusEl = step.querySelector('.step-status');
    statusEl.className = `step-status ${status}`;
    statusEl.textContent = text || status;
}

function updateProgress(percent) {
    document.getElementById('overall-progress').style.width = `${percent}%`;
}

function showResults(run) {
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('current-status').innerHTML = `<span style="color: var(--success)">✅ Automation completed in ${run.elapsedTime}s!</span>`;

    document.getElementById('results-content').innerHTML = `
        <div class="result-item">
            <span class="result-icon">📁</span>
            <span class="result-label">Project:</span>
            <span class="result-value">${run.project}</span>
        </div>
        <div class="result-item">
            <span class="result-icon">📝</span>
            <span class="result-label">Description:</span>
            <span class="result-value">${run.description}</span>
        </div>
        <div class="result-item">
            <span class="result-icon">🔧</span>
            <span class="result-label">Skills:</span>
            <span class="result-value">${run.skills?.slice(0, 8).join(', ')}</span>
        </div>
        <div class="result-item">
            <span class="result-icon">🔗</span>
            <span class="result-label">Repository:</span>
            <span class="result-value"><a href="${run.repoUrl}" target="_blank">${run.repoUrl}</a></span>
        </div>
        <div class="result-item">
            <span class="result-icon">⏱️</span>
            <span class="result-label">Duration:</span>
            <span class="result-value">${run.elapsedTime}s</span>
        </div>
        
        <div style="margin-top: 24px; text-align: center;">
            <button class="btn btn-primary" onclick="resetRun()">Start New Run</button>
        </div>
    `;
}

function resetRun() {
    document.getElementById('jd-input').value = '';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';

    // Reset all steps
    document.querySelectorAll('.progress-step').forEach(step => {
        step.classList.remove('active', 'completed', 'error');
        step.querySelector('.step-status').className = 'step-status pending';
        step.querySelector('.step-status').textContent = 'Pending';
    });

    updateProgress(0);
    document.getElementById('current-status').textContent = 'Ready to start...';
}

// History
function loadHistory() {
    const historyList = document.getElementById('history-list');

    if (runHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📜</span>
                <p>No run history yet</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = runHistory.slice().reverse().map(run => `
        <div class="run-item">
            <div class="run-status-icon ${run.status}">
                ${run.status === 'success' ? '✅' : '❌'}
            </div>
            <div class="run-info">
                <div class="run-title">${run.project || 'Unknown Project'}</div>
                <div class="run-meta">
                    ${run.timestamp} • ${run.elapsedTime || 0}s • 
                    ${run.skills?.length || 0} skills extracted
                </div>
            </div>
            ${run.repoUrl ? `<div class="run-actions"><a href="${run.repoUrl}" target="_blank">View Repo →</a></div>` : ''}
        </div>
    `).join('');
}

// Settings
function loadSettings() {
    settings = JSON.parse(localStorage.getItem('settings') || '{}');
}

function loadSettingsForm() {
    document.getElementById('gemini-key').value = settings.geminiKey || '';
    document.getElementById('github-token').value = settings.githubToken || '';
    document.getElementById('github-username').value = settings.githubUsername || '';
    document.getElementById('anthropic-key').value = settings.anthropicKey || '';
    document.getElementById('private-repos').checked = settings.privateRepos !== false;
    document.getElementById('enable-linkedin').checked = settings.enableLinkedin || false;
}

function saveSettings() {
    settings = {
        geminiKey: document.getElementById('gemini-key').value,
        githubToken: document.getElementById('github-token').value,
        githubUsername: document.getElementById('github-username').value,
        anthropicKey: document.getElementById('anthropic-key').value,
        privateRepos: document.getElementById('private-repos').checked,
        enableLinkedin: document.getElementById('enable-linkedin').checked
    };

    localStorage.setItem('settings', JSON.stringify(settings));
    alert('Settings saved successfully!');
}

function testConnection() {
    alert('Connection test would verify API keys here.\n\nIn full version, this tests:\n• Gemini API\n• GitHub API\n• Anthropic API');
}

// Utility
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
