FROM python:3.11-slim

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user called "user" with user ID 1000 (Required by Hugging Face)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app
COPY --chown=user . $HOME/app

# Install Python requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port (HF Spaces defaults to 7860 for Docker)
EXPOSE 7860

# Run the Streamlit app on port 7860
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
