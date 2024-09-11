import logging
import os
from typing import Any, Dict, List, Optional

import requests
from utils import embeddings, text_splitter
import re
import json
from convert import process_json_element

CATEGORY_THRESHOLD = 0.50
params = []

DIFF_TOKEN = os.environ["DIFFBOT_API_KEY"]


def get_articles():
    """
    Fetch relevant articles from Diffbot KG endpoint
    """
    with open('TransformerService.job_profiles_3rdSep_100.json', 'r') as file:  
        data = json.load(file)
    return data


def getSalary(estimatedSalaryRange: str) -> List[int] :
    pattern = r'₹([\d,]+)'  

    # Find all matches and remove commas from the numbers  
    matches = [int(match.replace(',', '')) for match in re.findall(pattern, estimatedSalaryRange)]  
    return [matches[0], matches[1]]


def process_params(data):
    params = []
    all_chunks = []
    for article in data:
        text = process_json_element(article)
        article["text"] = text
        split_chunks = [
            {"text": el, "index": f"{article['_id']['$oid']}-{i}"}
            for i, el in enumerate(text_splitter.split_text(article["text"]))
        ]
        all_chunks.extend(split_chunks)
        mediaURLs = article["jobProfile"]["generalDescription"] .get("mediaURLs", {})  
        params.append(
            {
                "sector": article["sector"],
                "collegeCategory": article["collegeCategory"],
                "subSector": article["subSector"],
                "deleted": article["deleted"],
                "id": article["_id"]["$oid"],
                "jobProfile": {
                    "generalDescription": {
                        "text": article["jobProfile"]["generalDescription"]["text"],
                        "mediaURL": article["jobProfile"]["generalDescription"].get("mediaURL", ""),
                        "mediaURLs": {
                            "male": mediaURLs.get("male", ""),
                            "female": mediaURLs.get("female", ""),
                        }
                    },
                    "dayInTheLife": {
                        "text": article["jobProfile"]["dayInTheLife"]['text'],
                    },
                    "reasonLiked": [
                        el["reason"]
                        for el in article["jobProfile"].get("reasonLiked", [])
                    ],
                    "reasonsDisliked": [
                        el["reason"]
                        for el in article["jobProfile"].get("reasonsDisliked", [])
                    ],
                    "prepareForRole": {
                        "educationVsDegreeHeading": article["jobProfile"]["prepareForRole"]["educationVsDegreeHeading"],
                        "educationVsDegree": article["jobProfile"]["prepareForRole"]["educationVsDegree"],
                        "trainingNeeded": article["jobProfile"]["prepareForRole"]["trainingNeeded"],
                        "priorWorkExperience": article["jobProfile"]["prepareForRole"]["priorWorkExperience"],
                    },                
                },
                "aptitudeRatings": [
                    {
                        "attribute": el["attribute"],
                        "score": int(el["score"]),
                        "reason": el["reason"],
                    }
                    for el in article.get("aptitudeRatings", [])
                ],
                "interestRatings": [
                    {
                        "attribute": el["attribute"],
                        "score": int(el["score"]),
                        "reason": el["reason"],
                    }
                    for el in article.get("interestRatings", [])
                ],
                "valueRatings": [
                    {
                        "attribute": el["attribute"],
                        "score": int(el["score"]),
                        "reason": el["reason"],
                    }
                    for el in article.get("valueRatings", [])
                ],
                "careerPathways": [
                    {
                        "pathwayTitle": el["pathwayTitle"],
                        "description": el["description"],
                        "jobRoles": [
                            {
                                "title": jr["title"],
                                "years": jr["years"],
                            }
                            for jr in el["jobRoles"]
                        ],
                    }
                    for el in article.get("careerPathways", [])
                ],
                "jobLocation": article["jobLocation"],
                "jobRole": article["jobRole"],
                "employers": {
                    "wellKnownEmployers": [                    
                        {
                            "name": el["name"],
                            "description": el["description"],
                            "website": el["website"],
                        }
                        for el in article["employers"].get("wellKnownEmployers", [])
                    ],
                    "employerProfiles": [
                        {
                            "geographicOption": el["geographicOption"],
                            "profiles": el["profiles"],
                        }
                        for el in article["employers"].get("employerProfiles", [])
                    ]
                },
                "geographicJobDetails": [
                    {
                        "geographicOption": el["geographicOption"],
                        "jobAvailability": el["jobAvailability"],
                        "estimatedSalaryRange": el["estimatedSalaryRange"],
                        "minimumSalary": getSalary(el["estimatedSalaryRange"])[0],
                        "maximumSalary": getSalary(el["estimatedSalaryRange"])[1],
                    }
                    for el in article.get("geographicJobDetails", [])
                ],
                "jobRoleKey": article["jobRoleKey"],
                "experienceLevel": article["experienceLevel"],
                "text": article["text"],
                "chunks": split_chunks,
            }
        )
        print(params[0]["jobProfile"]["prepareForRole"]["educationVsDegreeHeading"], "==============educationVsDegreeHeading=====================")
    logging.info(f"Number of text chunks: {len(all_chunks)}.")
    # Make a single request for embeddings
    embedded_documents = embeddings.embed_documents([el["text"] for el in all_chunks])
    # Assign embeddings to chunks in params using a dictionary
    chunk_embedding_map = {
        chunk["index"]: embedded_documents[i] for i, chunk in enumerate(all_chunks)
    }
    for param in params:
        param["chunks"] = [
            {**chunk, "embedding": chunk_embedding_map.get(chunk["index"], None)}
            for chunk in param["chunks"]
        ]

    return params


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
