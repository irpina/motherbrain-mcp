FROM node:22-slim

RUN apt-get update && apt-get install -y \
    ca-certificates wget gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install @playwright/mcp (brings its own playwright version)
RUN npm install @playwright/mcp@latest

# Install chromium for the exact playwright version that was installed
RUN node_modules/.bin/playwright install chromium --with-deps

EXPOSE 8931

CMD ["node_modules/.bin/playwright-mcp", "--port", "8931", "--host", "0.0.0.0", "--headless", "--browser", "chromium"]
