FROM node:20-alpine
WORKDIR /

COPY . ./

RUN npm i
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
