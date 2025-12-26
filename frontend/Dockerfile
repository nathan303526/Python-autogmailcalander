# 使用 Node.js 18 輕量版
FROM node:18-alpine

# 設定工作目錄
WORKDIR /app

# 複製 package.json 並安裝套件
COPY package*.json ./
RUN npm install

# 複製程式碼
COPY . .

# 開放 Port
EXPOSE 5173

# 啟動指令 (加上 --host 讓外部可存取)
CMD ["npm", "run", "dev", "--", "--host"]
