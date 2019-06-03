FROM r-base
COPY . /app
WORKDIR /app
RUN R -e "install.packages('plumber')"
RUN R -e "install.packages('uuid')"
RUN R -e "install.packages('lme4', version = '1.1-19')"
RUN R -e "install.packages('dplyr')"
RUN R -e "install.packages('devtools')"
RUN R -e "install.packages('scales')"
EXPOSE 5000
CMD sudo apt install libssl-dev libcurl4-gnutls-dev
