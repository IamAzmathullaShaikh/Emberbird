## Description
<!-- Provide a brief description of the problem solved or feature added. -->

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Documentation update
- [ ] CI/CD or workflow automation
- [ ] Refactoring / Dead code cleanup

## Differentiator Alignment
Does this change directly improve:
- [ ] Upstream synchronisation & compatibility
- [ ] User installation, update, or management experience
- [ ] Documentation accuracy and clarity
- [ ] Application compatibility reporting

## Quality Checklist
- [ ] Code compiles cleanly without errors
- [ ] Offline unit test suite passes: `python -m unittest discover -s tests -v`
- [ ] Local Markdown links verified: `python scripts/check_doc_links.py`
- [ ] Security and secret audit passes: `python scripts/security_scan.py`
- [ ] No personal tokens, secrets, or machine-specific paths committed
