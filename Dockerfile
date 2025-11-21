FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir python-dotenv

# Download Portuguese fastText vectors during image build instead of copying them
# Using curl and ca-certificates; keep image small by cleaning apt lists and removing curl afterwards
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl ca-certificates \
	&& curl -fSL https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.pt.300.vec.gz -o /app/cc.pt.300.vec.gz \
	&& rm -rf /var/lib/apt/lists/* \
	&& apt-get remove -y curl \
	&& apt-get autoremove -y

# Copy the rest of the application code
COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]