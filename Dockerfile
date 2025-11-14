# Dockerfile

## PART 1: Building liboqs, this image will only be used to build it, the real image is in PART 2
FROM python:3.11-trixie AS builder

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    automake \
    autoconf


WORKDIR /opt
# Clone repositories for liboqs and its Python bindings
RUN git clone --depth 1 --branch 0.12.0 https://github.com/open-quantum-safe/liboqs.git

# Build argument for liboqs configuration
ARG LIBOQS_BUILD_DEFINES="-DOQS_DIST_BUILD=ON -DBUILD_SHARED_LIBS=ON -DOQS_USE_OPENSSL=OFF"

# Build liboqs
WORKDIR /opt/liboqs
RUN mkdir build && cd build && \
    cmake -GNinja .. ${LIBOQS_BUILD_DEFINES} && \
    ninja install


# -------------------------------------
## PART 2: Final runtime image
FROM python:3.11-slim-trixie

# Copy liboqs shared libraries and headers from the builder stage
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/include /usr/local/include

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    openssl \
    ca-certificates \
    git && \
    rm -rf /var/lib/apt/lists/*


# Make sure the dynamic linker can find liboqs
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

## Now we start copying the hybridization module files to the container
WORKDIR /app

# Import python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: quick test to verify installation
RUN python -c "import oqs; print('oqs installed successfully')"

# Copy certificate and their scripts
COPY ca /app/ca
COPY scripts/certificates/sign_cert.sh /app/certificates/
RUN chmod +x /app/certificates/sign_cert.sh

# Copy application files
COPY src /app/src/
ENV SRC_PATH=/app/src/

# Run the application
ENTRYPOINT ["python3", "-u", "src/hybridization_module/main.py"]
