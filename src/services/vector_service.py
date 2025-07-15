import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
from src.models.schemas import JobPosition, ServiceHealth

logger = logging.getLogger(__name__)

class VectorService:
    """Service for handling vector database operations with Pinecone"""
    
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "job-embeddings")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.pinecone_client = None
        self.pinecone_index = None
        self.openai_client = None
        
    async def initialize(self):
        """Initialize Pinecone and OpenAI clients"""
        try:
            if not self.pinecone_api_key:
                raise ValueError("Pinecone API key must be set")
            
            if not self.openai_api_key:
                raise ValueError("OpenAI API key must be set")
            
            # Initialize Pinecone client
            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            
            # Create index if it doesn't exist
            existing_indexes = self.pinecone_client.list_indexes()
            if self.index_name not in existing_indexes.names():
                # Create index with default settings
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI text-embedding-ada-002 dimension
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            # Get the index
            self.pinecone_index = self.pinecone_client.Index(self.index_name)
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check vector database health"""
        try:
            if not self.pinecone_index:
                return ServiceHealth(status="unhealthy", message="Index not initialized")
            
            # Test connection by getting index stats
            stats = self.pinecone_index.describe_index_stats()
            return ServiceHealth(status="healthy", message=f"Index stats: {stats}")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def store_job_embeddings(self, jobs: List[JobPosition]):
        """Store job embeddings in Pinecone"""
        try:
            if not self.pinecone_index:
                raise ValueError("Pinecone index not initialized")
            
            vectors = []
            for job in jobs:
                # Create text representation of job
                job_text = f"Title: {job.title} Company: {job.company} Location: {job.location} Description: {job.description_snippet or ''}"
                
                # Generate embedding
                embedding = await self.generate_embedding(job_text)
                
                # Create vector record
                vector = {
                    "id": job.id or f"job_{hash(job.url)}",
                    "values": embedding,
                    "metadata": {
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.url,
                        "job_board": job.job_board,
                        "description": job.description_snippet or ""
                    }
                }
                vectors.append(vector)
            
            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.pinecone_index.upsert(vectors=batch)
            
            logger.info(f"Stored {len(vectors)} job embeddings in Pinecone")
            
        except Exception as e:
            logger.error(f"Error storing job embeddings: {e}")
            raise
    
    async def find_similar_jobs(self, job_description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar jobs using vector similarity search"""
        try:
            if not self.pinecone_index:
                raise ValueError("Pinecone index not initialized")
            
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(job_description)
            
            # Search for similar vectors
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True
            )
            
            # Format results
            similar_jobs = []
            for match in results.matches:
                similar_jobs.append({
                    "id": match.id,
                    "score": match.score,
                    "title": match.metadata.get("title"),
                    "company": match.metadata.get("company"),
                    "location": match.metadata.get("location"),
                    "url": match.metadata.get("url"),
                    "job_board": match.metadata.get("job_board"),
                    "description": match.metadata.get("description")
                })
            
            return similar_jobs
            
        except Exception as e:
            logger.error(f"Error finding similar jobs: {e}")
            raise
    
    async def delete_job_embedding(self, job_id: str):
        """Delete a job embedding from Pinecone"""
        try:
            if not self.pinecone_index:
                raise ValueError("Pinecone index not initialized")
            
            self.pinecone_index.delete(ids=[job_id])
            logger.info(f"Deleted job embedding: {job_id}")
            
        except Exception as e:
            logger.error(f"Error deleting job embedding: {e}")
            raise
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            if not self.pinecone_index:
                raise ValueError("Pinecone index not initialized")
            
            stats = self.pinecone_index.describe_index_stats()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise
    
    async def find_job_matches_for_user(self, user_profile: Dict[str, Any], job_description: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find job matches for a user based on their profile"""
        try:
            if not self.pinecone_index:
                raise ValueError("Pinecone index not initialized")
            
            # Create user profile text for embedding
            profile_text = self._create_profile_text(user_profile)
            
            # If job description is provided, combine with profile
            if job_description:
                query_text = f"{profile_text} Job Description: {job_description}"
            else:
                query_text = profile_text
            
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(query_text)
            
            # Search for similar vectors
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True
            )
            
            # Format results
            job_matches = []
            for match in results.matches:
                job_matches.append({
                    "id": match.id,
                    "similarity": match.score,
                    "title": match.metadata.get("title", ""),
                    "company": match.metadata.get("company", ""),
                    "location": match.metadata.get("location", ""),
                    "url": match.metadata.get("url", ""),
                    "job_board": match.metadata.get("job_board", ""),
                    "description": match.metadata.get("description", "")
                })
            
            return job_matches
            
        except Exception as e:
            logger.error(f"Error finding job matches for user: {e}")
            # Return empty list instead of raising to prevent API errors
            return []
    
    def _create_profile_text(self, user_profile: Dict[str, Any]) -> str:
        """Create text representation of user profile for embedding"""
        profile_parts = []
        
        # Basic info
        if user_profile.get('name'):
            profile_parts.append(f"Name: {user_profile['name']}")
        
        if user_profile.get('title'):
            profile_parts.append(f"Title: {user_profile['title']}")
        
        # Skills
        if user_profile.get('skills'):
            skills_text = ", ".join(user_profile['skills'])
            profile_parts.append(f"Skills: {skills_text}")
        
        # Experience
        if user_profile.get('experience'):
            for exp in user_profile['experience']:
                exp_text = f"{exp.get('job_title', '')} at {exp.get('company_name', '')}"
                if exp.get('description'):
                    exp_text += f" - {exp['description']}"
                profile_parts.append(f"Experience: {exp_text}")
        
        # Education
        if user_profile.get('education'):
            for edu in user_profile['education']:
                edu_text = f"{edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('institution_name', '')}"
                profile_parts.append(f"Education: {edu_text}")
        
        return " ".join(profile_parts)
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        try:
            # Generate embeddings for both texts
            embedding1 = await self.generate_embedding(text1)
            embedding2 = await self.generate_embedding(text2)
            
            # Calculate cosine similarity
            import numpy as np
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0 