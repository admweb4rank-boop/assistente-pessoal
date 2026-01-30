"""
TB Personal OS - Pattern Analysis Job
Job para executar análise de padrões periodicamente
"""

import structlog
from datetime import datetime
from supabase import create_client
from app.core.config import settings
from app.services.pattern_learning_service import pattern_learning_service

logger = structlog.get_logger(__name__)


class PatternAnalysisJob:
    """
    Job que executa análise de padrões de todos os usuários.
    Deve ser executado diariamente (de preferência à noite).
    """
    
    def __init__(self):
        self._supabase = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    async def run(self, user_id: str = None) -> dict:
        """
        Executa análise de padrões.
        
        Args:
            user_id: Se fornecido, analisa apenas este usuário.
                    Caso contrário, analisa todos os usuários ativos.
        """
        try:
            if user_id:
                # Analisar usuário específico
                result = await pattern_learning_service.run_full_analysis(user_id)
                return {
                    "success": True,
                    "users_analyzed": 1,
                    "result": result
                }
            
            # Buscar todos os usuários ativos
            users = self.supabase.table("users")\
                .select("id")\
                .execute()
            
            if not users.data:
                return {"success": True, "users_analyzed": 0, "message": "Nenhum usuário encontrado"}
            
            results = []
            for user in users.data:
                try:
                    result = await pattern_learning_service.run_full_analysis(user["id"])
                    results.append({
                        "user_id": user["id"],
                        "status": "success",
                        "successful_analyses": result.get("successful_analyses", 0)
                    })
                except Exception as e:
                    results.append({
                        "user_id": user["id"],
                        "status": "error",
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r["status"] == "success")
            
            logger.info(
                "pattern_analysis_job_completed",
                total_users=len(users.data),
                successful=successful
            )
            
            return {
                "success": True,
                "users_analyzed": len(users.data),
                "successful": successful,
                "results": results
            }
            
        except Exception as e:
            logger.error("pattern_analysis_job_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Instância global
pattern_analysis_job = PatternAnalysisJob()
