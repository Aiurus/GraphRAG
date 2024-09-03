from typing import Any, Dict, List, Tuple

from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import TokenTextSplitter

index_name = "news_vector"
keyword_index_name = "news_fulltext"
entity_keyword_index = "entity"

llm = ChatOpenAI(temperature=0, model="gpt-4-turbo", streaming=True)


def setup_indices():
    graph.query(
        "CREATE CONSTRAINT classification IF NOT EXISTS FOR (n:`Classification`) REQUIRE (n.name) IS UNIQUE;"
    )

    graph.query(
        "CREATE INDEX entity_range IF NOT EXISTS FOR (n:`__Entity__`) ON (n.name);"
    )
    graph.query(
        f"CREATE FULLTEXT INDEX {entity_keyword_index} IF NOT EXISTS FOR (n:`__Entity__`) ON EACH [n.name]",
    )
    graph.query(
        f"CREATE FULLTEXT INDEX {keyword_index_name} IF NOT EXISTS FOR (n:Chunk) ON EACH [n.text]",
    )
    graph.query(
        f"""CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n: Chunk) ON (n.embedding)
    OPTIONS {{indexConfig: {{
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
    }}}}""",
    )


graph = Neo4jGraph(enhanced_schema=False, refresh_schema=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Setup vector and keyword indices
setup_indices()

vector_index = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name=index_name,
    keyword_index_name=keyword_index_name,
    search_type="hybrid",
)

text_splitter = TokenTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


# Extract entities from text
class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the person, organization, or business entities that "
        "appear in the text",
    )


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting organization and person entities from the text.",
        ),
        (
            "human",
            "Use the given format to extract information from the following "
            "input: {question}",
        ),
    ]
)

entity_chain = prompt | llm.with_structured_output(Entities)


def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspelings.
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()


def remove_null_properties(data: Dict[str, Any]):
    if not data:
        return []
    # Process the 'nodes' part of the data
    for node in data["nodes"]:
        # Create a list of keys to remove (those that are None)
        keys_to_remove = [
            key for key, value in node["properties"].items() if value is None
        ]
        # Remove each key from the properties dictionary
        for key in keys_to_remove:
            node["properties"].pop(key)

    # Process the 'relationships' part of the data
    for relationship in data["relationships"]:
        # Create a list of keys to remove (those that are None)
        keys_to_remove = [
            key for key, value in relationship["properties"].items() if value is None
        ]
        # Remove each key from the properties dictionary
        for key in keys_to_remove:
            relationship["properties"].pop(key)

    return data

import_cypher_query = """
UNWIND $data AS row  
// Create or merge a JobProfile node  
MERGE (j:JobProfile {id: row.id})  
SET j.id = row.id,
    j.sector = row.sector,  
    j.subSector = row.subSector,  
    j.descriptionText = row.jobProfile.generalDescription.text,  
    j.mediaURL = row.jobProfile.generalDescription.mediaURL,  
    j.mediaURLsMale = row.jobProfile.generalDescription.mediaURLs.male,  
    j.mediaURLsFemale = row.jobProfile.generalDescription.mediaURLs.female,  
    j.collegeCategory = row.collegeCategory,  
    j.jobRole = row.jobRole,  
    j.jobLocation = row.jobLocation,  
    j.experienceLevel = row.experienceLevel,
    j.dayInTheLifeText = row.jobProfile.dayInTheLife.text,
    j.text = row.text,
    j.deleted = row.deleted

WITH j, row, row.jobProfile.prepareForRole.educationVsDegreeHeading as heading
MERGE (p:PrepareForRole {heading: heading})
MERGE (j)-[rel:ForRole]->(p)
SET rel.educationVsDegree = row.jobProfile.prepareforRole.educationVsDegree,
    rel.trainingNeeded = row.jobProfile.prepareforRole.trainingNeeded,
    rel.priorWorkExperience = row.jobProfile.prepareforRole.priorWorkExperience

// Handling Reason Liked  
WITH j, row
FOREACH (reasonLiked in row.jobProfile.reasonLiked |  
  MERGE (rl:ReasonLiked {reason: reasonLiked})  
  MERGE (j)-[:LIKED_FOR]->(rl)  
)  

// Handling Reason Disliked 
WITH j, row 
FOREACH (reasonDisliked in row.jobProfile.reasonsDisliked |  
  MERGE (rd:ReasonDisliked {reason: reasonDisliked})  
  MERGE (j)-[:DISLIKED_FOR]->(rd)  
)  

// Handling Aptitude Ratings  
WITH j, row
FOREACH (aptitude in row.aptitudeRatings |  
  MERGE (a:Aptitude {attribute: aptitude.attribute})  
  MERGE (j)-[rel:HAS_APTITUDE]->(a)
  SET rel.score = toFloat(aptitude.score)  
)  

// Handling Interested Ratings  
WITH j, row
FOREACH (interest in row.interestRatings |  
  MERGE (ir:Interest {attribute: interest.attribute})  
  MERGE (j)-[rel:HAS_INTEREST]->(ir)  
  SET rel.score = toFloat(interest.score)  
)  

// Handling Value Ratings  
WITH j, row
FOREACH (value in row.valueRatings |  
  MERGE (vr:Value {attribute: value.attribute})  
  MERGE (j)-[rel:HAS_VALUE]->(vr)  
  SET rel.score = toFloat(value.score)  
)  

// Handling Career Pathways  
WITH j, row
UNWIND row.careerPathways AS pathway  
  MERGE (cp:CareerPathway {title: pathway.pathwayTitle})  
  SET cp.description = pathway.description  
  MERGE (j)-[:HAS_CAREER_PATHWAY]->(cp)  
  // Handling Job Roles within Career Pathways  
  FOREACH (jobRole in pathway.jobRoles |  
    MERGE (jr:JobRole {title: jobRole.title, years: jobRole.years})  
    MERGE (cp)-[:HAS_JOB_ROLE]->(jr)  
  )  

// Handling Employers  
WITH j, row
FOREACH (employer in row.employers.wellKnownEmployers |  
  MERGE (e:Employer {name: employer.name})  
  SET e.description = employer.description,  
      e.website = employer.website  
  MERGE (j)-[:EMPLOYED_BY]->(e)  
)  

// Handling Employer Profiles  
WITH j, row
FOREACH (profile in row.employers.employerProfiles |  
  MERGE (ep:EmployerProfile {geographicOption: profile.geographicOption})  
  MERGE (j)-[rel:HAS_EMPLOYER_PROFILE]->(ep)  
  SET rel.profiles = profile.profiles  
)  

// Handling Geographic Job Details  
WITH j, row
FOREACH (geoDetail in row.geographicJobDetails |  
  MERGE (g:GeographicDetail {option: geoDetail.geographicOption})  
  MERGE (j)-[rel:HAS_GEOGRAPHIC_DETAIL]->(g)  
  SET rel.jobAvailability = geoDetail.jobAvailability,  
      rel.estimatedSalaryRange = geoDetail.estimatedSalaryRange,  
      rel.maximumSalary = geoDetail.maximumSalary,  
      rel.minimumSalary = geoDetail.minimumSalary  
)
WITH j, row
UNWIND row.chunks AS chunk
  MERGE (c:Chunk {id: chunk.index})
  SET c.text = chunk.text,
      c.index = chunk.index
  MERGE (j)-[:HAS_CHUNK]->(c)
  WITH c, chunk
  CALL db.create.setNodeVectorProperty(c, 'embedding', chunk.embedding)
"""
