FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This step is often done separately to leverage Docker's build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose the port your MCP server listens on (e.g., 8080)
EXPOSE 8080

# Define the command to run your MCP server
# Replace 'your_mcp_server.py' with the actual name of your server script
CMD ["python", "mcp_server.py"]
