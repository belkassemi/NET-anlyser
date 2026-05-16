FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Vite dev server port
EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
