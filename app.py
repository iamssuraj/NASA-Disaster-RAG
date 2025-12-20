import streamlit as st
from streamlit_folium import st_folium
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
import json
import re

from services.vectorDBHandler import get_retriever, get_vector_store
from services.modelHandler import get_model
from services.fileHandler import getSystemPrompt, getSamplePrompts, getFooterHtml
from utils.logger import logger
from services.mapHandler import create_disaster_map
from services.vectorDBHandler import load_disaster_events
from utils.logger import logger
from services.vectorDBHandler import populate_vector_store

st.set_page_config(page_title="NASA Disaster RAG", page_icon="🌍", layout="wide", initial_sidebar_state='collapsed')

if "results" not in st.session_state:
    st.session_state.results = None

st.title("NASA Disaster RAG")

@st.cache_resource(show_spinner="Please wait while the application loads...")
def get_cached_vector_store():
    return get_vector_store()

vector_store = get_cached_vector_store()
current_count = vector_store._collection.count()

if current_count == 0:
    st.warning("⚠️ No events in database. Click 'Refresh Data' in the sidebar to load events.")


selected_option = st.sidebar.selectbox(
    label="Select an LLM",
    options=["Use Groq (llama-3.3-70b) faster", "Use Ollama (qwen2.5:0.5b) (must download)"]
)

use_api = (selected_option == "Use Groq (llama-3.3-70b) faster")

st.sidebar.divider()

st.sidebar.markdown("### Sample Prompts")
sample_prompts = getSamplePrompts()
for prompt in sample_prompts:
    st.sidebar.markdown(f"- {prompt}")

st.sidebar.divider()

try:
    all_events = vector_store.get()
    if all_events and all_events['metadatas']:
        all_dates = [m.get('date', '') for m in all_events['metadatas'] if m.get('date', '')]
        if all_dates:
            latest_date = datetime.fromisoformat(max(all_dates)).strftime('%b %d, %Y')
            oldest_date = datetime.fromisoformat(min(all_dates)).strftime('%b %d, %Y')
            st.sidebar.markdown(f"This LLM is trained on data from {oldest_date} to {latest_date}. For more recent data, please refresh the data. This operation may take a while.")
except Exception as e:
    logger.log("Error in app.py: ", e)

if st.sidebar.button("Click here to refresh data", key="refresh_btn", use_container_width=True):
    logger.log("User initiated data refresh")
    with st.spinner("Refreshing database. This may take a while.."):
        try:
            documents = load_disaster_events()
            if documents:
                existing = vector_store.get()
                if existing and existing['ids']:
                    vector_store.delete(ids=existing['ids'])
                    logger.log(f"Deleted {len(existing['ids'])} existing documents from vector store")
                
                populate_vector_store(vector_store, documents)
                logger.log(f"Data refresh completed successfully with {len(documents)} new documents")
                st.cache_resource.clear()
                st.success(f"✅ Refreshed! Now have {len(documents)} events.")
                st.rerun()
        except Exception as e:
            logger.log(f"Data refresh failed with error: {e}")
            st.error(f"❌ Refresh failed: {e}")


query = st.text_input("Ask about disaster events...", key="query_input")
generate = st.button("Generate Response")



if generate and query:
    st.session_state.results = None
    logger.log(f"User query: {query}")
    try:
        retriever = get_retriever()
        with st.spinner("Retrieving context..."):
            context_docs = retriever.invoke(query)
            logger.log(f"Retrieved {len(context_docs)} context documents for query: {query}")
            if not context_docs:
                logger.log("No documents retrieved from vector store")

        model = get_model(use_api=use_api)
        system_prompt = getSystemPrompt()
        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | model
        with st.spinner("Generating response..."):
            response = chain.invoke({
                "context": context_docs,
                "question": query
            })
        logger.log(f"Response generation completed for query: {query}")
        result = response.content if use_api else response
        # replaced with single query instead of 2 quey approach
        try:
            start = result.find('{')
            end = result.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = result[start:end+1]
                json_str = re.sub(r',([ \n\r\t]*[}\]])', r'\1', json_str)
                result_json = json.loads(json_str)
                report = result_json.get("report", "")
                map_points = result_json.get("map_data", [])
            else:
                raise ValueError("No JSON object found in LLM output.")
        except Exception as e:
            logger.log(f"Error parsing LLM JSON output: {e}")
            report = "There was an error generating response, please retry!"
            map_points = []
        st.session_state.results = {"report": report, "events": map_points}
    except Exception as e:
        logger.log(f"Error processing query: {e}")
        st.error(f"Error: {e}")


if st.session_state.results:
    with st.container():
        st.markdown("### Response:")
        st.markdown(st.session_state.results["report"])
        map_points = st.session_state.results["events"]
        if map_points and isinstance(map_points, list) and len(map_points) > 0:
            disaster_map = create_disaster_map(map_points)
            st_folium(disaster_map, use_container_width=True)

st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
st.divider()

footer_html = getFooterHtml()
st.markdown(footer_html, unsafe_allow_html=True)