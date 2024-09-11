import json  

def process_json_element(item):  
    result = []  

    # for item in json_data:

    job_role = item.get('jobRole', 'N/A')
    sector = item.get('sector', 'N/A')
    sub_sector = item.get('subSector', 'N/A')
    college_category = item.get('collegeCategory', 'N/A')
    job_location = item.get('jobLocation', 'N/A')
    job_profile = item.get('jobProfile', {})
    general_description = job_profile.get('generalDescription', {}).get('text', 'N/A')
    day_in_the_life = job_profile.get('dayInTheLife', {}).get('text', 'N/A')

    reasons_liked = [reason.get('reason', 'N/A') for reason in job_profile.get('reasonsLiked', [])]
    reasons_disliked = [reason.get('reason', 'N/A') for reason in job_profile.get('reasonsDisliked', [])]
    
    prepare_for_role = item.get('prepareForRole', {})
    aptitude_ratings = item.get('aptitudeRatings', [])
    interest_ratings = item.get('interestRatings', [])
    value_ratings = item.get('valueRatings', [])

    career_pathways = item.get('careerPathways', [])
    wellknown_employers = item.get('employers', {}).get('wellKnownEmployers', 'N/A')
    employer_profiles = item.get('employers', {}).get('employerProfiles', 'N/A')
    geographic_JobDetails = item.get('geographicJobDetails', [])

    result.append(f"Job Role: {job_role}")
    result.append(f"Sector: {sector}")
    result.append(f"Sub-Sector: {sub_sector}")
    result.append(f"College Category: {college_category}")
    result.append("\nJob Profile:")
    result.append(f"- General Description: {general_description}")
    result.append(f"- Day in the Life: {day_in_the_life}")
    result.append("- Reasons Liked:")
    for reason in reasons_liked:
        result.append(f"  * {reason}")
    result.append("- Reasons Disliked:")
    for reason in reasons_disliked:
        result.append(f"  * {reason}")
    for key, value in prepare_for_role.items():
        result.append(key)
        result.append(value)

    result.append("Aptitude Ratings:")
    for rating in aptitude_ratings:
        attribute = rating.get('attribute', 'N/A')
        score = rating.get('score', 'N/A')
        reason = rating.get('reason', 'N/A')
        result.append(f"- {attribute}, score: {score}")
        result.append(f"  Reason: {reason}")

    result.append("Interest Ratings:")
    for rating in interest_ratings:
        attribute = rating.get('attribute', 'N/A')
        score = rating.get('score', 'N/A')
        reason = rating.get('reason', 'N/A')
        result.append(f"- {attribute}, score: {score}")
        result.append(f"  Reason: {reason}")

    result.append("Value Ratings:")
    for rating in value_ratings:
        attribute = rating.get('attribute', 'N/A')
        score = rating.get('score', 'N/A')
        reason = rating.get('reason', 'N/A')
        result.append(f"- {attribute}, score: {score}")
        result.append(f"  Reason: {reason}")
    
    result.append("Career Pathways")
    for index, pathway in enumerate(career_pathways, start=1):  
        pathway_title = pathway.get('pathwayTitle', 'N/A')
        description = pathway.get('description', 'N/A')

        result.append(f"- Pathway {index}: {pathway_title}")
        result.append(f"  Description: {description}")
        
        for job_role in pathway.get('jobRoles', []):
            title = job_role.get('title', 'N/A')
            years = job_role.get('years', 'N/A')
            result.append(f"  * {title}: {years} years")
    
    result.append("Well Known Employers")
    for employer in wellknown_employers:
        name = employer.get('name', 'N/A')
        description = employer.get('description', 'N/A')
        website = employer.get('website', 'N/A')
        result.append(f"- {name}: {website}")
        result.append(f"  description: {description}")
    
    result.append("Employer Profiles")
    for profiles in employer_profiles:
        geographic = profiles.get('geographicOption', 'N/A')
        profile = profiles.get('profiles', 'N/A')
        result.append(f"- Location: {geographic}")
        result.append(f"  profile: {profile}")

    result.append("Geographic Job Details")
    for job in geographic_JobDetails:
        geographic = job.get('geographicOption', 'N/A')
        availability = job.get('jobAvailability', 'N/A')
        salary = job.get('estimatedSalaryRange', 'N/A')
        result.append(f"- Location: {geographic}, availability: {availability}")
        result.append(f"  Salary Range: {salary}")

    return "\n".join(result)

# Read JSON data from a file
# with open('TransformerService.job_profiles_26Aug.json', 'r', encoding='utf-8') as json_file:
#     data = json.load(json_file)

# with open('output.txt', 'w', encoding='utf-8') as file:
#     for element in data:
#         description = process_json_element(element)
#         print(description)
#         file.write(description)
    
# text_output = process_json_element(data)

# print(text_output)
# with open('output.txt', 'w') as file:
#     file.write(text_output)
# with open('output.txt', 'w', encoding='utf-8') as output_file:  
#     output_file.write(text_output) 