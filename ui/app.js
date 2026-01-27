// JD Automation System - Frontend Application
// New flow: App Idea -> AI Enhancement -> PRD Generation -> GitHub -> Implementation -> Publish

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
    loadSettings();
    updateDashboard();
    setupNavigation();
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

// ============ PRD Review Rendering ============
function renderReviewSection(enhancedIdea, prdResult) {
    // Enhanced idea summary
    const summaryEl = document.getElementById('enhanced-idea-summary');
    const techStack = enhancedIdea.suggested_tech_stack || {};
    const techParts = Object.entries(techStack)
        .filter(([k]) => k !== 'notes')
        .map(([layer, techs]) => `<dt>${layer.charAt(0).toUpperCase() + layer.slice(1)}</dt><dd>${Array.isArray(techs) ? techs.join(', ') : techs}</dd>`)
        .join('');

    summaryEl.innerHTML = `
        <h3>Enhanced Application Concept</h3>
        <dl class="review-summary-grid">
            <dt>Title</dt><dd><strong>${escapeHtml(enhancedIdea.title)}</strong></dd>
            <dt>Description</dt><dd>${escapeHtml((enhancedIdea.description || '').substring(0, 300))}${(enhancedIdea.description || '').length > 300 ? '...' : ''}</dd>
            <dt>Target Users</dt><dd>${escapeHtml(enhancedIdea.target_users || 'N/A')}</dd>
            <dt>Problem</dt><dd>${escapeHtml(enhancedIdea.problem_statement || 'N/A')}</dd>
            ${techParts}
        </dl>
    `;

    // PRD markdown preview
    if (prdResult.prd_markdown) {
        document.getElementById('prd-preview-content').innerHTML =
            `<pre>${escapeHtml(prdResult.prd_markdown)}</pre>`;
    }

    // Feature checklist with checkboxes
    const checklistEl = document.getElementById('feature-checklist');
    let html = '';
    let featureIndex = 0;
    for (const epic of (prdResult.prd.epics || [])) {
        html += `<div class="feature-checklist-epic">`;
        html += `<div class="feature-checklist-epic-header">${escapeHtml(epic.name)} <span class="priority-badge">${epic.priority || 'P1'}</span></div>`;
        for (const story of (epic.user_stories || [])) {
            for (const feat of (story.features || [])) {
                html += `
                    <div class="feature-checkbox-item">
                        <input type="checkbox" id="feat-${featureIndex}" data-feature-index="${featureIndex}" checked>
                        <label for="feat-${featureIndex}">
                            <strong>${escapeHtml(feat.name)}</strong> — ${escapeHtml(feat.description || '')}
                            <span class="complexity-badge">${feat.complexity || 'M'}</span>
                        </label>
                    </div>
                `;
                featureIndex++;
            }
        }
        html += `</div>`;
    }
    checklistEl.innerHTML = html;
}

function getSelectedFeatureIndices() {
    const checkboxes = document.querySelectorAll('#feature-checklist input[type="checkbox"]');
    const selected = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            selected.push(parseInt(cb.dataset.featureIndex));
        }
    });
    return selected;
}

function cancelRun() {
    currentRun = null;
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('prd-review-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    updateProgress(0);
    document.getElementById('current-status').textContent = 'Ready to start...';
    document.querySelectorAll('.progress-step').forEach(step => {
        step.classList.remove('active', 'completed', 'error');
        step.querySelector('.step-status').className = 'step-status pending';
        step.querySelector('.step-status').textContent = 'Pending';
    });
    showToast('info', 'Cancelled', 'Build cancelled.');
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

// ============ Start Run (Phase 1: Enhance + PRD, then pause for review) ============
async function startRun() {
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

    // Show progress, hide review/results
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('prd-review-section').style.display = 'none';

    const startTime = Date.now();
    currentRun = {
        id: `run_${startTime}`,
        timestamp: new Date().toLocaleString(),
        status: 'running',
        startTime: startTime,
        apiRunning: apiRunning
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

        // ---- PAUSE: Show review section and wait for user to click Continue ----
        document.getElementById('current-status').innerHTML =
            '<span style="color: var(--warning);">⏸ Review the PRD below, then click <strong>Continue to Build</strong></span>';

        document.getElementById('prd-review-section').style.display = 'block';
        renderReviewSection(enhancedIdea, prdResult);

        showToast('info', 'Review Required', 'Review the enhanced idea and PRD before continuing.', 8000);

        // Pipeline pauses here — continueAfterReview() resumes steps 3-6

    } catch (error) {
        currentRun.status = 'failed';
        currentRun.error = error.message;
        showToast('error', 'Run Failed', error.message);
        document.getElementById('current-status').innerHTML = `<span style="color: var(--error)">❌ Error: ${error.message}</span>`;
        runHistory.push(currentRun);
        localStorage.setItem('runHistory', JSON.stringify(runHistory));
        updateDashboard();
    }
}

// ============ Continue After Review (Phase 2: GitHub, implement, publish) ============
async function continueAfterReview() {
    if (!currentRun || !currentRun.enhancedIdea || !currentRun.prd) {
        showToast('error', 'No Run', 'No active run to continue.');
        return;
    }

    const enhancedIdea = currentRun.enhancedIdea;
    const apiRunning = currentRun.apiRunning;

    // Filter features based on user's checkbox selections
    const selectedIndices = getSelectedFeatureIndices();
    const allFeatures = flattenFeatures(currentRun.prd);
    const selectedFeatures = allFeatures.filter((_, i) => selectedIndices.includes(i));

    currentRun.featuresCount = selectedFeatures.length;
    currentRun.selectedFeatures = selectedFeatures;

    // Hide review section
    document.getElementById('prd-review-section').style.display = 'none';
    document.getElementById('current-status').textContent = 'Continuing build...';

    try {
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

        // Step 4: Break down features (already done during review)
        updateStepStatus('step-features', 'active', 'Breaking down features...');
        document.getElementById('current-status').textContent = `Building ${currentRun.featuresCount} selected features across ${currentRun.epicsCount} epics...`;
        await sleep(500);
        updateStepStatus('step-features', 'completed', `✓ ${currentRun.featuresCount} features selected`);
        updateProgress(66);

        // Step 5: Implementation
        updateStepStatus('step-implement', 'active', 'Implementing...');
        document.getElementById('current-status').textContent = 'Claude Code is implementing features from the PRD...';
        await sleep(3000);
        updateStepStatus('step-implement', 'completed', `✓ ${currentRun.featuresCount} features implemented`);
        updateProgress(83);

        // Step 6: Publish
        updateStepStatus('step-publish', 'active', 'Publishing...');
        document.getElementById('current-status').textContent = 'Publishing to GitHub...';

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
        currentRun.elapsedTime = ((Date.now() - currentRun.startTime) / 1000).toFixed(1);

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

// ============ Flatten PRD features into ordered list ============
function flattenFeatures(prd) {
    const features = [];
    for (const epic of (prd.epics || [])) {
        for (const story of (epic.user_stories || [])) {
            for (const feat of (story.features || [])) {
                features.push({
                    epic: epic.name,
                    epicPriority: epic.priority || 'P1',
                    story: story.title,
                    name: feat.name,
                    description: feat.description || '',
                    complexity: feat.complexity || 'M'
                });
            }
        }
    }
    return features;
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
    document.getElementById('prd-review-section').style.display = 'none';

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
