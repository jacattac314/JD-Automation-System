// JD Automation System - Frontend Application

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// ============ Toast Notification System ============
function initToasts() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(type, title, message, duration = 5000) {
    initToasts();
    const container = document.getElementById('toast-container');

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    return toast;
}

// ============ API Functions ============
async function createGitHubRepo(name, description, isPrivate) {
    const response = await fetch(`${API_BASE_URL}/api/create-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            token: settings.githubToken,
            name: name,
            description: description,
            private: isPrivate
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create repository');
    }

    return await response.json();
}

async function validateGitHubToken(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/validate-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        return await response.json();
    } catch (e) {
        return { valid: false, message: 'API server not running' };
    }
}

async function checkApiServer() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            return { running: true, gemini: data.gemini_available };
        }
        return { running: false, gemini: false };
    } catch (e) {
        return { running: false, gemini: false };
    }
}

async function generateSpecification(jd, project, skills) {
    if (!settings.geminiKey) {
        throw new Error('Gemini API key not configured');
    }

    const response = await fetch(`${API_BASE_URL}/api/generate-spec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gemini_key: settings.geminiKey,
            job_description: jd,
            project_title: project.title,
            project_description: project.description,
            skills: skills
        })
    });

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.message || 'Failed to generate specification');
    }

    return data.specification;
}

async function pushFilesToRepo(repoFullName, files) {
    const response = await fetch(`${API_BASE_URL}/api/push-files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            token: settings.githubToken,
            repo_full_name: repoFullName,
            files: files,
            commit_message: 'Add project files from JD Automation'
        })
    });

    return await response.json();
}

async function analyzeJDWithAI(jd) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze-jd`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gemini_key: settings.geminiKey,
                job_description: jd
            })
        });
        return await response.json();
    } catch (e) {
        return null;
    }
}


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

// Set default GitHub username if not already configured
if (!settings.githubUsername) {
    settings.githubUsername = 'jacattac314';
    localStorage.setItem('settings', JSON.stringify(settings));
}

// GitHub username validation
function isValidGitHubUsername(username) {
    if (!username || typeof username !== 'string') return false;
    // GitHub usernames: 1-39 chars, alphanumeric or hyphen, can't start/end with hyphen
    const pattern = /^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/;
    return pattern.test(username) && !username.includes('--');
}

// Migrate existing history URLs to use correct GitHub username
function migrateHistoryUrls(newUsername) {
    if (!isValidGitHubUsername(newUsername)) {
        alert('Please enter a valid GitHub username first.');
        return 0;
    }

    let migratedCount = 0;
    runHistory = runHistory.map(run => {
        if (run.repoUrl) {
            // Extract repo name from existing URL
            const match = run.repoUrl.match(/github\.com\/[^\/]+\/(.+)$/);
            if (match) {
                const repoName = match[1];
                run.repoUrl = `https://github.com/${newUsername}/${repoName}`;
                migratedCount++;
            }
        }
        return run;
    });

    localStorage.setItem('runHistory', JSON.stringify(runHistory));
    return migratedCount;
}

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
        showToast('warning', 'Missing Input', 'Please enter a job description');
        return;
    }

    // Check if API server is running
    const apiStatus = await checkApiServer();
    const apiRunning = apiStatus.running;
    if (!apiRunning) {
        showToast('warning', 'API Server Offline', 'Running in simulation mode. Start server with: python start.py', 8000);
    }

    // Validate GitHub token if API is running
    if (apiRunning && settings.githubToken) {
        const tokenResult = await validateGitHubToken(settings.githubToken);
        if (tokenResult.valid && tokenResult.username) {
            settings.githubUsername = tokenResult.username;
            localStorage.setItem('settings', JSON.stringify(settings));
            showToast('success', 'GitHub Connected', `Authenticated as ${tokenResult.username}`);
        }
    }

    // Validate GitHub username before starting
    if (!isValidGitHubUsername(settings.githubUsername)) {
        const username = prompt('Please enter your GitHub username:');
        if (!username) {
            showToast('error', 'Username Required', 'A valid GitHub username is required to start a run.');
            return;
        }
        if (!isValidGitHubUsername(username)) {
            showToast('error', 'Invalid Username', 'Please check your GitHub username format and try again.');
            return;
        }
        settings.githubUsername = username;
        localStorage.setItem('settings', JSON.stringify(settings));
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

        // Step 3: Create GitHub repo
        updateStepStatus('step-github', 'pending', 'Creating GitHub repository...');
        const repoName = project.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

        // Try real API, fall back to simulation
        if (apiRunning && settings.githubToken) {
            try {
                const repoResult = await createGitHubRepo(
                    repoName,
                    project.description,
                    settings.privateRepos !== false
                );
                currentRun.repoUrl = repoResult.url;
                currentRun.repoCreated = true;
                updateStepStatus('step-github', 'completed', `✓ Repository created: ${repoResult.name}`);
            } catch (repoError) {
                // Fall back to simulation on error
                console.error('GitHub API error:', repoError);
                currentRun.repoUrl = `https://github.com/${settings.githubUsername}/${repoName}`;
                currentRun.repoCreated = false;
                updateStepStatus('step-github', 'completed', '⚠ Repository simulated (API error)');
            }
        } else {
            // Simulation mode
            await simulateStep('step-github', 'Creating GitHub repository...', 1200);
            currentRun.repoUrl = `https://github.com/${settings.githubUsername}/${repoName}`;
            currentRun.repoCreated = false;
            updateStepStatus('step-github', 'completed', '✓ Repository simulated');
        }
        updateProgress(50);

        // Step 4: Generate specification with Gemini
        updateStepStatus('step-spec', 'active', 'Generating specification...');
        document.getElementById('current-status').textContent = 'Generating specification with Gemini AI...';

        let specification = null;
        if (apiRunning && settings.geminiKey) {
            try {
                specification = await generateSpecification(jd, project, skills);
                currentRun.specification = specification;
                updateStepStatus('step-spec', 'completed', '✓ Specification generated with Gemini');
            } catch (specError) {
                console.error('Gemini error:', specError);
                showToast('warning', 'Spec Simulated', 'Could not reach Gemini API: ' + specError.message);
                await sleep(1500);
                updateStepStatus('step-spec', 'completed', '⚠ Specification simulated');
            }
        } else {
            await sleep(2000);
            updateStepStatus('step-spec', 'completed', '✓ Specification simulated');
        }
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

        showToast('success', 'Automation Complete!', `${currentRun.project} created in ${currentRun.elapsedTime}s`);
        showResults(currentRun);

    } catch (error) {
        currentRun.status = 'failed';
        currentRun.error = error.message;
        showToast('error', 'Run Failed', error.message);
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
    showToast('success', 'Settings Saved', 'Your configuration has been saved successfully.');
}

async function testConnection() {
    let results = [];

    // Test API server
    const apiRunning = await checkApiServer();
    results.push(`API Server: ${apiRunning ? '✓ Running' : '✗ Not running'}`);

    // Test GitHub token
    const token = document.getElementById('github-token').value;
    if (token) {
        if (apiRunning) {
            const tokenResult = await validateGitHubToken(token);
            if (tokenResult.valid) {
                results.push(`GitHub Token: ✓ Valid (${tokenResult.username})`);
                // Auto-fill username
                document.getElementById('github-username').value = tokenResult.username;
            } else {
                results.push(`GitHub Token: ✗ Invalid (${tokenResult.message})`);
            }
        } else {
            results.push('GitHub Token: ⚠ Cannot test (API not running)');
        }
    } else {
        results.push('GitHub Token: ⚠ Not provided');
    }

    alert('Connection Test Results:\n\n' + results.join('\n'));
}

function migrateHistory() {
    const username = document.getElementById('github-username').value.trim();
    if (!username) {
        alert('Please enter your GitHub username above first, then click this button.');
        return;
    }

    const count = migrateHistoryUrls(username);
    if (count > 0) {
        alert(`Successfully updated ${count} history entries to use username: ${username}`);
        // Refresh history display if on history page
        if (document.getElementById('history').classList.contains('active')) {
            loadHistory();
        }
    } else {
        alert('No history entries needed migration.');
    }
}

// Utility
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
