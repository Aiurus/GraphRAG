ANSWER_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on the provided context.

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
schema = """
## Schema:
### Node properties:
   Chunk {{text: STRING, embedding: LIST, id: STRING, index: STRING}}
   JobProfile {{text: STRING, id: STRING, sector: STRING, subSector: STRING, descriptionText: STRING, mediaURL: STRING, mediaURLsMale: STRING, mediaURLsFemale: STRING, collegeCategory: STRING, jobRole: STRING, jobLocation: STRING, experienceLevel: STRING, dayInTheLifeText: STRING, deleted: BOOLEAN}}
   PrepareForRole {{heading: STRING}}
   ReasonDisliked {{reason: STRING}}
   Aptitude {{attribute: STRING}}
   Interest {{attribute: STRING}}
   Value {{attribute: STRING}}
   CareerPathway {{title: STRING, description: STRING}}
   JobRole {{title: STRING, years: STRING}}
   Employer {{name: STRING, description: STRING, website: STRING}}
   EmployerProfile {{geographicOption: STRING}}
   GeographicDetail {{option: STRING}}
### Relationship properties:
   HAS_APTITUDE {{score: FLOAT}}
   HAS_INTEREST {{score: FLOAT}}
   HAS_VALUE {{score: FLOAT}}
   HAS_EMPLOYER_PROFILE {{profiles: STRING}}
   HAS_GEOGRAPHIC_DETAIL {{jobAvailability: STRING, estimatedSalaryRange: STRING, maximumSalary: INTEGER, minimumSalary: INTEGER}}
### The relationships:
   (:JobProfile)-[:ForRole]->(:PrepareForRole)
   (:JobProfile)-[:DISLIKED_FOR]->(:ReasonDisliked)
   (:JobProfile)-[:HAS_APTITUDE]->(:Aptitude)
   (:JobProfile)-[:HAS_INTEREST]->(:Interest)
   (:JobProfile)-[:HAS_VALUE]->(:Value)
   (:JobProfile)-[:HAS_CAREER_PATHWAY]->(:CareerPathway)
   (:JobProfile)-[:EMPLOYED_BY]->(:Employer)
   (:JobProfile)-[:HAS_EMPLOYER_PROFILE]->(:EmployerProfile)
   (:JobProfile)-[:HAS_GEOGRAPHIC_DETAIL]->(:GeographicDetail)
   (:JobProfile)-[:HAS_CHUNK]->(:Chunk)
   (:CareerPathway)-[:HAS_JOB_ROLE]->(:JobRole)

"""

CYPHER_GENERATION_PROMPT_TEMPLATE = """
## Overview
This prompt aims to assist in converting natural language queries into Cypher queries for a graph database focused on job profiles, capturing various elements like job roles, skills, and employers.

Schema:
{schema}

Important: Exclude explanations or apologies in your responses. Use only the provided relationship types and properties as per the schema guidelines. Avoid any unrelated types or properties, and present only the resulting Cypher query.

## Cypher Query Construction Guidelines
MATCH: Initiate with MATCH to outline nodes and relationships. Employ labels and properties for node filtering.
WHERE: Use WHERE for additional criteria to refine results.
RETURN: Specify desired outputs using the RETURN clause.
Aggregation: For data aggregation, apply the WITH clause with functions like COUNT, SUM, AVG, etc., prior to RETURN.
Avoid Non-Cypher Keywords: Refrain from using SQL-specific keywords like GROUP; instead, use Cypher's WITH for aggregations.
Additional Clauses: Implement OPTIONAL MATCH for optional patterns, and ORDER BY, SKIP, LIMIT for manipulating results.
Modification Commands: For data updates, use CREATE, SET, DELETE, or MERGE where necessary.

## Essential Instructions:
# Use Pre-existing Examples:
If the question matches an example, apply the matching Cypher query directly.

# Adherence to Schema:
Node Labels, Properties, and Relationships: These must strictly follow the schema definitions. Convert terms from the input to the closest schema-defined entity.
Adjustments: For queries like "average salary of Data Entry Clerk in small cities," interpret 'small cities' as geoGraphicDetail.option 'Medium & Small Cities' per the schema.

# Mapping Standards:
geoGraphicDetail.option: Stick to 'Large Cities', 'Medium & Small Cities', 'Towns & Villages'.
JobProfile.collegeCategory: Limit to 'College' or 'Non-College'.
Aptitude.attribute: Choose from 'Logical Reasoning and Analytical Skills', 'Verbal Ability and Communication Skills', 'Numerical Aptitude', 'Creative Thinking and Innovation', 'Spatial Awareness', 'Interpersonal Skills', 'Technical Proficiency', 'Organizational Skills', 'Entrepreneurial Skills', 'Physical and Manual Skills'.
Interest.attribute: Select from 'Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'.
Value.attribute: Opt from 'Work-Life Balance', 'Achievement', 'Independence', 'Recognition', 'Supportive Environment', 'Compensation', 'Security'.

# Query Verification:
Cross-check all queries for schema accuracy.
Test queries in a Neo4j database to ensure expected outcomes.

## Sample Questions and Queries
Question: Which employers are notable for hiring in the healthcare industry?
Cypher Query:
MATCH (j:JobProfile)-[:EMPLOYED_BY]->(e:Employer) WHERE j.sector = 'Healthcare' RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

Question: Top 3 aptitudes needed for excelling as a Retail Sales Associate?
Cypher Query:
MATCH (j:JobProfile {{jobRole: "Retail Sales Associate"}})-[r:HAS_APTITUDE]->(a:Aptitude) RETURN a.attribute ORDER BY r.score DESC LIMIT 3

Question: Salary information for Automotive Engineer role?
Cypher Query:
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) WHERE g.option = 'Large Cities' RETURN r.estimatedSalaryRange AS EstimatedSalaryRange

Question: Companies recognized for hiring Software Engineers?
Cypher Query:
MATCH (j:JobProfile {{jobRole: 'Software Engineer'}})-[:EMPLOYED_BY]->(e:Employer) RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

Question: Educational qualifications for an Automotive Engineer?
Cypher Query:
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[:ForRole]->(p:PrepareForRole) RETURN p.heading AS EducationalQualifications, p.educationVsDegree AS EducationVsDegree

Question: Employers known for healthcare sector jobs?
Cypher Query:
MATCH (j:JobProfile)-[:EMPLOYED_BY]->(e:Employer) WHERE j.sector = 'Healthcare' RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

Question: Role with a college degree offering the highest salary in small cities?
Cypher Query:
MATCH (j:JobProfile) WHERE j.collegeCategory = 'College' MATCH (j)-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) WHERE g.option = 'Medium & Small Cities' RETURN j.jobRole AS JobRole, r.maximumSalary AS MaximumSalary ORDER BY r.maximumSalary DESC LIMIT 1

## Translation Approach
Upon receiving a natural language question, identify relevant nodes and relationships and assemble a Cypher query by correlating the question's elements with nodes and relationships from the graph schema.

Question: {question}
Now, compose only the query statement without any associated Markdown formatting elements.
"""

OLD_CYPHER_GENERATION_PROMPT_TEMPLATE = """## Introduction  
This prompt is designed to help translate natural language questions into Cypher queries for a graph database. 
The database schema encapsulates various aspects of job profiles, such as job roles, aptitudes, and employers.  

## Schema:
### Node properties:
   Chunk {{text: STRING, embedding: LIST, id: STRING, index: STRING}}
   JobProfile {{text: STRING, id: STRING, sector: STRING, subSector: STRING, descriptionText: STRING, mediaURL: STRING, mediaURLsMale: STRING, mediaURLsFemale: STRING, collegeCategory: STRING, jobRole: STRING, jobLocation: STRING, experienceLevel: STRING, dayInTheLifeText: STRING, deleted: BOOLEAN}}
   PrepareForRole {{heading: STRING}}
   ReasonDisliked {{reason: STRING}}
   Aptitude {{attribute: STRING}}
   Interest {{attribute: STRING}}
   Value {{attribute: STRING}}
   CareerPathway {{title: STRING, description: STRING}}
   JobRole {{title: STRING, years: STRING}}
   Employer {{name: STRING, description: STRING, website: STRING}}
   EmployerProfile {{geographicOption: STRING}}
   GeographicDetail {{option: STRING}}
### Relationship properties:
   HAS_APTITUDE {{score: FLOAT}}
   HAS_INTEREST {{score: FLOAT}}
   HAS_VALUE {{score: FLOAT}}
   HAS_EMPLOYER_PROFILE {{profiles: STRING}}
   HAS_GEOGRAPHIC_DETAIL {{jobAvailability: STRING, estimatedSalaryRange: STRING, maximumSalary: INTEGER, minimumSalary: INTEGER}}
### The relationships:
   (:JobProfile)-[:ForRole]->(:PrepareForRole)
   (:JobProfile)-[:DISLIKED_FOR]->(:ReasonDisliked)
   (:JobProfile)-[:HAS_APTITUDE]->(:Aptitude)
   (:JobProfile)-[:HAS_INTEREST]->(:Interest)
   (:JobProfile)-[:HAS_VALUE]->(:Value)
   (:JobProfile)-[:HAS_CAREER_PATHWAY]->(:CareerPathway)
   (:JobProfile)-[:EMPLOYED_BY]->(:Employer)
   (:JobProfile)-[:HAS_EMPLOYER_PROFILE]->(:EmployerProfile)
   (:JobProfile)-[:HAS_GEOGRAPHIC_DETAIL]->(:GeographicDetail)
   (:JobProfile)-[:HAS_CHUNK]->(:Chunk)
   (:CareerPathway)-[:HAS_JOB_ROLE]->(:JobRole)

Note: Do not include any explanations or apologies in your responses.
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Do not include any text except the generated Cypher statement.

## Guidelines for Cypher Query Generation
MATCH: Begin with MATCH to specify the nodes and relationships involved. Use labels and properties to filter nodes.
WHERE: If further filtering is needed, use the WHERE clause to specify conditions.
RETURN: Define what you want to retrieve from the database using the RETURN clause.
Aggregation: When aggregating data, utilize the WITH clause in conjunction with aggregate functions like COUNT, SUM, AVG, etc., before RETURN.
Avoid Invalid Keywords: Do not include SQL-specific keywords such as GROUP. Use Cypher’s native constructs like WITH for intermediate aggregations.
Additional Clauses: Utilize optional clauses such as OPTIONAL MATCH for optional patterns, and ORDER BY, SKIP, LIMIT for result manipulation.
Modification Operations: For data modifications, start with CREATE, SET, DELETE, or MERGE as applicable.

## Key Instructions:
1. Leverage Examples:
If the input question matches an existing example, directly use the corresponding Cypher query instead of generating a new one.

2. Schema Compliance:
Node Labels, Properties, and Relationships: Ensure they match exactly with those defined in the schema. Translate any input terms to the closest defined entity in the schema.
Example Adjustments: For questions like "what is the average salary of Data Entry Clerk in small cities?", map 'small cities' to geoGraphicDetail.option as 'Medium & Small Cities' as specified in the schema.

3. Mapping Guide: 
geoGraphicDetail.option: Use only predefined categories - 'Large Cities', 'Medium & Small Cities', 'Towns & Villages'.
JobProfile.collegeCategory: Restrict values to 'College' or 'Non-College'.
Aptitude.attribute: Use only predefined categories -  'Logical Reasoning and Analytical Skills', 'Verbal Ability and Communication Skills', 'Numerical Aptitude', 'Creative Thinking and Innovation', 'Spatial Awareness', 'Interpersonal Skills', 'Technical Proficiency', 'Organizational Skills', 'Entrepreneurial Skills', or 'Physical and Manual Skills'.
Interest.attribute: Use only predefined categories - 'Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', or 'Convertional'
Value.attribute: Use only predefined categories - 'Work-Life Balance', 'Achievement', 'Independence', 'Recognition', 'Supportive Environment', 'Compensation', or 'Security'

4. Execution Strategy:
Double-check all generated queries against the schema to ensure compliance.
Validate the logic by testing queries on a Neo4j graph database to confirm that results align with expectations.

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

3. **Question**: What is the salary of Automotive Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) 
WHERE g.option = 'Large Cities' 
RETURN r.estimatedSalaryRange AS EstimatedSalaryRange

4. **Question**: Which companies are well known for hiring Software Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Software Engineer'}})-[:EMPLOYED_BY]->(e:Employer) 
RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

5. **Question**: What educational qualifications are necessary for becoming an Automotive Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[:ForRole]->(p:PrepareForRole) 
RETURN p.heading AS EducationalQualifications, p.educationVsDegree AS EducationVsDegree

6. **Question**: "Which employers are known for hiring in the healthcare sector?",
**Cypher Query**
MATCH (j:JobProfile)-[:EMPLOYED_BY]->(e:Employer) 
WHERE j.sector = 'Healthcare' 
RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

7. **Question**: "Which role with a college degree has highest salary in small cities?",
**Cypher Query**
MATCH (j:JobProfile) WHERE j.collegeCategory = 'College' 
MATCH (j)-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) 
WHERE g.option = 'Medium & Small Cities' 
RETURN j.jobRole AS JobRole, r.maximumSalary AS MaximumSalary 
ORDER BY r.maximumSalary DESC LIMIT 1


## Instructions for Translation  
When given a natural language question, identify the relevant entities and relationships. Construct a Cypher query by mapping elements of the question to nodes and relationships in the graph database schema.  

## Question: {question}  
Now, only write down the query statement without any surrounding Markdown formatting elements.
"""  

adsf = """
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

3. **Question**: What is the salary of Automotive Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) 
WHERE g.option = 'Large Cities' 
RETURN r.estimatedSalaryRange AS EstimatedSalaryRange

4. **Question**: Which companies are well known for hiring Software Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Software Engineer'}})-[:EMPLOYED_BY]->(e:Employer) 
RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

5. **Question**: What educational qualifications are necessary for becoming an Automotive Engineer?
**Cypher Query**
MATCH (j:JobProfile {{jobRole: 'Automotive Engineer'}})-[:ForRole]->(p:PrepareForRole) 
RETURN p.heading AS EducationalQualifications, p.educationVsDegree AS EducationVsDegree

6. **Question**: "Which employers are known for hiring in the healthcare sector?",
**Cypher Query**
MATCH (j:JobProfile)-[:EMPLOYED_BY]->(e:Employer) 
WHERE j.sector = 'Healthcare' 
RETURN DISTINCT e.name AS EmployerName, e.description AS EmployerDescription

7. **Question**: "Which role with a college degree has highest salary in small cities?",
**Cypher Query**
MATCH (j:JobProfile) WHERE j.collegeCategory = 'College' 
MATCH (j)-[r:HAS_GEOGRAPHIC_DETAIL]->(g:GeographicDetail) 
WHERE g.option = 'Medium & Small Cities' 
RETURN j.jobRole AS JobRole, r.maximumSalary AS MaximumSalary 
ORDER BY r.maximumSalary DESC LIMIT 1

"""
add = """
## if question is in example, use it, not generate new one.
## VERY IMPORANT: In cypher, you MUST use node labels, properties and relationships defined in schema. 
for example, if question is "what is the average salary of Data Entry Clerk in small cities?", geoGraphicDetail.option should be 'Medium & Small Cities', not 'small cities' which include in question.
In other word, if entities in question isn't contained in schema, you must find the most similar node, properties or relationship defined in schema.

geoGraphicDetail.option should be one of 'Large Cities', 'Medium & Small Cities' or 'Towns & Villages'.
JobProfile.collegeCategory should be one of 'College' or 'Non-College'.
Aptitude.attribute should be one of 'Logical Reasoning and Analytical Skills', 'Verbal Ability and Communication Skills', 'Numerical Aptitude', 'Creative Thinking and Innovation', 'Spatial Awareness', 'Interpersonal Skills', 'Technical Proficiency', 'Organizational Skills', 'Entrepreneurial Skills', or 'Physical and Manual Skills'.
Interest.attribute should be one of 'Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', or 'Convertional'
Value.attribute should be one of 'Work-Life Balance', 'Achievement', 'Independence', 'Recognition', 'Supportive Environment', 'Compensation', or 'Security'


"""
## Question: {question}  
# Now, only write down the query statement without any surrounding Markdown formatting elements.
