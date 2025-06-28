# Imagem base Node.js
FROM node:18

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto frontend
COPY ./frontend /app

# Instala dependências
RUN npm install

# Expõe a porta padrão do Vite
EXPOSE 5173

# Inicia o Vite dev server
CMD ["npm", "run", "dev"]
