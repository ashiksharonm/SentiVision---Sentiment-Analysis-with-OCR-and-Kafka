import streamlit as st
import requests
import json
from kafka import KafkaProducer, KafkaConsumer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
import findspark
from pyspark.sql import SparkSession
import pytesseract
from PIL import Image
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Keycloak Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM_NAME = os.getenv("REALM_NAME", "master")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"

def authenticate_user(username, password):
    payload = {'client_id': CLIENT_ID, 'grant_type': 'password', 'username': username, 'password': password}
    try:
        response = requests.post(TOKEN_URL, data=payload)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error during authentication: {e}")
        return None

# Initialize PySpark session
findspark.init()
spark = SparkSession.builder.appName("OCR Sentiment Analysis").master("local[*]").getOrCreate()

# Kafka Configuration
KAFKA_TOPIC = "ocr-sentiment"
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "localhost:9092")

# Initialize Kafka Producer
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def send_to_kafka(data):
    producer.send(KAFKA_TOPIC, data)
    producer.flush()

# Load data into PySpark DataFrame
file_path = "expanded_support_log.csv"
df = spark.read.csv(file_path, header=True, inferSchema=True)

documents = [row.asDict() for row in df.collect()]
text_documents = [" ".join([str(value) for value in doc.values()]) for doc in documents]

# Initialize embeddings and FAISS index
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(texts=text_documents, embedding=embeddings)
retriever = vector_store.as_retriever()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing! Set it in the environment variables or .env file.")

genai.configure(api_key=api_key)
llm = genai.GenerativeModel('gemini-1.5-flash-latest')

# Streamlit UI
st.title("🤖 SentiVision – OCR & Sentiment Analysis with Kafka Integration")

if "auth_token" not in st.session_state:
    st.sidebar.title("🔑 Login")
    username = st.sidebar.text_input("👤 Username")
    password = st.sidebar.text_input("🔒 Password", type="password")
    if st.sidebar.button("🔓 Login"):
        auth_response = authenticate_user(username, password)
        if auth_response:
            st.session_state.auth_token = auth_response['access_token']
            st.sidebar.success("✅ Login Successful!")
        else:
            st.sidebar.error("❌ Invalid username or password")
else:
    st.sidebar.success("✅ You are logged in.")
    option = st.sidebar.selectbox("📌 Choose an option:", ["Multi-Image OCR & Sentiment", "Kafka Consumer View"])

    if option == "Multi-Image OCR & Sentiment":
        uploaded_files = st.file_uploader("📂 Upload multiple images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

        if uploaded_files:
            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"📷 Uploaded: {uploaded_file.name}", use_container_width=True)

                extracted_text = pytesseract.image_to_string(image).strip()
                if extracted_text:
                    retrieved_docs = retriever.invoke(extracted_text)
                    combined_content = " ".join([doc.page_content for doc in retrieved_docs])

                    sentiment_prompt = f"""
                    You are a sentiment analysis expert. Given the following extracted feedback and similar past feedback,
                    classify the sentiment as: Positive, Negative, or Neutral.

                    Extracted Feedback: "{extracted_text}"
                    Similar Past Feedback: {combined_content}

                    Provide only the sentiment classification without explanation.
                    """
                    response = llm.generate_content(sentiment_prompt)
                    sentiment_result = response.text.strip()

                    # Kafka producer sends the extracted text and sentiment
                    kafka_data = {"image": uploaded_file.name, "text": extracted_text, "sentiment": sentiment_result}
                    send_to_kafka(kafka_data)

                    if "Positive" in sentiment_result:
                        st.success(f"✅ Sentiment: {sentiment_result}")
                    elif "Neutral" in sentiment_result:
                        st.info(f"ℹ️ Sentiment: {sentiment_result}")
                    elif "Negative" in sentiment_result:
                        st.error(f"❌ Sentiment: {sentiment_result}")
                    else:
                        st.warning("⚠️ Sentiment analysis could not determine the sentiment.")

    elif option == "Kafka Consumer View":
        st.header("📥 Kafka Consumer Data")

        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_SERVER,
            auto_offset_reset='earliest',
            group_id='ocr-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        st.write("⏳ Waiting for messages from Kafka...")  # Indicate waiting status
        time.sleep(2)  # Allow time for Kafka to process messages

        for message in consumer:
            data = message.value
            st.write(f"📷 **Image:** {data['image']}")
            st.write(f"📜 **Extracted Text:** {data['text']}")
            st.write(f"💬 **Sentiment:** {data['sentiment']}")
            st.write("---")

st.sidebar.markdown("👨‍💻 Developed by **Ashik Sharon M** - `24MAI0098`")
