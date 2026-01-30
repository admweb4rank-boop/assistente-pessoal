"""
TB Personal OS - Google Drive Service
Integração com Google Drive API para gerenciamento de arquivos
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
import io
import mimetypes

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials

from supabase import Client, create_client
from app.core.config import settings
from app.services.google_auth_service import google_auth_service

logger = structlog.get_logger(__name__)


class DriveService:
    """
    Serviço de integração com Google Drive.
    Permite criar pastas, upload de arquivos e busca.
    """
    
    # Tipos MIME comuns
    FOLDER_MIME = 'application/vnd.google-apps.folder'
    DOCUMENT_MIME = 'application/vnd.google-apps.document'
    SPREADSHEET_MIME = 'application/vnd.google-apps.spreadsheet'
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
    
    @property
    def supabase(self) -> Client:
        """Lazy load Supabase client."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    async def _get_service(self, user_id: str):
        """Obtém serviço do Drive autenticado."""
        credentials = await google_auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError("Google não conectado. Use /connect para autorizar.")
        
        return build('drive', 'v3', credentials=credentials)
    
    # ==========================================
    # FOLDERS
    # ==========================================
    
    async def create_folder(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma pasta no Drive.
        
        Args:
            user_id: ID do usuário
            name: Nome da pasta
            parent_id: ID da pasta pai (opcional)
            
        Returns:
            Dados da pasta criada
        """
        try:
            service = await self._get_service(user_id)
            
            file_metadata = {
                'name': name,
                'mimeType': self.FOLDER_MIME
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink, createdTime'
            ).execute()
            
            logger.info(
                "folder_created",
                user_id=user_id,
                folder_id=folder['id'],
                name=name
            )
            
            return {
                'id': folder['id'],
                'name': folder['name'],
                'url': folder.get('webViewLink'),
                'created_at': folder.get('createdTime'),
                'type': 'folder'
            }
            
        except Exception as e:
            logger.error("create_folder_failed", user_id=user_id, name=name, error=str(e))
            raise
    
    async def create_project_folder(
        self,
        user_id: str,
        project_name: str,
        base_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria estrutura de pastas para um projeto.
        
        Cria:
        - Pasta principal do projeto
        - Subpastas: Documentos, Recursos, Entregas
        
        Args:
            user_id: ID do usuário
            project_name: Nome do projeto
            base_folder_id: Pasta base para projetos (opcional)
            
        Returns:
            Dados das pastas criadas
        """
        try:
            # Criar pasta principal
            main_folder = await self.create_folder(
                user_id=user_id,
                name=project_name,
                parent_id=base_folder_id
            )
            
            # Criar subpastas
            subfolders = ['Documentos', 'Recursos', 'Entregas']
            created_subfolders = []
            
            for subfolder_name in subfolders:
                subfolder = await self.create_folder(
                    user_id=user_id,
                    name=subfolder_name,
                    parent_id=main_folder['id']
                )
                created_subfolders.append(subfolder)
            
            logger.info(
                "project_folder_created",
                user_id=user_id,
                project=project_name,
                folder_id=main_folder['id']
            )
            
            return {
                'main_folder': main_folder,
                'subfolders': created_subfolders
            }
            
        except Exception as e:
            logger.error("create_project_folder_failed", user_id=user_id, project=project_name, error=str(e))
            raise
    
    async def get_or_create_folder(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém uma pasta existente ou cria se não existir.
        
        Args:
            user_id: ID do usuário
            name: Nome da pasta
            parent_id: ID da pasta pai
            
        Returns:
            Dados da pasta
        """
        try:
            # Buscar pasta existente
            query = f"name = '{name}' and mimeType = '{self.FOLDER_MIME}' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            service = await self._get_service(user_id)
            results = service.files().list(
                q=query,
                fields='files(id, name, webViewLink)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder = files[0]
                return {
                    'id': folder['id'],
                    'name': folder['name'],
                    'url': folder.get('webViewLink'),
                    'type': 'folder',
                    'existed': True
                }
            
            # Criar se não existir
            new_folder = await self.create_folder(user_id, name, parent_id)
            new_folder['existed'] = False
            return new_folder
            
        except Exception as e:
            logger.error("get_or_create_folder_failed", user_id=user_id, name=name, error=str(e))
            raise
    
    # ==========================================
    # FILES - LIST & SEARCH
    # ==========================================
    
    async def list_files(
        self,
        user_id: str,
        folder_id: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista arquivos no Drive.
        
        Args:
            user_id: ID do usuário
            folder_id: ID da pasta (None = root)
            page_size: Quantidade por página
            page_token: Token para paginação
            
        Returns:
            Lista de arquivos com paginação
        """
        try:
            service = await self._get_service(user_id)
            
            query = "trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = service.files().list(
                q=query,
                pageSize=page_size,
                pageToken=page_token,
                fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, iconLink)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = []
            for f in results.get('files', []):
                files.append({
                    'id': f['id'],
                    'name': f['name'],
                    'mime_type': f['mimeType'],
                    'size': f.get('size'),
                    'modified_at': f.get('modifiedTime'),
                    'url': f.get('webViewLink'),
                    'icon': f.get('iconLink'),
                    'is_folder': f['mimeType'] == self.FOLDER_MIME
                })
            
            return {
                'files': files,
                'next_page_token': results.get('nextPageToken')
            }
            
        except Exception as e:
            logger.error("list_files_failed", user_id=user_id, error=str(e))
            raise
    
    async def search_files(
        self,
        user_id: str,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Busca arquivos por nome.
        
        Args:
            user_id: ID do usuário
            query: Termo de busca
            max_results: Máximo de resultados
            
        Returns:
            Lista de arquivos encontrados
        """
        try:
            service = await self._get_service(user_id)
            
            # Buscar por nome
            search_query = f"name contains '{query}' and trashed = false"
            
            results = service.files().list(
                q=search_query,
                pageSize=max_results,
                fields='files(id, name, mimeType, size, modifiedTime, webViewLink, parents)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = []
            for f in results.get('files', []):
                files.append({
                    'id': f['id'],
                    'name': f['name'],
                    'mime_type': f['mimeType'],
                    'size': f.get('size'),
                    'modified_at': f.get('modifiedTime'),
                    'url': f.get('webViewLink'),
                    'parent_ids': f.get('parents', []),
                    'is_folder': f['mimeType'] == self.FOLDER_MIME
                })
            
            logger.info("search_files_completed", user_id=user_id, query=query, count=len(files))
            
            return files
            
        except Exception as e:
            logger.error("search_files_failed", user_id=user_id, query=query, error=str(e))
            raise
    
    async def get_recent_files(
        self,
        user_id: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Lista arquivos recentes (últimos modificados).
        
        Args:
            user_id: ID do usuário
            max_results: Máximo de resultados
            
        Returns:
            Lista de arquivos recentes
        """
        try:
            service = await self._get_service(user_id)
            
            results = service.files().list(
                pageSize=max_results,
                q="trashed = false and mimeType != 'application/vnd.google-apps.folder'",
                fields='files(id, name, mimeType, size, modifiedTime, webViewLink)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = []
            for f in results.get('files', []):
                files.append({
                    'id': f['id'],
                    'name': f['name'],
                    'mime_type': f['mimeType'],
                    'size': f.get('size'),
                    'modified_at': f.get('modifiedTime'),
                    'url': f.get('webViewLink')
                })
            
            return files
            
        except Exception as e:
            logger.error("get_recent_files_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # FILES - UPLOAD
    # ==========================================
    
    async def upload_file(
        self,
        user_id: str,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz upload de um arquivo para o Drive.
        
        Args:
            user_id: ID do usuário
            file_path: Caminho local do arquivo
            folder_id: ID da pasta destino
            file_name: Nome do arquivo (usa nome original se não especificado)
            
        Returns:
            Dados do arquivo criado
        """
        try:
            service = await self._get_service(user_id)
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Nome do arquivo
            if not file_name:
                file_name = file_path.split('/')[-1]
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, webViewLink, createdTime'
            ).execute()
            
            logger.info(
                "file_uploaded",
                user_id=user_id,
                file_id=file['id'],
                name=file['name']
            )
            
            return {
                'id': file['id'],
                'name': file['name'],
                'mime_type': file['mimeType'],
                'size': file.get('size'),
                'url': file.get('webViewLink'),
                'created_at': file.get('createdTime')
            }
            
        except Exception as e:
            logger.error("upload_file_failed", user_id=user_id, file_path=file_path, error=str(e))
            raise
    
    async def upload_content(
        self,
        user_id: str,
        content: bytes,
        file_name: str,
        mime_type: str,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz upload de conteúdo em memória para o Drive.
        
        Args:
            user_id: ID do usuário
            content: Bytes do conteúdo
            file_name: Nome do arquivo
            mime_type: Tipo MIME
            folder_id: ID da pasta destino
            
        Returns:
            Dados do arquivo criado
        """
        try:
            service = await self._get_service(user_id)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mime_type,
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, webViewLink, createdTime'
            ).execute()
            
            logger.info(
                "content_uploaded",
                user_id=user_id,
                file_id=file['id'],
                name=file['name']
            )
            
            return {
                'id': file['id'],
                'name': file['name'],
                'mime_type': file['mimeType'],
                'size': file.get('size'),
                'url': file.get('webViewLink'),
                'created_at': file.get('createdTime')
            }
            
        except Exception as e:
            logger.error("upload_content_failed", user_id=user_id, file_name=file_name, error=str(e))
            raise
    
    # ==========================================
    # FILES - DELETE & MOVE
    # ==========================================
    
    async def delete_file(
        self,
        user_id: str,
        file_id: str
    ) -> bool:
        """
        Move arquivo para a lixeira.
        
        Args:
            user_id: ID do usuário
            file_id: ID do arquivo
            
        Returns:
            True se sucesso
        """
        try:
            service = await self._get_service(user_id)
            
            service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()
            
            logger.info("file_deleted", user_id=user_id, file_id=file_id)
            return True
            
        except Exception as e:
            logger.error("delete_file_failed", user_id=user_id, file_id=file_id, error=str(e))
            raise
    
    async def move_file(
        self,
        user_id: str,
        file_id: str,
        new_parent_id: str
    ) -> Dict[str, Any]:
        """
        Move arquivo para outra pasta.
        
        Args:
            user_id: ID do usuário
            file_id: ID do arquivo
            new_parent_id: ID da nova pasta pai
            
        Returns:
            Dados do arquivo atualizado
        """
        try:
            service = await self._get_service(user_id)
            
            # Obter pais atuais
            file = service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents', []))
            
            # Mover
            updated_file = service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=previous_parents,
                fields='id, name, parents, webViewLink'
            ).execute()
            
            logger.info(
                "file_moved",
                user_id=user_id,
                file_id=file_id,
                new_parent=new_parent_id
            )
            
            return {
                'id': updated_file['id'],
                'name': updated_file['name'],
                'parents': updated_file.get('parents', []),
                'url': updated_file.get('webViewLink')
            }
            
        except Exception as e:
            logger.error("move_file_failed", user_id=user_id, file_id=file_id, error=str(e))
            raise
    
    # ==========================================
    # FILE DETAILS
    # ==========================================
    
    async def get_file(
        self,
        user_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """
        Obtém detalhes de um arquivo.
        
        Args:
            user_id: ID do usuário
            file_id: ID do arquivo
            
        Returns:
            Dados completos do arquivo
        """
        try:
            service = await self._get_service(user_id)
            
            file = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, createdTime, webViewLink, parents, description'
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'mime_type': file['mimeType'],
                'size': file.get('size'),
                'modified_at': file.get('modifiedTime'),
                'created_at': file.get('createdTime'),
                'url': file.get('webViewLink'),
                'parents': file.get('parents', []),
                'description': file.get('description'),
                'is_folder': file['mimeType'] == self.FOLDER_MIME
            }
            
        except Exception as e:
            logger.error("get_file_failed", user_id=user_id, file_id=file_id, error=str(e))
            raise
    
    # ==========================================
    # STORAGE INFO
    # ==========================================
    
    async def get_storage_quota(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém informações de quota de armazenamento.
        
        Returns:
            Uso e limite de armazenamento
        """
        try:
            service = await self._get_service(user_id)
            
            about = service.about().get(
                fields='storageQuota'
            ).execute()
            
            quota = about.get('storageQuota', {})
            
            return {
                'limit': int(quota.get('limit', 0)),
                'usage': int(quota.get('usage', 0)),
                'usage_in_drive': int(quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(quota.get('usageInDriveTrash', 0)),
                'limit_gb': round(int(quota.get('limit', 0)) / (1024**3), 2),
                'usage_gb': round(int(quota.get('usage', 0)) / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error("get_storage_quota_failed", user_id=user_id, error=str(e))
            raise


# Singleton
drive_service = DriveService()
