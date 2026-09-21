# Run Python tests with coverage report
# Usage: .\scripts\run_coverage.ps1

Write-Host "[Emberbird] Running Python test suite with coverage..."
pip install coverage --quiet

coverage run -m unittest discover -s tests
coverage report --omit="tests/*,*/__pycache__/*"
coverage html --omit="tests/*,*/__pycache__/*" -d coverage_html

Write-Host "[Emberbird] Coverage HTML report written to coverage_html/"
