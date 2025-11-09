🧠 SkillSense AI – Unlock Your Hidden Potential

An AI-powered skill analysis platform that identifies, compares, and visualizes skills from resumes, LinkedIn, and GitHub profiles to help users understand their strengths and bridge their skill gaps.

🌟 Overview:

SkillSense AI is an intelligent web application that automatically detects a person’s skills from their digital profiles using Machine Learning and Natural Language Processing (NLP).

It analyzes resumes, LinkedIn pages, or GitHub accounts to identify key skills, compares them with 40+ predefined job roles (Tech, Finance, HR, Design), and highlights the missing skills.

The app provides personalized recommendations, learning resources, and visual dashboards — all in real time.

🎯 Key Features:

✅ Upload resumes in PDF, DOCX, or TXT format
✅ Analyze LinkedIn or GitHub profiles directly
✅ Detects and compares skills using semantic AI embeddings
✅ Highlights missing & extra skills
✅ Visualizes skill coverage with charts & metrics
✅ Generates personalized learning suggestions
✅ Includes Fast Mode (keyword-based) and AI Mode (semantic)
✅ Built completely within 24 hours for a hackathon 🚀

⚙️ Tech Stack:
Layer	Tools / Libraries
Frontend:	Streamlit

Backend:	Python
Machine Learning:	Sentence Transformers
 (all-MiniLM-L6-v2), spaCy

Data Extraction	: pdfplumber, python-docx
Visualization:	Matplotlib, Streamlit components
Integrations:	GitHub REST API, LinkedIn public parsing
Data Storage:	JSON ontology for roles & skills
Environment:	Virtualenv + Requirements.txt

🧠 ML Model Details:

Model: all-MiniLM-L6-v2 from Sentence Transformers

Purpose: Convert both text and skill names into vector embeddings

Logic:

Clean and preprocess resume text

Split text into short lines/sentences

Encode using SentenceTransformer

Compare cosine similarity with canonical skill embeddings

Return top matches above threshold

Optimization:

Precomputed embeddings for speed

Cached model loading with Streamlit’s resource cache

🧰 Setup Instructions
1️⃣ Clone the repository
git clone https://github.com/<your-username>/SkillSense_AI.git
cd SkillSense_AI

2️⃣ Create a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
# or
source venv/bin/activate       # macOS / Linux

3️⃣ Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

4️⃣ (Optional) Precompute skill embeddings
python precompute_embeddings.py

5️⃣ Run the app
streamlit run app.py


App will launch at 👉 http://localhost:8501

📊 Sample Output:

Input: Resume or LinkedIn profile
Output:

Extracted skills list

Skills you already have

Missing skills for chosen role

Recommended learning resources

Visual radar chart for skill coverage

🧠 Example Use Case:

A student uploads their resume and selects Data Scientist role.

SkillSense AI detects skills like Python, Pandas, and SQL.

It shows missing ones like TensorFlow, NLP, and Cloud.

It suggests learning links to Coursera or YouTube for those topics.

🚀 What Makes It Special:

Built end-to-end in 24 hours for a hackathon

Uses semantic AI, not just keyword matching

Integrates real profiles from GitHub and LinkedIn

Fast, modular, and extensible design

No external database needed — simple JSON setup

🧩 Challenges Faced:

Model loading & performance tuning

Extracting clean text from PDFs and LinkedIn HTML

Designing a fast, judge-friendly UI

Balancing accuracy with real-time response speed

🧭 Future Enhancements:

Add team matching and job recommendation features

Integrate with OpenAI API for smarter resume rewriting

Multi-language support for global users

Export analysis as a detailed PDF report

🏆 Built For:

Hackathon 2025 – SAP Challenge: Unlock Your Hidden Potential
Developed by Tejas

🤝 Contribution:

Pull requests and suggestions are welcome!
If you’d like to improve the model, add new roles, or enhance the UI:

Fork the repo

Create a feature branch

Submit a pull request

📄 License:

This project is released under the MIT License.
Feel free to use and modify it for learning or personal development purposes.

💬 Contact
👨‍💻 Developer: Tejas
📧 Email: tejasdixit53@gmail.com
🐙 GitHub: github.com/tejasd5
