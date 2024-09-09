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
from langchain.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema


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

from prompt import CYPHER_GENERATION_PROMPT_TEMPLATE

# Condense a chat history and follow-up question into a standalone question
rewrite_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(rewrite_template)

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
    # cypher_llm_chain = LLMChain(  
    #     llm=llm,  
    #     prompt=PromptTemplate.from_template(cypher_prompt_template)  
    # )  
    
    
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_PROMPT_TEMPLATE
    )

    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in graph.structured_schema.get("relationships")
    ]
    cypher_validation = CypherQueryCorrector(corrector_schema)

    cypher_llm_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
    )
    response = cypher_llm_chain.invoke(question)
    result = response['result']
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
