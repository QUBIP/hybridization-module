# Dockerfile
FROM kdfix-docker-base

WORKDIR /app

# Copy application files
COPY ../src /app/
COPY ../hybridization_module.py /app/
COPY ../driver.py /app/
COPY ../requests/open_connect_request.json /app/
COPY ca /app/ca
COPY ../certificates/generate_cert.sh /app/
RUN chmod +x /app/certificates/generate_cert.sh
COPY ../nodes /app/nodes

# Pass configuration file argument
ARG CFGFILE
ENV CFGFILE=/app/${CFGFILE}

# Run the application
ENTRYPOINT ["python3", "-u", "hybridization_module.py"]
