# src/graph/vector_index.py
import logging
from openai import OpenAI
from src.graph.neo4j_client import Neo4jClient
from src.config.settings import settings

logger = logging.getLogger(__name__)

class VectorIndexManager:
    def __init__(self):
        # Menggunakan settings terpusat untuk API key
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.db = Neo4jClient()
        # Menggunakan model termurah dan paling efisien
        self.embedding_model = "text-embedding-3-small" 

    def generate_embedding(self, text: str) -> list[float]:
        """Menghasilkan vector embedding dari teks menggunakan OpenAI."""
        try:
            if not text or not text.strip():
                text = "No description available"
                
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Gagal menghasilkan embedding: {e}")
            raise e

    def initialize(self):
        """
        Membuat Vector Index di Neo4j jika belum ada, 
        dan mengisi embedding untuk node Definition yang belum memilikinya.
        """
        print("   Mempersiapkan Vector Index 'definition_description_vector'...")
        
        # 1. Buat Vector Index di Neo4j (Dimensi 1536 standar OpenAI)
        try:
            self.db.execute_query("""
            CREATE VECTOR INDEX definition_description_vector IF NOT EXISTS
            FOR (d:Definition) ON (d.embedding)
            OPTIONS {indexConfig: {
             `vector.dimensions`: 1536,
             `vector.similarity_function`: 'cosine'
            }}
            """)
        except Exception as e:
            logger.warning(f"Catatan index: {e}")

        # 2. Mulai proses populasi embedding (Pass 1.5)
        self._populate_embeddings()

    def _populate_embeddings(self):
        """Menarik deskripsi node dan menyimpannya sebagai vector."""
        # Cari node Definition yang belum punya embedding tapi punya deskripsi
        query_get_nodes = """
        MATCH (d:Definition)
        WHERE d.embedding IS NULL AND d.description IS NOT NULL
        RETURN d.id AS id, d.description AS description
        """
        nodes = self.db.execute_query(query_get_nodes)
        
        if not nodes:
            print("   ✓ Semua node sudah memiliki vector embedding.")
            return

        print(f"   ⏳ Menghasilkan vector embeddings untuk {len(nodes)} node (API Call)...")
        
        updated_count = 0
        for node in nodes:
            try:
                node_id = node['id']
                desc = node['description']
                
                # Request ke OpenAI
                vector = self.generate_embedding(desc)
                
                # Simpan vector kembali ke node di Neo4j
                self.db.execute_query("""
                MATCH (d:Definition {id: $id})
                SET d.embedding = $vector
                """, {"id": node_id, "vector": vector})
                
                updated_count += 1
                if updated_count % 100 == 0:
                    print(f"      ... {updated_count}/{len(nodes)} node selesai diproses")
                    
            except Exception as e:
                logger.error(f"Gagal memproses node {node.get('id')}: {e}")
                
        print(f"   ✓ Selesai menambahkan embedding untuk {updated_count} node.")