# GitaAI – AI Powered Bhagavad Gita Guidance System

GitaAI is an AI-driven system that provides **life guidance inspired by the teachings of the Bhagavad Gita**.
It analyzes a user's emotional state or question and returns relevant **Gita verses, reflections, and wisdom** to help users gain clarity and peace.

The goal of this project is to combine **ancient spiritual knowledge with modern AI technology** to support people facing stress, confusion, or emotional challenges.

---

##  Features

*  Emotion detection from user input
*  Bhagavad Gita verse recommendation
*  AI generated spiritual reflection
*  Memory engine for emotional context
*  FastAPI backend for API communication
*  Frontend interface for user interaction

---

##  Project Architecture

```
gita-ai/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   │
│   ├── routers/
│   │   └── chat.py
│   │
│   ├── ai/
│   │   ├── chat_engine.py
│   │   ├── pipeline.py
│   │   ├── response_builder.py
│   │   ├── memory_engine.py
│   │   └── emotion_memory.py
│
├── frontend/
│
├── requirements.txt
└── README.md
```

---

##  Installation

Clone the repository:

```
git clone https://github.com/YOUR_USERNAME/gita-ai.git
cd gita-ai
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the backend server:

```
uvicorn main:app --reload
```

The API will start at:

```
http://127.0.0.1:8000
```

---

##  How It Works

1. User sends a message describing their problem or emotion
2. The system analyzes emotional context
3. Relevant Bhagavad Gita verses are retrieved from the database
4. AI generates a meaningful reflection
5. The user receives spiritual guidance

---

##  Technologies Used

* Python
* FastAPI
* SQLite
* AI / NLP pipelines
* HTML / CSS / JavaScript

---

## Future Improvements

* AI emotion classifier
* Vector search for verse retrieval
* Voice interaction system
* Mobile application version

---

##  Inspiration

The Bhagavad Gita teaches timeless wisdom about **duty, balance, and inner peace**.
This project aims to make those teachings accessible using modern technology.

---

##  Author

**Ashutosh Satapathy**

BTech Student | AI/ML Enthusiast
Interested in building AI systems that combine **technology with meaningful impact**.
