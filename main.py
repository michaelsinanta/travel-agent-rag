import os
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

database_uri = st.secrets["DATABASE_URI"]
api_key = st.secrets["TOGETHER_API_KEY"]

db = SQLDatabase.from_uri(database_uri)

llm = ChatOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=api_key,
    model="mistralai/Mixtral-8x22B-Instruct-v0.1",
)

ask_prompt = """
    You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".
    Pay attention for queries containing names or place identifiers, search for the closest matching results, allowing partial matches and common abbreviations.

    Use the following format:

    Question: "Question here"
    SQLQuery: "SQL Query to run"
    SQLResult: "Result of the SQLQuery"
    Answer: "Final answer here"

    Only use the following tables:
    {table_info}

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
