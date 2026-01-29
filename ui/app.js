// JD Automation System - Frontend Application
// Flow: App Idea -> AI Enhancement -> PRD Generation -> GitHub -> Implementation -> Publish

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// ============ Auth State ============
let authToken = localStorage.getItem('authToken') || null;
let currentUser = null;

function getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
}

async function checkAuth() {
    if (!authToken) {
        showAuthUI(false);
        return false;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: getAuthHeaders()
        });
        if (response.ok) {
            currentUser = await response.json();
            showAuthUI(true);
            return true;
        }
        // Token expired or invalid
        authToken = null;
        localStorage.removeItem('authToken');
        showAuthUI(false);
        return false;
    } catch (e) {
        // API not running — show settings-based mode
        showAuthUI(false);
        return false;
    }
}

function showAuthUI(isAuthenticated) {
    const authArea = document.getElementById('auth-area');
    if (!authArea) return;

    if (isAuthenticated && currentUser) {
        authArea.innerHTML = `
            <div class="user-profile">
                <img src="${currentUser.avatar_url || ''}" alt="" class="user-avatar" onerror="this.style.display='none'">
                <span class="user-name">${currentUser.username}</span>
                <button class="btn btn-sm" onclick="logout()">Logout</button>
            </div>
        `;
    } else {
        authArea.innerHTML = `
            <button class="btn btn-primary btn-sm" onclick="loginWithGitHub()">Sign in with GitHub</button>
        `;
    }
}

async function loginWithGitHub() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/github`);
        if (response.ok) {
            const data = await response.json();
            window.location.href = data.authorize_url;
        } else {
            showToast('warning', 'Auth Not Configured', 'GitHub OAuth not configured. Use API keys in Settings.');
        }
    } catch (e) {
        showToast('warning', 'API Offline', 'Cannot connect to API server for authentication.');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    showAuthUI(false);
    showToast('info', 'Logged Out', 'You have been logged out.');
}

// Handle OAuth callback (check URL for auth token)
function handleAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) {
        // Exchange code via the callback endpoint
        fetch(`${API_BASE_URL}/api/auth/callback?code=${code}`)
            .then(r => r.json())
            .then(data => {
                if (data.token) {
                    authToken = data.token;
                    currentUser = data.user;
                    localStorage.setItem('authToken', authToken);
                    showAuthUI(true);
                    showToast('success', 'Signed In', `Welcome, ${data.user.username}!`);
                    // Clean URL
                    window.history.replaceState({}, '', window.location.pathname);
                }
            })
            .catch(e => console.error('Auth callback error:', e));
    }
}

// ============ SSE-Based Pipeline Run ============
async function startRunWithSSE() {
    const appIdea = document.getElementById('idea-input').value.trim();
    const techPrefs = document.getElementById('tech-preferences').value.trim();

    if (!appIdea) {
        showToast('warning', 'Missing Input', 'Please describe your application idea');
        return;
    }

    if (appIdea.length < 20) {
        showToast('warning', 'Too Short', 'Please provide a more detailed description (at least 20 characters)');
        return;
    }

    // Need either auth token or manual API keys
    const hasAuth = !!authToken;
    const hasKeys = settings.geminiKey && settings.githubToken;

    // Validation relaxed to allow backend-configured keys to work
    // if (!hasAuth && !hasKeys) { ... }
    console.log("Proceeding with run (relying on backend configuration if client keys are missing)...");

    // Show progress
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('prd-preview-section').style.display = 'none';

    const startTime = Date.now();
    currentRun = {
        id: `run_${startTime}`,
        timestamp: new Date().toLocaleString(),
        status: 'running'
    };

    try {
        // Start the pipeline via API
        const response = await fetch(`${API_BASE_URL}/api/run`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                gemini_key: settings.geminiKey || '',
                github_token: settings.githubToken || '',
                github_username: settings.githubUsername || '',
                app_idea: appIdea,
                tech_preferences: techPrefs || null,
                private: settings.privateRepos !== false
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to start pipeline');
        }

        const { run_id } = await response.json();
        currentRun.id = run_id;

        // Connect to SSE stream for real-time updates
        document.getElementById('current-status').textContent = 'Pipeline started — streaming progress...';
        const eventSource = new EventSource(`${API_BASE_URL}/api/run/${run_id}/stream`);

        const stepMapping = {
            'enhance_idea': 'step-enhance',
            'generate_prd': 'step-prd',
            'create_repo': 'step-github',
            'extract_features': 'step-features',
            'implement': 'step-implement',
            'publish': 'step-publish'
        };

        const stepProgress = {
            'enhance_idea': 16,
            'generate_prd': 33,
            'create_repo': 50,
            'extract_features': 66,
            'implement': 83,
            'publish': 95,
            'pipeline': 100
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const step = data.step;
                const status = data.status;
                const detail = data.detail || '';

                // Update step UI
                const stepId = stepMapping[step];
                if (stepId) {
                    if (status === 'in_progress') {
                        updateStepStatus(stepId, 'active', detail);
                    } else if (status === 'completed') {
                        updateStepStatus(stepId, 'completed', `✓ ${detail}`);
                    } else if (status === 'failed') {
                        updateStepStatus(stepId, 'error', `✗ ${detail}`);
                    }
                }

                // Update progress bar
                const progress = stepProgress[step];
                if (progress) {
                    updateProgress(status === 'completed' ? progress : Math.max(progress - 10, 0));
                }

                // Update status text
                document.getElementById('current-status').textContent = detail;

                // Show PRD preview when available
                if (step === 'generate_prd' && status === 'completed' && data.data?.prd_markdown) {
                    document.getElementById('prd-preview-section').style.display = 'block';
                    document.getElementById('prd-preview-content').innerHTML =
                        `<pre style="white-space: pre-wrap; font-size: 0.85em; max-height: 400px; overflow-y: auto;">${escapeHtml(data.data.prd_markdown)}</pre>`;
                }

                // Update run data from events
                if (data.data?.epics_count) currentRun.epicsCount = data.data.epics_count;
                if (data.data?.features_count) currentRun.featuresCount = data.data.features_count;
                if (data.data?.name) currentRun.repoUrl = data.data.url;

                // Pipeline finished
                if (step === 'pipeline') {
                    eventSource.close();

                    if (status === 'completed') {
                        currentRun.status = 'success';
                        currentRun.elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);

                        // Fetch final run data
                        fetch(`${API_BASE_URL}/api/run/${run_id}`)
                            .then(r => r.json())
                            .then(runData => {
                                if (runData.result) {
                                    currentRun.projectTitle = runData.result.project_title || currentRun.projectTitle;
                                    currentRun.repoUrl = runData.result.repo_url || currentRun.repoUrl;
                                    currentRun.epicsCount = runData.result.epics_count || currentRun.epicsCount;
                                    currentRun.featuresCount = runData.result.features_count || currentRun.featuresCount;
                                }
                                showResults(currentRun);
                                showToast('success', 'Build Complete!',
                                    `${currentRun.projectTitle || 'Project'} created in ${currentRun.elapsedTime}s`);
                            })
                            .catch(() => showResults(currentRun));
                    } else {
                        currentRun.status = 'failed';
                        currentRun.error = detail;
                        showToast('error', 'Pipeline Failed', detail);
                        document.getElementById('current-status').innerHTML =
                            `<span style="color: var(--error)">Pipeline failed: ${escapeHtml(detail)}</span>`;
                    }

                    // Save to history
                    runHistory.push(currentRun);
                    localStorage.setItem('runHistory', JSON.stringify(runHistory));
                    updateDashboard();
                }
            } catch (e) {
                console.error('SSE parse error:', e);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            // If we haven't gotten a completion event, check the run status
            fetch(`${API_BASE_URL}/api/run/${run_id}`)
                .then(r => r.json())
                .then(runData => {
                    if (runData.status === 'completed' || runData.status === 'failed') {
                        // Already handled
                    } else {
                        document.getElementById('current-status').textContent =
                            'Connection lost — check run status in History';
                    }
                })
                .catch(() => {
                    document.getElementById('current-status').textContent =
                        'Connection lost — pipeline may still be running on the server';
                });
        };

    } catch (error) {
        // Fall back to the original step-by-step method
        console.warn('SSE pipeline failed, falling back to step-by-step mode:', error.message);
        await startRunLegacy();
    }
}

// Rename old startRun to startRunLegacy as fallback

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

// ============ Sample Idea ============
const SAMPLE_IDEA = `A project management tool for remote teams that integrates with Slack, supports Kanban boards, time tracking, and automated daily standups via AI summarization.

The tool should allow team leads to create projects, assign tasks with priorities and deadlines, and visualize progress through burndown charts. Team members should get notifications when assigned tasks or when deadlines approach.

Key features: drag-and-drop Kanban board, time logging per task, AI-generated standup summaries from activity logs, Slack bot integration for task updates, and a dashboard with team analytics.`;

// ============ API Functions ============
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

async function enhanceIdeaAPI(appIdea, techPreferences) {
    const response = await fetch(`${API_BASE_URL}/api/enhance-idea`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gemini_key: settings.geminiKey,
            app_idea: appIdea,
            tech_preferences: techPreferences || null
        })
    });
    return await response.json();
}

async function generatePRDAPI(enhancedIdea) {
    const response = await fetch(`${API_BASE_URL}/api/generate-prd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gemini_key: settings.geminiKey,
            enhanced_idea: enhancedIdea
        })
    });
    return await response.json();
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

// ============ State ============
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

// ============ Initialize ============
document.addEventListener('DOMContentLoaded', () => {
    handleAuthCallback();
    loadSettings();
    updateDashboard();
    setupNavigation();
    checkAuth();
});

// ============ Navigation ============
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
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`)?.classList.add('active');

    const titles = {
        'dashboard': 'Dashboard',
        'new-run': 'Build a New Application',
        'history': 'Run History',
        'settings': 'Settings'
    };
    document.querySelector('.header-title h1').textContent = titles[viewName] || 'Dashboard';

    if (viewName === 'history') loadHistory();
    if (viewName === 'settings') loadSettingsForm();
}

// ============ Dashboard ============
function updateDashboard() {
    const total = runHistory.length;
    const successful = runHistory.filter(r => r.status === 'success').length;
    const avgTime = total > 0
        ? (runHistory.reduce((sum, r) => sum + (r.elapsedTime || 0), 0) / total).toFixed(1)
        : 0;
    const totalFeatures = runHistory.reduce((sum, r) => sum + (r.featuresCount || 0), 0);

    document.getElementById('total-runs').textContent = total;
    document.getElementById('successful-runs').textContent = successful;
    document.getElementById('avg-time').textContent = `${avgTime}s`;
    document.getElementById('total-features').textContent = totalFeatures;

    const recentRuns = document.getElementById('recent-runs');
    if (runHistory.length === 0) {
        recentRuns.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📭</span>
                <p>No runs yet. Start by building your first app!</p>
                <button class="btn btn-primary" onclick="showView('new-run')">Build App</button>
            </div>
        `;
    } else {
        recentRuns.innerHTML = runHistory.slice(-5).reverse().map(run => `
            <div class="run-item">
                <div class="run-status-icon ${run.status}">
                    ${run.status === 'success' ? '✅' : '❌'}
                </div>
                <div class="run-info">
                    <div class="run-title">${run.projectTitle || run.project || 'Unknown Project'}</div>
                    <div class="run-meta">${run.timestamp} • ${run.elapsedTime || 0}s • ${run.epicsCount || 0} epics • ${run.featuresCount || 0} features</div>
                </div>
                ${run.repoUrl ? `<div class="run-actions"><a href="${run.repoUrl}" target="_blank">View Repo →</a></div>` : ''}
            </div>
        `).join('');
    }
}

// ============ Load Sample Idea ============
function loadSampleIdea() {
    document.getElementById('idea-input').value = SAMPLE_IDEA;
}

// ============ PRD Preview Toggle ============
function togglePrdPreview() {
    const content = document.getElementById('prd-preview-content');
    content.style.display = content.style.display === 'none' ? 'block' : 'none';
}

// ============ Fallback: Build enhanced idea client-side ============
function buildFallbackEnhancedIdea(appIdea, techPrefs) {
    const title = appIdea.trim().split('.')[0].split('\n')[0].substring(0, 80) || 'Application Project';
    return {
        title: title,
        description: appIdea,
        target_users: 'End users who need the described functionality',
        problem_statement: appIdea.substring(0, 200),
        key_value_props: ['Solves the core need', 'Modern architecture', 'Production-ready'],
        suggested_tech_stack: {
            frontend: ['React', 'TypeScript'],
            backend: ['Python', 'FastAPI'],
            database: ['PostgreSQL'],
            infrastructure: ['Docker']
        }
    };
}

// ============ Fallback: Build PRD client-side ============
function buildFallbackPRD(enhancedIdea) {
    return {
        prd: {
            product_overview: {
                vision: `Build ${enhancedIdea.title}`,
                goals: ['Deliver core functionality', 'Clean codebase', 'Good documentation'],
                success_metrics: ['All features implemented', 'App runs without errors']
            },
            epics: [
                {
                    name: 'Project Foundation',
                    description: 'Project setup and structure',
                    priority: 'P0',
                    user_stories: [{
                        title: 'Project Setup',
                        story: 'As a developer, I want a structured project so I can develop efficiently',
                        acceptance_criteria: ['Project structure follows best practices'],
                        features: [{ name: 'Scaffolding', description: 'Create project structure', complexity: 'S' }]
                    }]
                },
                {
                    name: 'Core Features',
                    description: 'Primary application functionality',
                    priority: 'P0',
                    user_stories: [{
                        title: 'Core Logic',
                        story: 'As a user, I want the main features so I can accomplish my goals',
                        acceptance_criteria: ['Core functionality works', 'Error handling in place'],
                        features: [
                            { name: 'Business logic', description: 'Main features', complexity: 'L' },
                            { name: 'UI', description: 'User-facing interface', complexity: 'M' }
                        ]
                    }]
                },
                {
                    name: 'Data Layer',
                    description: 'Data storage and access',
                    priority: 'P0',
                    user_stories: [{
                        title: 'Data Persistence',
                        story: 'As a user, I want data to persist so I can access it later',
                        acceptance_criteria: ['Data stored reliably', 'CRUD operations work'],
                        features: [{ name: 'Database', description: 'Data models and access', complexity: 'M' }]
                    }]
                },
                {
                    name: 'Testing',
                    description: 'Automated testing',
                    priority: 'P1',
                    user_stories: [{
                        title: 'Automated Tests',
                        story: 'As a developer, I want tests so I can refactor safely',
                        acceptance_criteria: ['Tests cover core logic'],
                        features: [{ name: 'Unit tests', description: 'Test core modules', complexity: 'M' }]
                    }]
                }
            ]
        },
        prd_markdown: `# PRD: ${enhancedIdea.title}\n\n${enhancedIdea.description}\n\n(Simulated PRD — Gemini API not available)`
    };
}

// ============ Count features from PRD ============
function countFeatures(prd) {
    let count = 0;
    for (const epic of (prd.epics || [])) {
        for (const story of (epic.user_stories || [])) {
            count += (story.features || []).length;
        }
    }
    return count;
}

// ============ Start Run (main entry point — delegates to SSE pipeline) ============
function startRun() {
    return startRunWithSSE();
}

async function startRunLegacy() {
    const appIdea = document.getElementById('idea-input').value.trim();
    const techPrefs = document.getElementById('tech-preferences').value.trim();

    if (!appIdea) {
        showToast('warning', 'Missing Input', 'Please describe your application idea');
        return;
    }

    // Check API server
    const apiStatus = await checkApiServer();
    const apiRunning = apiStatus.running;
    if (!apiRunning) {
        showToast('warning', 'API Server Offline', 'Running in simulation mode. Start server with: python start.py', 8000);
    }

    // Validate GitHub token
    if (apiRunning && settings.githubToken) {
        const tokenResult = await validateGitHubToken(settings.githubToken);
        if (tokenResult.valid && tokenResult.username) {
            settings.githubUsername = tokenResult.username;
            localStorage.setItem('settings', JSON.stringify(settings));
            showToast('success', 'GitHub Connected', `Authenticated as ${tokenResult.username}`);
        }
    }

    // Validate GitHub username
    if (!isValidGitHubUsername(settings.githubUsername)) {
        const username = prompt('Please enter your GitHub username:');
        if (!username || !isValidGitHubUsername(username)) {
            showToast('error', 'Invalid Username', 'A valid GitHub username is required.');
            return;
        }
        settings.githubUsername = username;
        localStorage.setItem('settings', JSON.stringify(settings));
    }

    // Show progress
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('prd-preview-section').style.display = 'none';

    const startTime = Date.now();
    currentRun = {
        id: `run_${startTime}`,
        timestamp: new Date().toLocaleString(),
        status: 'running'
    };

    try {
        // Step 1: Enhance idea with AI
        updateStepStatus('step-enhance', 'active', 'Enhancing idea...');
        document.getElementById('current-status').textContent = 'AI is enhancing your application idea...';
        let enhancedIdea;

        if (apiRunning && settings.geminiKey) {
            try {
                const enhanceResult = await enhanceIdeaAPI(appIdea, techPrefs);
                if (enhanceResult.success && enhanceResult.enhanced_idea) {
                    enhancedIdea = enhanceResult.enhanced_idea;
                    updateStepStatus('step-enhance', 'completed', `✓ Enhanced: ${enhancedIdea.title}`);
                } else {
                    showToast('warning', 'Enhancement Simulated', enhanceResult.message || 'Using local enhancement');
                    enhancedIdea = buildFallbackEnhancedIdea(appIdea, techPrefs);
                    updateStepStatus('step-enhance', 'completed', '⚠ Enhanced (simulated)');
                }
            } catch (err) {
                console.error('Enhance idea error:', err);
                enhancedIdea = buildFallbackEnhancedIdea(appIdea, techPrefs);
                updateStepStatus('step-enhance', 'completed', '⚠ Enhanced (simulated)');
            }
        } else {
            await sleep(1500);
            enhancedIdea = buildFallbackEnhancedIdea(appIdea, techPrefs);
            updateStepStatus('step-enhance', 'completed', '✓ Enhanced (simulated)');
        }

        currentRun.projectTitle = enhancedIdea.title;
        currentRun.description = enhancedIdea.description;
        currentRun.enhancedIdea = enhancedIdea;
        updateProgress(16);

        // Step 2: Generate PRD with epics and user stories
        updateStepStatus('step-prd', 'active', 'Generating PRD...');
        document.getElementById('current-status').textContent = 'Gemini AI is generating the PRD with epics and user stories...';
        let prdResult;

        if (apiRunning && settings.geminiKey) {
            try {
                prdResult = await generatePRDAPI(enhancedIdea);
                if (prdResult.success && prdResult.prd) {
                    const epicCount = (prdResult.prd.epics || []).length;
                    const featureCount = countFeatures(prdResult.prd);
                    updateStepStatus('step-prd', 'completed', `✓ PRD: ${epicCount} epics, ${featureCount} features`);
                } else {
                    showToast('warning', 'PRD Simulated', prdResult.message || 'Using local PRD');
                    prdResult = buildFallbackPRD(enhancedIdea);
                    updateStepStatus('step-prd', 'completed', '⚠ PRD generated (simulated)');
                }
            } catch (err) {
                console.error('Generate PRD error:', err);
                prdResult = buildFallbackPRD(enhancedIdea);
                updateStepStatus('step-prd', 'completed', '⚠ PRD generated (simulated)');
            }
        } else {
            await sleep(2000);
            prdResult = buildFallbackPRD(enhancedIdea);
            updateStepStatus('step-prd', 'completed', '✓ PRD generated (simulated)');
        }

        currentRun.prd = prdResult.prd;
        currentRun.prdMarkdown = prdResult.prd_markdown;
        currentRun.epicsCount = (prdResult.prd.epics || []).length;
        currentRun.featuresCount = countFeatures(prdResult.prd);
        updateProgress(33);

        // Show PRD preview
        if (prdResult.prd_markdown) {
            document.getElementById('prd-preview-section').style.display = 'block';
            document.getElementById('prd-preview-content').innerHTML =
                `<pre style="white-space: pre-wrap; font-size: 0.85em; max-height: 400px; overflow-y: auto;">${escapeHtml(prdResult.prd_markdown)}</pre>`;
        }

        // Step 3: Create GitHub repo
        updateStepStatus('step-github', 'active', 'Creating repository...');
        document.getElementById('current-status').textContent = 'Creating GitHub repository...';
        const repoName = enhancedIdea.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

        if (apiRunning && settings.githubToken) {
            try {
                const repoResult = await createGitHubRepo(
                    repoName,
                    (enhancedIdea.description || '').substring(0, 200),
                    settings.privateRepos !== false
                );
                currentRun.repoUrl = repoResult.url;
                currentRun.repoFullName = repoResult.full_name;
                currentRun.repoCreated = true;
                updateStepStatus('step-github', 'completed', `✓ Repository: ${repoResult.name}`);
            } catch (repoError) {
                console.error('GitHub API error:', repoError);
                currentRun.repoUrl = `https://github.com/${settings.githubUsername}/${repoName}`;
                currentRun.repoCreated = false;
                updateStepStatus('step-github', 'completed', '⚠ Repository simulated');
            }
        } else {
            await sleep(1200);
            currentRun.repoUrl = `https://github.com/${settings.githubUsername}/${repoName}`;
            currentRun.repoCreated = false;
            updateStepStatus('step-github', 'completed', '✓ Repository simulated');
        }
        updateProgress(50);

        // Step 4: Break down features
        updateStepStatus('step-features', 'active', 'Breaking down features...');
        document.getElementById('current-status').textContent = 'Extracting implementation features from PRD...';
        await sleep(800);
        updateStepStatus('step-features', 'completed', `✓ ${currentRun.featuresCount} features across ${currentRun.epicsCount} epics`);
        updateProgress(66);

        // Step 5: Implementation (simulated)
        updateStepStatus('step-implement', 'active', 'Implementing...');
        document.getElementById('current-status').textContent = 'Claude Code is implementing features from the PRD...';
        await sleep(3000);
        updateStepStatus('step-implement', 'completed', `✓ ${currentRun.featuresCount} features implemented`);
        updateProgress(83);

        // Step 6: Publish
        updateStepStatus('step-publish', 'active', 'Publishing...');
        document.getElementById('current-status').textContent = 'Publishing to GitHub...';

        // Push PRD and project files if repo was created
        if (currentRun.repoCreated && currentRun.repoFullName) {
            try {
                const files = {
                    'docs/PRD.md': currentRun.prdMarkdown || '# PRD\n\nGenerated PRD',
                    'project.json': JSON.stringify({
                        title: enhancedIdea.title,
                        description: enhancedIdea.description,
                        tech_stack: enhancedIdea.suggested_tech_stack,
                        epics_count: currentRun.epicsCount,
                        features_count: currentRun.featuresCount
                    }, null, 2)
                };
                await pushFilesToRepo(currentRun.repoFullName, files);
            } catch (pushErr) {
                console.error('Push files error:', pushErr);
            }
        } else {
            await sleep(1000);
        }

        updateStepStatus('step-publish', 'completed', '✓ Published');
        updateProgress(100);

        // Complete
        currentRun.status = 'success';
        currentRun.elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);

        showToast('success', 'Build Complete!', `${currentRun.projectTitle} created in ${currentRun.elapsedTime}s`);
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

// ============ UI Helpers ============
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
    document.getElementById('current-status').innerHTML = `<span style="color: var(--success)">✅ Build completed in ${run.elapsedTime}s!</span>`;

    document.getElementById('results-content').innerHTML = `
        <div class="result-item">
            <span class="result-icon">📁</span>
            <span class="result-label">Project:</span>
            <span class="result-value">${run.projectTitle}</span>
        </div>
        <div class="result-item">
            <span class="result-icon">📝</span>
            <span class="result-label">Description:</span>
            <span class="result-value">${(run.description || '').substring(0, 200)}</span>
        </div>
        <div class="result-item">
            <span class="result-icon">📋</span>
            <span class="result-label">PRD:</span>
            <span class="result-value">${run.epicsCount} epics, ${run.featuresCount} features</span>
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
            <button class="btn btn-primary" onclick="resetRun()">Build Another App</button>
        </div>
    `;
}

function resetRun() {
    document.getElementById('idea-input').value = '';
    document.getElementById('tech-preferences').value = '';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('prd-preview-section').style.display = 'none';

    document.querySelectorAll('.progress-step').forEach(step => {
        step.classList.remove('active', 'completed', 'error');
        step.querySelector('.step-status').className = 'step-status pending';
        step.querySelector('.step-status').textContent = 'Pending';
    });

    updateProgress(0);
    document.getElementById('current-status').textContent = 'Ready to start...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ History ============
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
                <div class="run-title">${run.projectTitle || run.project || 'Unknown Project'}</div>
                <div class="run-meta">
                    ${run.timestamp} • ${run.elapsedTime || 0}s •
                    ${run.epicsCount || 0} epics • ${run.featuresCount || 0} features
                </div>
            </div>
            ${run.repoUrl ? `<div class="run-actions"><a href="${run.repoUrl}" target="_blank">View Repo →</a></div>` : ''}
        </div>
    `).join('');
}

// ============ Settings ============
function loadSettings() {
    settings = JSON.parse(localStorage.getItem('settings') || '{}');
}

function loadSettingsForm() {
    document.getElementById('gemini-key').value = settings.geminiKey || '';
    document.getElementById('github-token').value = settings.githubToken || '';
    document.getElementById('github-username').value = settings.githubUsername || '';
    document.getElementById('anthropic-key').value = settings.anthropicKey || '';
    document.getElementById('private-repos').checked = settings.privateRepos !== false;
}

function saveSettings() {
    settings = {
        geminiKey: document.getElementById('gemini-key').value,
        githubToken: document.getElementById('github-token').value,
        githubUsername: document.getElementById('github-username').value,
        anthropicKey: document.getElementById('anthropic-key').value,
        privateRepos: document.getElementById('private-repos').checked
    };

    localStorage.setItem('settings', JSON.stringify(settings));
    showToast('success', 'Settings Saved', 'Your configuration has been saved successfully.');
}

async function testConnection() {
    let results = [];

    const apiRunning = await checkApiServer();
    results.push(`API Server: ${apiRunning.running ? '✓ Running' : '✗ Not running'}`);

    const token = document.getElementById('github-token').value;
    if (token) {
        if (apiRunning.running) {
            const tokenResult = await validateGitHubToken(token);
            if (tokenResult.valid) {
                results.push(`GitHub Token: ✓ Valid (${tokenResult.username})`);
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
        if (document.getElementById('history-view').classList.contains('active')) {
            loadHistory();
        }
    } else {
        alert('No history entries needed migration.');
    }
}

// ============ Utility ============
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
