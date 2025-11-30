
# pipeline_llama.py

import re

import requests

from SPARQLWrapper import SPARQLWrapper, JSON

import nltk

from nltk.corpus import stopwords



# ---------- CONFIG ----------

FUSEKI_URL = "https://fuseki.sobaz.uk/university_faq/query"

LLAMA_API_URL = "http://llama.sobaz.uk/v1/completions"



# ---------- NLTK STOPWORDS SETUP ----------

nltk.download("stopwords")

STOPWORDS = set(stopwords.words("english"))



# ---------- FUNCTIONS ----------



def extract_university(user_query):

    universities = ["Air University", "FAST", "NUST", "National University"]

    for uni in universities:

        if uni.lower() in user_query.lower():

            return uni

    return None



def call_llama(prompt):

    """

    Call LLaMA API without token limit.

    """

    payload = {

        "model": "llama3.1",

        "prompt": prompt

    }

    response = requests.post(LLAMA_API_URL, json=payload)

    response.raise_for_status()

    return response.json()["choices"][0]["text"]



# ---------- KEYWORD EXTRACTION & SPARQL GENERATION ----------



def extract_keywords(user_query):

    """

    Tokenize, lowercase, and remove NLTK stopwords.

    """

    words = re.findall(r"\w+", user_query.lower())

    keywords = [w for w in words if w not in STOPWORDS]

    return keywords



def generate_sparql(user_query, university=None):

    """

    Generate SPARQL query using keywords from user query.

    If keywords are empty, no FILTER is added (returns all FAQs).

    """

    keywords = extract_keywords(user_query)

    

    sparql = f"""

PREFIX : <http://example.org/unifaq#>

SELECT ?question ?answer

WHERE {{

    ?faq a :FAQ ;

         :hasQuestion ?q ;

         :hasAnswer ?a .

    ?q :text ?question .

    ?a :text ?answer .

"""

    if keywords:

        filter_clauses = " || ".join([f'CONTAINS(LCASE(?question), "{k}")' for k in keywords])

        sparql += f"    FILTER ({filter_clauses})\n"



    if university:

        sparql += f'    ?faq :fromUniversity :{university.replace(" ","")} .\n'

    

    sparql += "}"

    return sparql.strip()



# ---------- RUN SPARQL ON FUSEKI ----------



def run_sparql(query):

    sparql = SPARQLWrapper(FUSEKI_URL)

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()

    faqs = []

    for result in results["results"]["bindings"]:

        faqs.append({

            "question": result["question"]["value"],

            "answer": result["answer"]["value"]

        })

    return faqs



# ---------- PROCESS RESULTS WITH LLaMA ----------



def llama_process_results(user_query, faqs):

    if not faqs:

        return "Sorry, I could not find any relevant FAQ."



    faqs_text = ""

    for idx, faq in enumerate(faqs, start=1):

        faqs_text += f"{idx}. Question: \"{faq['question']}\"\n   Answer: \"{faq['answer']}\"\n"



    prompt = f"""

You are an assistant that answers questions based on a university FAQ dataset.

The following FAQs were returned by a SPARQL query for the user's question:



{faqs_text}



User's question: "{user_query}"



Task:

- Pick the most relevant information.

- Summarize and rewrite it in clear, concise, natural language.

- Provide only the answer, do not include raw questions from dataset.
- Do not mention that you are using a dataset or FAQ and do not reference the source.

- Keep it accurate according to the FAQ.

- if you think the retrieved FAQ have no link to the question (like for example if question says what is attendance policy and you get faq of something else, just ignore it), reply with 'Sorry, I could not find any relevant FAQ.'"""

    answer = call_llama(prompt)

    return answer



# ---------- MAIN CHATBOT FUNCTION ----------



def answer_question(user_query):

    university = extract_university(user_query)

    sparql_query = generate_sparql(user_query, university)



    print("DEBUG: Generated SPARQL query:\n", sparql_query)



    results = run_sparql(sparql_query)



    # ---- DEBUG: Show retrieved FAQs ---
    print("----------------------------------------\n")



    final_answer = llama_process_results(user_query, results)

    return final_answer





# -------------------- TEST --------------------

# -------------------- CHAT LOOP --------------------

