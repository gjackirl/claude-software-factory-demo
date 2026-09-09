# Claude Software Factory Demo

This repo demonstrates an external Claude agent that can receive a task, update repo content, and open a pull request.

## Local setup

Coming soon.

## FAQ

### How do I run the project locally?

1. Clone the repository:
   ```bash
   git clone https://github.com/gjackirl/claude-software-factory-demo.git
   cd claude-software-factory-demo
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```

### How do I configure environment variables?

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the required values. At a minimum you will need:
   - `NOTION_API_TOKEN` – your Notion integration token
   - `GITHUB_TOKEN` – a GitHub personal access token with repo permissions
3. Save the file. Environment variables are loaded automatically at startup.

### How do I run the tests?

Run the full test suite with:
```bash
npm test
```

To run tests in watch mode during development:
```bash
npm run test:watch
```

To generate a coverage report:
```bash
npm run test:coverage
```

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the full list of planned work. Highlights:

- **4K export support for Cam 2 and Cam 3** — resolving the current 1080p output cap for cameras with 4K sensors (621 votes on the ideas board)
