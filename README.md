# Claude Software Factory Demo

This repo demonstrates an external Claude agent that can receive a task, update repo content, and open a pull request.

## Local setup

Coming soon.

## FAQ

### How do I run the project locally?

1. Clone the repository:
   ```
   git clone <repo-url>
   cd <repo-directory>
   ```
2. Install dependencies (adjust for your package manager):
   ```
   npm install
   ```
   or
   ```
   pip install -r requirements.txt
   ```
3. Start the project:
   ```
   npm start
   ```
   or
   ```
   python main.py
   ```

> Note: Exact commands depend on the language/framework used in this project. Update this section once the setup is finalized.

### How do I configure environment variables?

1. Create a `.env` file in the project root (you can copy from `.env.example` if one is provided):
   ```
   cp .env.example .env
   ```
2. Open `.env` and fill in the required values, for example:
   ```
   API_KEY=your_api_key_here
   BASE_URL=http://localhost:3000
   ```
3. Make sure your application loads environment variables at startup (e.g., using `dotenv` for Node.js or `python-dotenv` for Python).

> If no `.env.example` exists yet, check the codebase or ask a maintainer for the list of required variables.

### How do I run tests?

1. Ensure all dependencies are installed (see setup steps above).
2. Run the test suite using the appropriate command for the project's stack:
   ```
   npm test
   ```
   or
   ```
   pytest
   ```
3. Review test output for failures and fix any issues before opening a pull request.

> If a specific testing framework is configured (e.g., Jest, Mocha, PyTest), refer to its documentation for advanced options like watch mode or coverage reports.