FROM python:3.11-slim

WORKDIR /app

# 更新・日本語化
RUN apt-get update && apt-get -y install locales && apt-get -y upgrade && \
	localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ポート開放 (uvicornで指定したポート)
EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
