from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from db import database
from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    
    model_path = "cc.pt.300.vec.gz"
    app.state.model = KeyedVectors.load_word2vec_format(model_path)
    yield
    await database.disconnect()

app = FastAPI(
    title="Recomendation API Gateway", 
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/{id}")
async def root(id: str, request: Request):
    query = '''
    SELECT DISTINCT p.*, t.id as tag_id, t.name as tag_name 
    FROM "Product" p
    JOIN "Bid" b ON b."productId" = p.id
    LEFT JOIN "_ProductToTag" pt ON pt."A" = p.id
    LEFT JOIN "Tag" t ON t.id = pt."B"
    WHERE b."userId" = :id
    '''
    results = await database.fetch_all(query=query, values={"id": id})
    
    tags_where_user_bid = []
    s = set()
    for row in results:
        
        s.add(row.id)
        if row.tag_id not in tags_where_user_bid:
            tags_where_user_bid.append({
                "id": row.tag_id,
                "name": row.tag_name
            })
            
    all_tags_query = '''
    SELECT DISTINCT t.id as tag_id, t.name as tag_name
    FROM "Tag" t
    '''
    all_tags = await database.fetch_all(query=all_tags_query)
    all_tags = [{"id": row.tag_id, "name": row.tag_name} for row in all_tags]
    
    model = request.app.state.model
    
    recommendations = []
    similarity_threshold = 0.2 

    for candidate_tag in all_tags:
        best_similarity = 0
        
        if candidate_tag["name"] not in model:
            continue
            
        candidate_vector = model[candidate_tag["name"]]
        
        for user_tag in tags_where_user_bid:
            if user_tag["name"] not in model:
                continue
                
            user_tag_vector = model[user_tag["name"]]
            similarity = cosine_similarity(
                [candidate_vector], 
                [user_tag_vector]
            )[0][0]
            
            best_similarity = max(best_similarity, similarity)
        
        if best_similarity >= similarity_threshold:
            recommendations.append({
                "id": candidate_tag["id"],
                "name": candidate_tag["name"],
                "similarity": float(best_similarity)
            })
    
    recommendations.sort(key=lambda x: x["similarity"], reverse=True)
    
    top_recommendations = recommendations[:30]
            
    return {
        "user_tags": tags_where_user_bid,
        "recommendations": top_recommendations
    }

