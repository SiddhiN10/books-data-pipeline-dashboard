FROM apache/airflow:2.9.1

USER root

# Install dependencies for Microsoft ODBC
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https ca-certificates && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev gcc g++ && \
    apt-get clean

# Switch back to airflow user before installing Python packages
USER airflow

# Install Python ODBC packages (as airflow user)
RUN pip install --no-cache-dir pyodbc pymssql
