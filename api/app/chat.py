import logging
from typing import List, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import LLMChain
from langchain.chains import GraphCypherQAChain
from langchain.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from langchain_core.messages import AIMessage, HumanMessage
from langchain.callbacks import get_openai_callback

from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from utils import (
    _format_chat_history,
    format_docs,
    graph,
    llm,
    vector_index,
)

from prompt import (
    ANSWER_PROMPT_TEMPLATE,
    CYPHER_GENERATION_PROMPT_TEMPLATE,
)

rewrite_template = """
Given the following conversation and a follow-up question, rewrite the follow-up question as a standalone question so that it can be easily understood and parsed by an LLM. 
Double Check the spelling and grammar of the question.
Chat History:
{chat_history}
Follow Up Input: {question}
"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(rewrite_template)

# RAG answer synthesis prompt

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", ANSWER_PROMPT_TEMPLATE),
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
    
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_PROMPT_TEMPLATE
    )

    QA_TEMPLATE = """You are an assistant that helps to form nice and human understandable answers.
    The information part contains the provided information that you must use to construct an answer.
    The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
    Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
    If there is salary information, the currency unit is '₹'.
    For questions about salaries, please check whether it is a monthly or annual salary and process it accordingly.
    Here is an example:

    Question: Which managers own Neo4j stocks?
    Context:[manager:CTL LLC, manager:JANE STREET GROUP LLC]
    Helpful Answer: CTL LLC, JANE STREET GROUP LLC owns Neo4j stocks.

    Follow this example when generating answers.
    If the provided information is empty, say that you don't know the answer.
    Information:
    {context}

    Question: {question}
    Helpful Answer:"""
    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"], template=QA_TEMPLATE
    )
    cypher_llm_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        qa_prompt=QA_PROMPT
    )
    response = cypher_llm_chain.invoke(question)
    return response['result']

def structured_retriever(question: str) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    response = query_generate(question)
    return response

def retriever(input) -> str:
    query = input.get("search_query")
    if not isinstance(query, str):
        query = query.content
    documents = format_docs(vector_index.similarity_search(query, 5))
    print(documents, "================================")
    if input.get("question", {}).get("mode") == "basic_hybrid_search_node_neighborhood":
        structured_data = structured_retriever(query)
        if (structured_data != "I don't know the answer."):
            documents = f"""Structured data:
            {structured_data}
            Unstructured data:
            {documents}"""
    return documents


chain = (
    RunnableParallel(
        {
            "question": RunnablePassthrough(),
            "chat_history": lambda x: [],
            "search_query": _search_query,
        }
    )
    | RunnableParallel(
        {
            "question": lambda x: x["question"],
            "chat_history": lambda x: [],
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
    mode: str


chain = chain.with_types(input_type=ChainInput)
