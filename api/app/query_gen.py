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

from langchain import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI
from langchain_core.prompts import PromptTemplate

def query_generate(question):
    cypher_prompt_template = """## Introduction  
    This prompt is designed to help translate natural language questions into Cypher queries for a graph database. The database schema encapsulates various aspects of job profiles, such as job roles, aptitudes, and employers.  

    ## Schema Overview  

    - **Entities (Nodes)**  
    - `JobProfile`: Properties include `id`, `sector`, `subSector`, `descriptionText`, and more.  
    - `PrepareForRole`: Captures educational and training aspects.  
    - `ReasonLiked`, `ReasonDisliked`: Represents reasons someone might like or dislike a job.  
    - `Aptitude`, `Interest`, `Value`: Attributes with associated scores.  
    - `CareerPathway`: Includes `title` and `description`, connected to job roles.  
    - `Employer`, `EmployerProfile`: Information about potential employers.  
    - `GeographicDetail`: Offers job availability and salary information per region.  

    - **Relationships**  
    - `ForRole`, `LIKED_FOR`, `DISLIKED_FOR`: Connect job profiles to preparation roles, likes, and dislikes.  
    - `HAS_APTITUDE`, `HAS_INTEREST`, `HAS_VALUE`: Links job profiles to various attributes with scores.  
    - `HAS_CAREER_PATHWAY`, `HAS_JOB_ROLE`: Connects career pathways to job roles.  
    - `EMPLOYED_BY`, `HAS_EMPLOYER_PROFILE`: Relates job profiles to employers.  
    - `HAS_GEOGRAPHIC_DETAIL`: Associates jobs with geographical data.  
    - `HAS_CHUNK`: Links to text content in the form of chunks.  

    ## Instructions for Translation  
    When given a natural language question, identify the relevant entities and relationships. Construct a Cypher query by mapping elements of the question to nodes and relationships in the graph database schema.  

    ## Question: {question}  
    Now, write down the query statement:
    """  

    llm = ChatOpenAI(temperature=0, model="gpt-4-turbo", streaming=True)
    cypher_llm_chain = LLMChain(  
        llm=llm,  
        prompt=PromptTemplate.from_template(cypher_prompt_template)  
    )  
    response = llm_chain.run(question=question)  
    return response.strip()

question = "How can I find job roles linked with the finance sector?"  
cypher_query = generate_cypher_query(question)  
print("Generated Cypher Query:")  
print(cypher_query)  