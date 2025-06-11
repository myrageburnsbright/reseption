FROM nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf
RUN usermod -aG 1001 nginx
COPY nginx.conf /etc/nginx/conf.d
