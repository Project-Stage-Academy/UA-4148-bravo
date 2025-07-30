# Code Quality and Linting with Pylint
This project uses **Pylint** and the **pylint-django** plugin to ensure code quality, consistency, and adherence to best practices in a Django environment.

**Installation**

Install the linting tools into your Python environment:

    pip install pylint pylint-django

**Usage**

To run Pylint on a specific Django app (e.g., users), use:

    pylint --load-plugins pylint_django users/

You can also run it on the entire project folder once all apps are available.

**Interpreting the Results**

Pylint outputs a list of messages and a final score from -10.00 to 10.00.
Each message includes:
- the file and line number,
- a message ID (e.g., C0114, E1101),
- and a short description.

Example:

    users/models.py:1:0: C0114: Missing module docstring (missing-module-docstring)

Messages are categorized by type:
    C – convention (style issues)
    R – refactor (design recommendations)
    W – warning (potential issues)
    E – error (likely bugs)
    F – fatal (breaks analysis)

Aim for a score as close to 10.00/10.00 as possible.

**Notes**

- Please run Pylint before submitting code for review.
- Fix as many warnings as possible, or leave comments if a warning is known and safe to ignore.
- You may customize .pylintrc further if needed — discuss changes with the team.