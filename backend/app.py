import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs


load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to extract text
def extract_text(video_id):
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_id)
        all_text = ""
        for dic in srt:
            all_text += dic['text'] + ' '
        return all_text
    except Exception as e:
        return str(e)

def extract_video_id(url):
    # Extract video ID from YouTube URL
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]  # Remove the leading '/'
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    return None

# Function to split text into chunks
def split_text_into_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=12000, chunk_overlap=1200)
    text_chunks = splitter.split_text(text)
    return text_chunks

# Function to create vector store
def create_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

# Function to setup conversation chain for QA
def setup_conversation_chain(template):
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# Function to handle user input based on selected mode
def handle_user_input(user_question=None):
    if user_question and (user_question.startswith('https://youtu.be/') or 'youtube.com/watch' in user_question):
        video_id = extract_video_id(user_question)
        if video_id:
            raw_text = extract_text(video_id)
            text_chunks = split_text_into_chunks(raw_text)
            create_vector_store(text_chunks)
            print('Video processed and vector store created.')
            return 'Processing video...'
        else:
            print('Invalid URL format')
            return 'Invalid URL format'
    else:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        indexed_data = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = indexed_data.similarity_search(user_question)

        chain = setup_conversation_chain(prompt_template)
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        print('Response generated from vector store.')
        return response["output_text"]
 

# Prompt templates for each mode
prompt_template = """
Your task is to provide a thorough response based on the given context, ensuring all relevant details are included. 
If the requested information isn't available, simply state, "answer not available in context," then answer based on your understanding, connecting with the context. 
Don't provide incorrect information.\n\n
Context: \n {context}?\n
Question: \n {question}\n
Answer:
"""


from flask import Flask, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
@cross_origin()
def home():
    return "Hello!!!!"

@app.route("/getReply", methods = ['POST'])
@cross_origin()
def get_response():
    req_data = request.get_json()
    print(req_data)
    temp = req_data['temp']
    print(temp)
    message = temp['msg']
    print(message)
    botResponse = handle_user_input(message)
    return str(botResponse)

if __name__ == "__main__":
    app.run()