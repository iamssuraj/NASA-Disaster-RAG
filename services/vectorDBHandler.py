import os
from services.apiService import fetch_nasa_events
from utils.logger import logger
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


load_dotenv("app.config")
load_dotenv()

def get_embedding_model():
    
    try:
        model = os.getenv("EMBEDDING_MODEL")
        logger.log(f"Initializing HuggingFace embeddings: {model}")
        return HuggingFaceEmbeddings(model_name=model)
    except Exception as e:
        logger.log(f"Error initializing embeddings: {e}")
        raise RuntimeError(f"Failed to initialize embeddings: {e}")

def get_vector_store():
    
    try:
        embedding_model = get_embedding_model()
        collection_name = os.getenv("COLLECTION_NAME")
        db_path = os.getenv("CHROMA_DB_PATH")
        logger.log(f"Initializing vector store: {collection_name} at {db_path}")
        vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=db_path,
            embedding_function=embedding_model
        )
        return vector_store
    except Exception as e:
        logger.log(f"Error initializing vector store: {e}")
        raise RuntimeError(f"Failed to initialize vector store: {e}")


def extract_nasa_event_data(event):
    try:
        event_id = event.get("id")
        title = event.get("title")
        categories = event.get("categories")
        category_names = ", ".join([cat.get("title") for cat in categories])
        
        geometries = event.get("geometry")
        if geometries:
            coordinates = geometries[0].get("coordinates", [])
            if len(coordinates) > 1:
                lon = coordinates[0]
                lat = coordinates[1]
            date = geometries[0].get("date")
        
        return {
            "id": event_id,
            "title": title,
            "category": category_names,
            "latitude": lat,
            "longitude": lon,
            "date": date
        }
    except Exception as e:
        logger.log(f"Error extracting event data: {e}")
        return None

def create_documents_from_events(events):
    
    documents = []
    
    for event in events:
        data = extract_nasa_event_data(event)
        if data and data["latitude"] and data["longitude"]:
            content = f"Disaster Event: {data['title']}\nType: {data['category']}\nLocation: Lat {data['latitude']}, Lon {data['longitude']}\nDate: {data['date']}"
            doc = Document(
                page_content=content,
                metadata={
                    "event_id": data["id"],
                    "title": data["title"],
                    "category": data["category"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "date": data["date"]
                }
            )
            documents.append(doc)
    
    logger.log(f"Extracted {len(documents)} events from {len(events)} raw events")
    return documents

def populate_vector_store(vector_store, documents, batch_size=100):
    
    try:
        total_docs = len(documents)
        logger.log(f"Starting to add {total_docs} documents in batches of {batch_size}")
        
        for i in range(0, total_docs, batch_size): # using this because it takes a lot of time to train all docs directly in one go, also we can try showing progressing in future, logging it for now
            batch = documents[i:i + batch_size]
            vector_store.add_documents(batch)
            logger.log(f"Added batch {i//batch_size + 1}: {len(batch)} documents ({i + len(batch)}/{total_docs})")
        
        logger.log(f"Vector store operation complete: Added {total_docs} documents to store")
    except Exception as e:
        logger.log(f"Error adding documents to vector store: {e}")
        raise RuntimeError(f"Failed to add documents: {e}")

def get_retriever(k=10):
    
    try:
        vector_store = get_vector_store()
        search_kwargs = {"k": k}
        logger.log(f"Retriever initialized with k={k}")
        return vector_store.as_retriever(search_kwargs=search_kwargs)
    except Exception as e:
        raise RuntimeError(f"Failed to create retriever: {e}")

def load_disaster_events():
    
    logger.log("Starting disaster events loading process")
    
    events = fetch_nasa_events(
        limit=int(os.getenv("NASA_DEFAULT_LIMIT")),
        days=int(os.getenv("NASA_DEFAULT_DAYS"))
    )
    
    logger.log(f"Fetched {len(events)} raw events from API")
    
    documents = create_documents_from_events(events)
    logger.log(f"Created {len(documents)} documents from {len(events)} events")
    
    return documents
