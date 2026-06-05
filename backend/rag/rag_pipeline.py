from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


# Load PDF
loader = PyPDFLoader("data/brochure.pdf")

documents = loader.load()


# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

docs = text_splitter.split_documents(documents)


# Create embeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# Store in ChromaDB
vectorstore = Chroma.from_documents(
    docs,
    embedding_model,
    persist_directory="chroma_db"
)


# retriever = vectorstore.as_retriever()

# this one retrieves more relavant sections 
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 4}
)


def retrieve_relevant_context(query):

    results = retriever.invoke(query)

    context = "\n\n".join(
        [doc.page_content for doc in results]
    )

    return context