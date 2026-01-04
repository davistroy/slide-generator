# Security Policy

## Reporting Security Issues

If you discover a security vulnerability in this project, please report it responsibly:

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please contact the project maintainers directly. We will work with you to understand and address the issue promptly.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | ✅ Yes             |
| 1.1.x   | ✅ Yes             |
| < 1.1   | ❌ No              |

## Security Best Practices

### API Key Management

**Critical:** This project uses Google Gemini API keys that must be protected.

#### ✅ DO:
- Store API keys in `.env` files (never committed to git)
- Use environment variables for all secrets
- Rotate API keys regularly (every 90 days recommended)
- Monitor API usage for anomalies at https://console.cloud.google.com/
- Use separate API keys for development, staging, and production
- Revoke keys immediately if compromised

#### ❌ DON'T:
- Commit `.env` files to version control
- Hardcode API keys in source code
- Share API keys via email, chat, or screenshots
- Include API keys in documentation or comments
- Reuse API keys across multiple projects
- Share your `.env` file even with team members

### Environment File Security

**The `.env` file contains sensitive credentials and must be protected:**

1. **Always in .gitignore:** Verify `.env` is listed in `.gitignore`
2. **Never committed:** Check git history doesn't contain old `.env` commits
3. **Proper permissions:** On Unix systems, set `chmod 600 .env`
4. **Not in distributions:** Ensure `.env` is excluded from ZIP/TAR distributions
5. **Team sharing:** Use `.env.example` as a template, each developer creates their own `.env`

### Distribution Safety

When creating distribution packages:

1. **Verify exclusions:** Always check package contents before sharing
2. **Use .gitignore:** Leverage git's exclusion patterns
3. **Check ZIP contents:** Inspect `dist/*.zip` files for accidental `.env` inclusion
4. **Document properly:** Ensure `.env.example` has clear instructions
5. **Test fresh install:** Verify distribution works without your local `.env`

### Dependency Security

#### Regular Updates

Keep dependencies updated to patch security vulnerabilities:

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Check for known vulnerabilities (recommended)
pip install pip-audit
pip-audit
```

#### Dependency Pinning

The project uses `requirements.txt` with version specifications:

```txt
python-pptx>=1.0.2
google-genai>=1.55.0
```

#### Security Scanning

Periodically scan for vulnerabilities:

```bash
# Install security scanner
pip install safety pip-audit

# Scan dependencies
safety check
pip-audit
```

### Code Security

#### Input Validation

- **File paths:** Validate all file paths to prevent directory traversal
- **User input:** Sanitize user-provided content in presentations
- **API responses:** Validate all data from Gemini API before use

#### Error Handling

- **No sensitive data in errors:** Ensure error messages don't leak API keys
- **Log sanitization:** Remove secrets from logs before writing
- **Graceful failures:** Handle API errors without exposing internal state

### What To Do If You Accidentally Expose a Key

**If you commit an API key to git or share it publicly:**

1. **Revoke immediately:** Go to https://aistudio.google.com/app/apikey and delete the key
2. **Generate new key:** Create a replacement API key
3. **Update .env:** Replace the old key with the new one
4. **Review usage:** Check API logs for unauthorized activity
5. **Understand risk:** Even if you remove it from git history, consider it permanently compromised
6. **Git history note:** Rewriting git history doesn't remove keys from forks/clones

**Important:** Deleting a commit doesn't delete the secret! Anyone who pulled the repository before you removed it still has access to the key.

## Common Vulnerabilities to Avoid

### Path Traversal

```python
# ❌ DON'T: Accept arbitrary paths without validation
output_path = user_input  # Could be "../../etc/passwd"

# ✅ DO: Validate paths are within expected directory
from pathlib import Path
output_path = Path(user_input).resolve()
if not output_path.is_relative_to(expected_dir):
    raise ValueError("Invalid path")
```

### Command Injection

```python
# ❌ DON'T: Pass user input to shell commands
os.system(f"convert {user_filename}")  # Dangerous!

# ✅ DO: Use subprocess with argument lists
subprocess.run(["convert", user_filename])
```

### Unsafe Deserialization

```python
# ❌ DON'T: Load untrusted pickle files
import pickle
data = pickle.load(open(user_file, 'rb'))  # Dangerous!

# ✅ DO: Use JSON for untrusted data
import json
data = json.load(open(user_file, 'r'))
```

## Security Checklist for Contributors

Before submitting a pull request:

- [ ] No hardcoded API keys or secrets in code
- [ ] `.env` file not included in commits
- [ ] Sensitive data not logged or printed
- [ ] User input properly validated
- [ ] File paths validated against traversal attacks
- [ ] External commands use subprocess with argument lists
- [ ] Error messages don't leak sensitive information
- [ ] New dependencies reviewed for known vulnerabilities
- [ ] Documentation updated if security practices changed

## Security Update Process

When a security issue is identified:

1. **Private disclosure:** Reporter contacts maintainers privately
2. **Verification:** Maintainers confirm and assess severity
3. **Patch development:** Fix created and tested privately
4. **Coordinated release:** Update released with security advisory
5. **Public disclosure:** Details shared after patch is available

## Resources

- **Google API Security:** https://cloud.google.com/docs/security
- **API Key Best Practices:** https://cloud.google.com/docs/authentication/api-keys
- **Python Security Guide:** https://python.readthedocs.io/en/stable/library/security_warnings.html
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/

## License

This security policy is part of the slide-generator project and follows the same license.

---

**Last Updated:** January 3, 2026
**Version:** 1.0
