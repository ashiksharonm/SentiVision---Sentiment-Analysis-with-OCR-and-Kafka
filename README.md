# 🤖 SentiVision – OCR & Sentiment Analysis with Kafka Integration  

SentiVision is an AI-powered tool that extracts text from images using OCR and performs sentiment analysis using a **Gemini AI model**. It integrates **Kafka** for real-time processing and **FAISS** for semantic search.

## 🚀 Features  
✅ **Multi-Image OCR** – Extracts text from multiple images  
✅ **AI-Based Sentiment Analysis** – Classifies sentiment as Positive, Negative, or Neutral  
✅ **Kafka Streaming** – Sends extracted data to Kafka for real-time processing  
✅ **Vector Search (FAISS)** – Retrieves similar past feedback for better analysis  
✅ **Secure Authentication** – Uses **Keycloak** for user login  

## 🔧 Installation  

### **1️⃣ Clone the Repository**
```bash
git clone <your-repo-url>
cd sentivision
```

### **2️⃣ Install Dependencies**  
```bash
pip install -r requirements.txt
```

### **3️⃣ Set Up Environment Variables**  
Create a `.env` file and add:  
```ini
API_KEY=your_gemini_api_key
KEYCLOAK_URL=http://localhost:8080
REALM_NAME=master
CLIENT_ID=client_0098
KAFKA_SERVER=localhost:9092
KAFKA_TOPIC=ocr-sentiment
```

### **4️⃣ Run the Application**  
```bash
streamlit run app.py
```

## 📜 Example Output  
🔹 **Extracted Text:** "Great service, but slow response!"  
🔹 **Sentiment:** "Negative" ❌  

## 🤝 Contributing  
Want to improve SentiVision? Feel free to fork this repo and submit a pull request!  

## 📌 Developed by  
👨‍💻 **Ashik Sharon M** – `24MAI0098`  

---  


