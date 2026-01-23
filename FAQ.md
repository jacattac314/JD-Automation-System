# FAQ - Frequently Asked Questions

## General Questions

### What is this project?

The JD Automation System is a local-first automation pipeline that transforms job descriptions into fully implemented GitHub projects. It uses AI (Gemini for specs, Claude Code for implementation) to generate relevant portfolio projects based on job requirements.

### Who is this for?

- **Job seekers** building portfolio projects
- **Students** learning from real-world project requirements
- **Developers** quickly prototyping ideas
- **Recruiters** generating sample projects for assessment

### Is it free to use?

The software itself is free (MIT license), but you'll need:

- API access to Google Gemini (free tier available)
- API access to Anthropic Claude (paid)
- GitHub account (free)
- LinkedIn API access (optional, requires approval)

### Does it actually work?

Yes! The pipeline is functional. However, the Claude Code integration is currently simulated (creates placeholder structure). Everything else works: JD analysis, project ideation, GitHub integration, Gemini spec generation, etc.

## Technical Questions

### What programming languages does it support?

The system itself is written in Python. The projects it generates can be in any language/framework based on the templates and AI specifications (Python, JavaScript, Java, etc.).

### Can I add my own project templates?

Yes! Edit `modules/ideation.py` and add templates to the `PROJECT_TEMPLATES` dictionary. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How long does a run take?

Typical run time: 3-5 minutes

- JD Analysis: ~1 second
- Project Ideation: ~1 second  
- GitHub Repo Creation: ~2-3 seconds
- Gemini Spec Generation: 30-60 seconds
- Claude Code Implementation: 2-4 minutes (varies)
- Publishing: ~5-10 seconds

### Can I run it without API keys?

For testing: Run `python demo.py` to see the analysis and ideation steps without any API keys.

For production: You need at least Gemini and GitHub API keys.

### Is my data secure?

Yes:

- All processing is local
- API keys stored in OS keyring
- GitHub repos are private by default
- No data sent to cloud except AI API calls
- Full audit logs of all operations

### Can I customize the generated projects?

Absolutely! After generation:

1. Clone the GitHub repo locally
2. Modify code as needed
3. The generated spec and plan provide a solid foundation
4. All artifacts are yours to edit

## Configuration Questions

### Where do I get API keys?

**Gemini:** [Google AI Studio](https://makersuite.google.com/app/apikey)
**GitHub:** [Settings > Developer > Tokens](https://github.com/settings/tokens)
**Anthropic:** [Anthropic Console](https://console.anthropic.com/)
**LinkedIn:** [LinkedIn Developers](https://www.linkedin.com/developers/) (requires app approval)

### Do I need all API keys?

Required:

- ✓ Gemini API key
- ✓ GitHub token
- ✓ Anthropic API key

Optional:

- LinkedIn (can skip with `--no-linkedin` flag)

### How do I configure the system?

Two ways:

1. Run setup wizard: `python -m cli.main setup`
2. Edit `.env` file manually

### Can I use a different AI model?

Currently hardcoded to Gemini Pro and Claude Code. You could modify:

- `modules/gemini_client.py` for different Google models
- `modules/antigravity_runner.py` for different coding agents

## Usage Questions

### Can I process multiple job descriptions?

Currently one at a time. For batch processing:

```bash
for jd in jd_files/*.txt; do
  python -m cli.main run --jd-file "$jd"
done
```

### What if I don't like the generated project idea?

In interactive mode (without `--auto` flag), you can reject and regenerate ideas. Or edit `modules/ideation.py` to adjust templates.

### Where are the generated projects stored?

- Locally: `projects/<project-name>/`
- Remotely: GitHub repository (URL in run output)

### Can I delete a generated project?

Yes:

- Delete local directory: `rm -rf projects/<project-name>`
- Delete GitHub repo: Via GitHub web UI or API
- Remove from LinkedIn: Via LinkedIn profile editing

### How do I view past runs?

```bash
python -m cli.main history
```

Or check `data/runs.json` directly.

## Troubleshooting

### "Configuration errors" message

- Ensure all required API keys are in `.env`
- Run `python -m cli.main setup` to reconfigure
- Check `.env.example` for required fields

### "Module not found" error

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### GitHub authentication fails

- Verify token has `repo` scope
- Check token hasn't expired
- Ensure GitHub username is correct in config

### Gemini API errors

- Check API key is valid
- Verify you have API access enabled
- Check for rate limits or quota

### LinkedIn integration fails

- LinkedIn API requires developer app
- App must be approved for profile editing
- OAuth token must be valid and not expired

### "Permission denied" on file operations

- Check file permissions
- Ensure you have write access to project directory
- Run without `sudo` (should work as regular user)

## Advanced Questions

### Can I run this in Docker?

Yes! See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker instructions.

### Can I deploy to the cloud?

Yes, it can run on any VM (AWS EC2, GCP Compute, etc.). See [DEPLOYMENT.md](DEPLOYMENT.md).

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:

- Bug fixes
- New project templates
- Documentation improvements
- Feature enhancements

### What's the real Antigravity integration?

Antigravity is Google's experimental AI-first IDE. The current implementation simulates it. When the official API is available, we'll integrate directly.

### Can I use this commercially?

Yes! MIT license allows commercial use. However:

- Respect API terms of service (Gemini, Claude, etc.)
- Don't abuse rate limits
- Follow GitHub's acceptable use policy

### How can I speed up runs?

- Use faster AI models (when available)
- Cache specifications for similar JDs
- Run on more powerful hardware
- Use local Claude models (when available)

### Can I modify the generated code before publishing?

Yes! The workflow is:

1. Generate project locally
2. Review/modify in `projects/<name>/`
3. System publishes to GitHub
4. You can continue editing after publish

Or skip auto-publish and do it manually.

## Project-Specific Questions

### What types of projects can it generate?

Current categories:

- Full-stack web applications
- Machine learning / Data science projects
- Cloud / DevOps infrastructure
- Mobile applications
- API services

Depends on templates in `modules/ideation.py`.

### Can it generate enterprise-scale applications?

The specs can be comprehensive, but implementation complexity depends on:

- AI coding agent capabilities
- Template sophistication
- Time allocated

Best for: MVPs, proof-of-concepts, portfolio projects
Not ideal for: Large enterprise systems (yet)

### Will the generated code actually run?

With real Claude Code integration: Should produce working code.
Currently (simulated): Creates structure but needs manual implementation.

### Can I use generated projects in interviews?

Absolutely! That's a primary use case. Just:

- Review and understand the code
- Be honest about AI assistance
- Customize to show your skills
- Use as conversation starters

---

**Still have questions?**

- Check our [documentation](README.md)
- Open an [issue](https://github.com/your-repo/issues)
- Start a [discussion](https://github.com/your-repo/discussions)
