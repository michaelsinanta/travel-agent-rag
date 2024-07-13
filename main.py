import os
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.prompts import PromptTemplate

database_uri = st.secrets["DATABASE_URI"]
api_key = st.secrets["TOGETHER_API_KEY"]

db = SQLDatabase.from_uri(database_uri)

llm = ChatOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=api_key,
    model="Qwen/Qwen2-72B-Instruct",
    temperature=0,
)

ask_prompt = """
    You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run,
    When your query involves specific names or locations, make sure to expand your search to include partial search and common abbreviations. Use a query that includes wildcards to cover all variations available.
    Then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".
    
    When your query involves specific names or locations, expand your search to include partial searches and common abbreviations. Use a SQL query that includes wildcards to cover variations. Make sure to find matches where the search term appears as the first word, last word, or any word within the name.
    Example SQL Query:
    SELECT "phone", "website"
    FROM accommodations
    WHERE "name" LIKE '%Alila%' AND "name" LIKE '%Uluwatu%';
    This query ensures that the search term "Alila Uluwatu" is matched whether it appears at the beginning, end, or anywhere within the name.

    Use the following format:

    Question: "Question here"
    SQLQuery: "SQL Query to run"
    SQLResult: "Result of the SQLQuery"
    Answer: "Final answer here"

    Only use the following tables:
    {table_info}

    --
    -- Name: accommodation_faqs; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.accommodation_faqs (
        id character varying(26) NOT NULL,
        accommodation_id character varying(26),
        question text NOT NULL,
        answer text NOT NULL,
        category character varying(50)
    );


    --
    -- Name: accommodation_reviews; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.accommodation_reviews (
        id character varying(26) NOT NULL,
        accommodation_id character varying(26),
        user_id character varying(26),
        rating integer,
        comment text,
        created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
    );


    --
    -- Name: accommodations; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.accommodations (
        id character varying(26) NOT NULL,
        name character varying(255) NOT NULL,
        description text,
        destination_id character varying(26),
        address character varying(255),
        phone character varying(20),
        website character varying(255),
        rating numeric(3,2)
    );


    --
    -- Name: attraction_faqs; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.attraction_faqs (
        id character varying(26) NOT NULL,
        attraction_id character varying(26),
        question text NOT NULL,
        answer text NOT NULL,
        category character varying(50)
    );


    --
    -- Name: attraction_reviews; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.attraction_reviews (
        id character varying(26) NOT NULL,
        attraction_id character varying(26),
        user_id character varying(26),
        rating integer,
        comment text,
        created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
    );


    --
    -- Name: attractions; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.attractions (
        id character varying(26) NOT NULL,
        name character varying(255) NOT NULL,
        description text,
        destination_id character varying(26),
        address character varying(255),
        phone character varying(20),
        website character varying(255),
        type character varying(50)
    );


    --
    -- Name: destination_faqs; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.destination_faqs (
        id character varying(26) NOT NULL,
        destination_id character varying(26),
        question text NOT NULL,
        answer text NOT NULL,
        category character varying(50)
    );


    --
    -- Name: destination_reviews; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.destination_reviews (
        id character varying(26) NOT NULL,
        destination_id character varying(26),
        user_id character varying(26),
        rating integer,
        comment text,
        created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
    );


    --
    -- Name: destinations; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.destinations (
        id character varying(26) NOT NULL,
        name character varying(255) NOT NULL,
        description text,
        country character varying(255),
        continent character varying(255),
        city character varying(255)
    );


    --
    -- Name: travel_tips; Type: TABLE; Schema: public; Owner: -
    --

    CREATE TABLE public.travel_tips (
        id character varying(26) NOT NULL,
        title character varying(255) NOT NULL,
        content text,
        destination_id character varying(26),
        category character varying(50)
    );

    Questions:{input}
"""

execute_query = QuerySQLDataBaseTool(db=db)
write_query = create_sql_query_chain(
    llm,
    db,
    prompt=PromptTemplate(
        input_variables=["input", "top_k", "table_info"], template=ask_prompt
    ),
)

answer_prompt = PromptTemplate.from_template(
    """
        Given the following user question and corresponding SQL result, answer the user question to the best of your ability in Indonesian. Always respond in Indonesian. If there is no valid SQL query provided or the results are unexpected, acknowledge the input and provide a general response related to the topic in Indonesian.
        
        Question: {question}
        SQL Query: {query}
        SQL Result: {result}

        Remember this important rule: if you do not have sufficient information to answer the question, do not mention SQL, SQL queries, or any related errors.
        Use markdown syntax in prompts to structure response
        Answer (in Indonesian): 
    """
)

chain = (
    RunnablePassthrough.assign(query=write_query).assign(
        result=itemgetter("query") | execute_query
    )
    | answer_prompt
    | llm
    | StrOutputParser()
)

st.title("Travel Agent Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        result = chain.invoke(
            {
                "top_k": 50,
                "question": question,
                "table_info": db.get_usable_table_names(),
            }
        )
        st.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": result})
