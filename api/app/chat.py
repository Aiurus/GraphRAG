import logging
from typing import List, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
# from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import LLMChain
from langchain.chains import GraphCypherQAChain

from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from utils import (
    _format_chat_history,
    entity_chain,
    format_docs,
    generate_full_text_query,
    graph,
    llm,
    vector_index,
    import_cypher_query,
)

# Condense a chat history and follow-up question into a standalone question
rewrite_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(rewrite_template)

# RAG answer synthesis prompt
template = """You are a helpful assistant that answers questions based on the provided context.

---Special Instructions---
1. When answering salary-related questions, prioritize mentioning positions with the highest salaries. For instance, if asked about "4 lakhs annually," focus on high-paying roles like Automotive Engineer and Manufacturing Engineer rather than lower-paying positions.
2. Ensure all responses are closely related to the recruitment theme. Avoid discussing information unrelated to job positions, companies, or the application process.
3. When encountering ambiguous queries, attempt to understand the job seeker's potential intentions. For example, "company benefits" could be interpreted as inquiries about health insurance, paid time off, or professional development opportunities.
4. If asked about specific skills or qualifications, only mention those explicitly stated in the provided data. Do not assume or infer requirements not listed in the job descriptions.
5. When comparing multiple positions, focus on objective data points such as salary, required experience, and listed responsibilities. Avoid making subjective judgments about which job is "better" unless specifically asked to do so based on certain criteria.
6. Numerical Data Handling (CRITICAL):
   a. Always treat scores and ratings as numerical values, not text.
   b. When sorting or ranking based on scores:
      - Create a list of tuples (item, score).
      - Convert all scores to numbers (if not already).
      - Sort the list based on these numerical values.    
   c. When selecting top N items:
      - After sorting, select the first N items from the list.
   d. Always double-check your sorting and selection before answering.
7. For questions about top aptitudes or skills:
   a. Use ONLY the "Aptitude Ratings" section in the data.
   b. Follow the exact sorting process in instruction 6.
   c. List selected aptitudes from highest score to lowest.
   d. Include the numerical score for each aptitude.
   e. Verify that your top selections are correct by manually comparing their scores.
8. For salary-related queries specific to certain locations (e.g., villages), refer to the "Geographic Salary Ratings" section and use the appropriate salary range for that location category.
9. Before finalizing any answer involving numerical rankings or selections:
   a. Explicitly list out all relevant items with their scores.
   b. Show your sorting process step-by-step.
   c. Confirm that the final order is correct by manually comparing the top few scores.
10. When asked for top N aptitudes or skills:
    a. Use ONLY the "Aptitude Ratings" section in the data.
    b. List ALL aptitudes with their scores.
    c. Sort them in descending order of scores.
    d. Select the top N aptitudes based on this sorted list.
    e. In case of ties, include all aptitudes with the same score.
    f. Always show your work by listing all aptitudes, their scores, and the sorting process.
11. Tie-breaking rule:
    When selecting top N items and there's a tie for the Nth position, include ALL items with that score. This may result in more than N items being listed.
12. Verification step:
    After sorting and selecting the top items, manually verify that:
    a. All items with the same score as the Nth item are included.
    b. No item with a higher score than the Nth item is excluded.
    c. The total number of items may exceed N if there are ties.

Answer the question based only on the following context:
<context>
{context}
</context>
If the context doesn't provide any helpful information, say that you don't know the answer.
"""

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{question}"),
    ]
)

_search_query = RunnableBranch(
    # If input includes chat_history, we condense it with the follow-up question
    (
        RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
            run_name="HasChatHistoryCheck"
        ),  # Condense follow-up question and chat into a standalone_question
        RunnablePassthrough.assign(
            chat_history=lambda x: _format_chat_history(x["chat_history"])
        )
        | CONDENSE_QUESTION_PROMPT
        | llm,
    ),
    # Else, we have no chat history, so just pass through the question
    RunnableLambda(lambda x: x["question"]),
)

def query_generate(question):
    CYPHER_GENERATION_TEMPLATE = """## Introduction  
    This prompt is designed to help translate natural language questions into Cypher queries for a graph database. 
    The database schema encapsulates various aspects of job profiles, such as job roles, aptitudes, and employers.  

    Schema:
    {schema}

    Note: Do not include any explanations or apologies in your responses.
    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.
    Do not include any text except the generated Cypher statement.

    ## Example Questions and Queries  
    1. **Question**: Which employers are known for hiring in the healthcare sector?  
    **Cypher Query**:  
    MATCH (j:JobProfile)-[:EMPLOYED_BY]->(e:Employer)  
    WHERE j.sector = 'Healthcare'  
    RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

    2. **Question**: What are the top 3 aptitudes I would need to excel as an Retail Sales Associate?
    **Cypher Query**
    MATCH (j:JobProfile {{jobRole: "Retail Sales Associate"}})-[r:HAS_APTITUDE]->(a:Aptitude)
    RETURN a.attribute
    ORDER BY r.score DESC
    LIMIT 3

    ## Instructions for Translation  
    When given a natural language question, identify the relevant entities and relationships. Construct a Cypher query by mapping elements of the question to nodes and relationships in the graph database schema.  

    ## Question: {question}  
    Now, only write down the query statement without any surrounding Markdown formatting elements.
    """  
    # cypher_llm_chain = LLMChain(  
    #     llm=llm,  
    #     prompt=PromptTemplate.from_template(cypher_prompt_template)  
    # )  
    
    
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
    )

    cypher_llm_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
    )
    response = cypher_llm_chain.run(question)
    return response.strip()

# # Fulltext index query
def structured_retriever(question: str) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    result = ""
    # cypher_query = query_generate(question)
    # print(cypher_query, "==============cypher_query===================")
    # response = graph.query(cypher_query)
    response = query_generate(question)
    print(response, "===========response=======================")
    result = "\n".join(response)
    return result

def retriever(input) -> str:
    print(input)
    # Rewrite query if needed
    query = input.get("search_query")
    if not isinstance(query, str):
        query = query.content
    # Retrieve documents from vector index
    documents = format_docs(vector_index.similarity_search(query))
    if input.get("question", {}).get("mode") == "basic_hybrid_search_node_neighborhood":
        structured_data = structured_retriever(query)
        print(structured_data, "=============structured_data===============")
        documents = f"""Structured data:
        {structured_data}
        Unstructured data:
        {documents}"""
    return documents


chain = (
    RunnableParallel(
        {
            "question": RunnablePassthrough(),
            "chat_history": lambda x: (
                _format_chat_history(x["chat_history"]) if x.get("chat_history") else []
            ),
            "search_query": _search_query,
        }
    )
    | RunnableParallel(
        {
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"],
            "context": retriever,
        }
    )
    | ANSWER_PROMPT
    | llm
    | StrOutputParser()
)


# Add typing for input
class ChainInput(BaseModel):
    question: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )
    mode: str


chain = chain.with_types(input_type=ChainInput)
