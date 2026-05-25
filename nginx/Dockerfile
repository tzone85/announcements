FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN rm /etc/nginx/conf.d/*.conf.default 2>/dev/null || true

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
