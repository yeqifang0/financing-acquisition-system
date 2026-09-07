FROM node:24-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --silent
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start", "--", "-p", "3000"]
