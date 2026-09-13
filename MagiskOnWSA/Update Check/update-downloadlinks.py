import os
from bs4 import BeautifulSoup, Tag

# Load the README.md file
with open('README.md', 'r', encoding='utf-8', errors='replace') as file:
    readme_content = file.read()

# Parse the content with BeautifulSoup
soup = BeautifulSoup(readme_content, 'html.parser')

# Define the headers to locate the table (mirrors were removed, the table now has 2 columns)
headers = ['Operating System', 'Download Page']

# Initialize target_table
target_table = None

# Find the table with the specified headers
for table in soup.find_all('table'):
    ths = table.find_all('th')
    if len(ths) == len(headers):
        th_texts = [th.get_text(strip=True) if th.img is None else (th.img['alt'] if 'alt' in th.img.attrs else '') for th in ths]
        if all(header_text == header for header_text, header in zip(th_texts, headers)):
            target_table = table
            break

# Check if a matching table was found
if target_table is None:
    print("No table with the specified headers found in README.md")
    exit(1)

# Get the GitHub ENV variables
release_type = os.getenv('RELEASE_TYPE')

# Define the cell coordinates and corresponding ENV variables for each release type
release_types = {
    'WIF': [
        ((1, 1), 'LINK_FOR_W11X64'),
        ((2, 1), 'LINK_FOR_W11ARM64'),
        ((5, 1), 'LINK_FOR_W10X64')
    ],
    'retail': [
        ((3, 1), 'LINK_FOR_W11X64'),
        ((4, 1), 'LINK_FOR_W11ARM64'),
        ((6, 1), 'LINK_FOR_W10X64')
    ]
}

# Check if the release type is valid
if release_type not in release_types:
    print(f"Invalid RELEASE_TYPE: {release_type}")
    exit(1)

# Create a 2D list (matrix) to represent the table
table_matrix = []
for _ in range(100):  # Assuming the table will not have more than 100 rows
    table_matrix.append([None] * 100)  # Assuming the table will not have more than 100 columns

# Fill the table matrix with the cells from the table
for row_num, row in enumerate(target_table.find_all('tr')):
    col_num = 0
    for cell in row.find_all(['td', 'th']):
        while table_matrix[row_num][col_num] is not None:  # Skip columns that are already filled due to rowspan
            col_num += 1
        rowspan = int(cell.get('rowspan', 1))
        colspan = int(cell.get('colspan', 1))
        for i in range(row_num, row_num + rowspan):
            for j in range(col_num, col_num + colspan):
                table_matrix[i][j] = cell

# Replace the content of the specified cells
updated_count = 0
for (row_num, col_num), env_var in release_types[release_type]:
    # Check if the cell coordinates are within the range of the table matrix
    if row_num < len(table_matrix) and col_num < len(table_matrix[row_num]):
        github_env_var = os.getenv(env_var)
        if github_env_var is None:
            print(f"[*] Notice: {env_var} environment variable is not set; preserving existing table entry.")
            continue

        # Parse the GitHub ENV variable with BeautifulSoup
        github_env_var_soup = BeautifulSoup(github_env_var, 'html.parser')

        # Replace the cell content with the GitHub ENV variable
        target_cell = table_matrix[row_num][col_num]
        if target_cell is not None:
            target_cell.clear()
            target_cell.append(github_env_var_soup)
            updated_count += 1
            print(f"[+] Successfully updated {env_var} at table cell ({row_num}, {col_num})")
    else:
        print(f"[-] Warning: Cell coordinates ({row_num}, {col_num}) are out of range")

# Write the updated content back to the README.md file if updates occurred
if updated_count > 0:
    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(str(soup))
    print(f"[+] README.md successfully updated with {updated_count} download link(s).")
else:
    print("[*] No download links were modified in README.md.")