# Notebook Coding Standards & Instructions

## General Principles

- **Clarity & Readability:** All code must be clear, concise, and easy to understand.
- **Documentation:** Every cell must include a docstring or markdown explaining its purpose, inputs, and outputs.
- **Consistency:** Use consistent naming conventions and code formatting (PEP8 for Python).
- **Error Handling:** Handle exceptions gracefully and provide informative error messages.

## Logging & Output

- **Rich/Pretty Logging:** Use the `rich` library for all logging and output in code cells to enhance readability and visual appeal.
    - Example:
      ```python
      from rich import print
      from rich.console import Console
      console = Console()
      console.log("[bold green]This is a pretty log message![/bold green]")
      ```
- **No Plain Prints:** Avoid using plain `print()` for output; always use `rich.print` or `console.log`.

## Cell Structure

- **Top Documentation:** Each code cell must start with a markdown or docstring describing:
    - What the cell does
    - Any important context or assumptions
    - Expected input/output
- **Imports:** Group all imports at the top of the notebook or cell, and only import what is necessary.
- **Reusable Code:** Encapsulate logic in functions where possible, with clear docstrings.



## Plotting Standards

- **Plotting Engine:** Use `plotly` for all visualizations unless otherwise specified.
- **Color Palette & Theme:** Use a bright color palette and set the plot background to black with all font/text in white for maximum contrast.
    - Example:
      ```python
      import plotly.express as px
      import plotly.io as pio
      # Set default template for dark background and bright colors
      pio.templates.default = "plotly_dark"
      # Example plot
      fig = px.scatter(data_frame, x="col1", y="col2", color_discrete_sequence=px.colors.qualitative.Bold)
      fig.update_layout(
          plot_bgcolor='black',
          paper_bgcolor='black',
          font_color='white',
          legend=dict(bgcolor='black', font_color='white')
      )
      fig.show()
      ```

- **Interactivity:** Add interactive Plotly features only when specifically requested.

---
## Example Cell

```python
# Purpose: Load and display the first 5 rows of the reservations dataset.
# Input: Path to Excel file
# Output: Pretty-printed DataFrame head

from rich import print
import pandas as pd

def load_and_preview(path: str):
    """Load an Excel file and pretty-print the first 5 rows."""
    df = pd.read_excel(path)
    print(df.head())
    return df

df = load_and_preview('path/to/file.xlsx')
```

## Markdown Cells

- Use markdown cells to explain the workflow, context, and results.
- Include section headers, bullet points, and links to documentation where helpful.

## File Scraping & Download Standards

- **Progress Tracking:**  
    For any file scraping or mass download operations, always implement a live progress bar using `rich.progress.Progress` with the following components:
        - Task description with colored text (e.g., `[cyan]Downloading PDFs...`)
        - Progress bar (`BarColumn()`)
        - Percentage completion
        - Current/total file counter (e.g., `Downloaded: {completed}/{total}`)
        - Elapsed time (`TimeElapsedColumn()`)

- **Summary Reporting:**  
    After completion, display a comprehensive summary table using `rich.table.Table` that includes:
        - File names with appropriate styling (**bold white**)
        - File sizes in human-readable format (**yellow** styling)
        - Additional metadata (page counts, file types, etc.) with distinct colors (**cyan**, **magenta**)
        - Status indicators (`[green]Downloaded`, `[blue]Already exists`, `[red]Failed`) with colored markup

- **Error Handling:**  
    Track and report statistics for downloaded, skipped, and failed files in the final console log with appropriate color coding.

> **Purpose:**  
> These standards ensure all file operations provide clear visual feedback and professional reporting, consistent with the `rich` library ecosystem.
---

**Follow these standards in every notebook and code cell for maintainable, professional, and visually appealing data science work.**
