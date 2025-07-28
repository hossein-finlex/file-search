import os
import numpy as np
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
from PIL import Image
import io
import base64
import logging
from ..config import get_config, VectorConfig

# Add PDF text extraction support
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pypdf not available. PDF text extraction will be limited.")

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings from different file types"""
    
    def __init__(self, model_name: Optional[str] = None, config: Optional[VectorConfig] = None):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the sentence transformer model to use (overrides config)
            config: Optional VectorConfig instance. If None, uses global config.
        """
        if config is None:
            config = get_config().vector
        
        self.config = config
        self.model_name = model_name or str(config.embedding_model.value)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text content
        
        Args:
            text: Text content to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            # Clean and prepare text
            text = self._preprocess_text(text)
            
            # Generate embedding
            embedding = self.model.encode(text)
            
            # Convert to list of floats
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            raise
    
    def generate_file_embedding(self, file_path: str, content_type: Optional[str] = None) -> List[float]:
        """
        Generate embedding for a file based on its content type
        
        Args:
            file_path: Path to the file
            content_type: MIME type of the file (optional, will be inferred if not provided)
            
        Returns:
            List of float values representing the embedding
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine content type if not provided
        if content_type is None:
            content_type = self._infer_content_type(file_path)
        
        try:
            if content_type.startswith('text/'):
                return self._embed_text_file(file_path)
            elif content_type.startswith('image/'):
                return self._embed_image_file(file_path)
            elif content_type == 'application/pdf':
                return self._embed_pdf_file(file_path)
            else:
                # For other file types, try to extract text content
                return self._embed_generic_file(file_path)
        
        except Exception as e:
            logger.error(f"Error generating file embedding for {file_path}: {e}")
            raise
    

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long (most models have token limits)
        max_length = self.config.max_text_length
        if len(text) > max_length:
            if self.config.text_truncation_strategy == "start":
                text = text[-max_length:]
            elif self.config.text_truncation_strategy == "middle":
                half = max_length // 2
                text = text[:half] + text[-half:]
            else:  # "end" (default)
                text = text[:max_length]
        
        return text
    
    def _infer_content_type(self, file_path: str) -> str:
        """Infer content type from file extension"""
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            # Default to text for unknown types
            return 'text/plain'
        return content_type
    
    def _embed_text_file(self, file_path: str) -> List[float]:
        """Generate embedding for text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.generate_text_embedding(text)
        
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            return self.generate_text_embedding(text)
    
    def _embed_image_file(self, file_path: str) -> List[float]:
        """Generate embedding for image files"""
        try:
            # Load image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image for processing
            image = image.resize((self.config.image_resize_width, self.config.image_resize_height))
            
            # Convert to base64 string for text-based embedding
            # This is a simple approach - in production, you might want to use
            # a dedicated image embedding model
            buffer = io.BytesIO()
            image.save(buffer, format=self.config.image_format)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            # Use the base64 string as text for embedding
            return self.generate_text_embedding(f"image: {img_str}")
        
        except Exception as e:
            logger.error(f"Error embedding image file {file_path}: {e}")
            raise

    def _embed_pdf_file(self, file_path: str) -> List[float]:
        """Generate embedding for PDF files by extracting text content"""
        try:
            if not PDF_SUPPORT:
                logger.warning(f"PDF text extraction not available for {file_path}, falling back to generic method")
                return self._embed_generic_file(file_path)
            
            # Extract text from PDF
            text_content = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text_content += f"\n--- Page {page_num + 1} ---\n"
                            text_content += page_text
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1} of {file_path}: {e}")
                        continue
            
            # If no text extracted, fall back to metadata
            if not text_content.strip():
                logger.warning(f"No text content extracted from PDF {file_path}, using file metadata")
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                text_content = f"PDF document: {file_name}, size: {file_size} bytes"
            else:
                logger.info(f"Extracted {len(text_content)} characters from PDF {file_path}")
            
            # Generate embedding from extracted text
            return self.generate_text_embedding(text_content)
        
        except Exception as e:
            logger.error(f"Error embedding PDF file {file_path}: {e}")
            # Fall back to generic method on error
            return self._embed_generic_file(file_path)
    
    def _embed_generic_file(self, file_path: str) -> List[float]:
        """Generate embedding for generic files"""
        try:
            # Try to read as text first
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.generate_text_embedding(text)
        
        except (UnicodeDecodeError, UnicodeError):
            # If text reading fails, create a generic description
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            text = f"file: {file_name}, size: {file_size} bytes"
            
            return self.generate_text_embedding(text)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embeddings
        """
        try:
            # Preprocess texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Generate embeddings in batch
            embeddings = self.model.encode(processed_texts)
            
            # Convert to list of lists
            return [emb.tolist() for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def similarity_score(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            raise 