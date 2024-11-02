# Python image ব্যবহার করা হচ্ছে
FROM python:3.10-slim

# কাজের ডিরেক্টরি সেট করা হচ্ছে
WORKDIR /app

# প্রয়োজনীয় ফাইল কপি করা হচ্ছে
COPY . .

# প্যাকেজ ইনস্টল করা হচ্ছে
RUN pip install -r requirements.txt

# পরিবেশ ভেরিয়েবল সেট করা হচ্ছে
ENV PORT=5000

# কন্টেইনার রান করা হচ্ছে
CMD ["python", "bot.py"]
