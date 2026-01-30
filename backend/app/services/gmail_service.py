"""
TB Personal OS - Gmail Service
Integração com Gmail API para leitura e envio de emails
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from supabase import Client, create_client
from app.core.config import settings
from app.services.google_auth_service import google_auth_service

logger = structlog.get_logger(__name__)


class GmailService:
    """
    Serviço de integração com Gmail.
    Permite ler emails, criar rascunhos e enviar mensagens.
    """
    
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
        """Obtém serviço do Gmail autenticado."""
        credentials = await google_auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError("Google não conectado. Use /connect para autorizar.")
        
        return build('gmail', 'v1', credentials=credentials)
    
    # ==========================================
    # MESSAGES - READ
    # ==========================================
    
    async def get_unread_emails(
        self,
        user_id: str,
        max_results: int = 10,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Lista emails não lidos das últimas X horas.
        
        Args:
            user_id: ID do usuário
            max_results: Máximo de emails a retornar
            hours_back: Buscar emails das últimas X horas
            
        Returns:
            Lista de emails com metadados
        """
        try:
            service = await self._get_service(user_id)
            
            # Calcular data limite
            tz = pytz.timezone(settings.OWNER_TIMEZONE)
            since_date = datetime.now(tz) - timedelta(hours=hours_back)
            after_timestamp = int(since_date.timestamp())
            
            # Query: não lidos, das últimas X horas, inbox
            query = f"is:unread in:inbox after:{after_timestamp}"
            
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_data = await self._get_email_details(service, msg['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info(
                "unread_emails_fetched",
                user_id=user_id,
                count=len(emails),
                hours_back=hours_back
            )
            
            return emails
            
        except Exception as e:
            logger.error("get_unread_emails_failed", user_id=user_id, error=str(e))
            raise
    
    async def _get_email_details(
        self,
        service,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de um email específico."""
        try:
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            
            return {
                'id': message_id,
                'thread_id': msg.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', '(sem assunto)'),
                'date': headers.get('Date', ''),
                'snippet': msg.get('snippet', ''),
                'labels': msg.get('labelIds', []),
                'is_unread': 'UNREAD' in msg.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error("get_email_details_failed", message_id=message_id, error=str(e))
            return None
    
    async def get_email_full(
        self,
        user_id: str,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Obtém email completo com corpo da mensagem.
        
        Args:
            user_id: ID do usuário
            message_id: ID do email
            
        Returns:
            Email com corpo completo
        """
        try:
            service = await self._get_service(user_id)
            
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            
            # Extrair corpo
            body = self._extract_body(msg.get('payload', {}))
            
            return {
                'id': message_id,
                'thread_id': msg.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', '(sem assunto)'),
                'date': headers.get('Date', ''),
                'body': body,
                'labels': msg.get('labelIds', []),
                'is_unread': 'UNREAD' in msg.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error("get_email_full_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    def _extract_body(self, payload: Dict) -> str:
        """Extrai o corpo do email do payload."""
        body = ""
        
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part.get('mimeType') == 'text/html' and not body:
                    if part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    # Recursivo para multipart
                    body = self._extract_body(part)
                    if body:
                        break
        
        return body
    
    async def get_thread(
        self,
        user_id: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Obtém uma thread completa de emails.
        
        Args:
            user_id: ID do usuário
            thread_id: ID da thread
            
        Returns:
            Thread com todas as mensagens
        """
        try:
            service = await self._get_service(user_id)
            
            thread = service.users().threads().get(
                userId='me',
                id=thread_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            messages = []
            for msg in thread.get('messages', []):
                headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
                messages.append({
                    'id': msg['id'],
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': msg.get('snippet', '')
                })
            
            return {
                'thread_id': thread_id,
                'messages': messages,
                'message_count': len(messages)
            }
            
        except Exception as e:
            logger.error("get_thread_failed", user_id=user_id, thread_id=thread_id, error=str(e))
            raise
    
    # ==========================================
    # MESSAGES - ACTIONS
    # ==========================================
    
    async def mark_as_read(
        self,
        user_id: str,
        message_id: str
    ) -> bool:
        """
        Marca um email como lido.
        
        Args:
            user_id: ID do usuário
            message_id: ID do email
            
        Returns:
            True se sucesso
        """
        try:
            service = await self._get_service(user_id)
            
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info("email_marked_read", user_id=user_id, message_id=message_id)
            return True
            
        except Exception as e:
            logger.error("mark_as_read_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    async def mark_as_unread(
        self,
        user_id: str,
        message_id: str
    ) -> bool:
        """Marca um email como não lido."""
        try:
            service = await self._get_service(user_id)
            
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info("email_marked_unread", user_id=user_id, message_id=message_id)
            return True
            
        except Exception as e:
            logger.error("mark_as_unread_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    async def archive_email(
        self,
        user_id: str,
        message_id: str
    ) -> bool:
        """
        Arquiva um email (remove do inbox).
        
        Args:
            user_id: ID do usuário
            message_id: ID do email
            
        Returns:
            True se sucesso
        """
        try:
            service = await self._get_service(user_id)
            
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info("email_archived", user_id=user_id, message_id=message_id)
            return True
            
        except Exception as e:
            logger.error("archive_email_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    # ==========================================
    # DRAFTS & SEND
    # ==========================================
    
    async def create_draft(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um rascunho de email.
        
        Args:
            user_id: ID do usuário
            to: Destinatário
            subject: Assunto
            body: Corpo do email
            reply_to_message_id: ID do email sendo respondido (opcional)
            thread_id: ID da thread para resposta (opcional)
            
        Returns:
            Dados do rascunho criado
        """
        try:
            service = await self._get_service(user_id)
            
            # Criar mensagem
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            # Codificar
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            draft_body = {'message': {'raw': raw}}
            
            # Se for resposta, adicionar thread_id
            if thread_id:
                draft_body['message']['threadId'] = thread_id
            
            draft = service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            logger.info(
                "draft_created",
                user_id=user_id,
                draft_id=draft['id'],
                to=to,
                subject=subject
            )
            
            return {
                'draft_id': draft['id'],
                'message_id': draft['message']['id'],
                'to': to,
                'subject': subject,
                'status': 'draft'
            }
            
        except Exception as e:
            logger.error("create_draft_failed", user_id=user_id, error=str(e))
            raise
    
    async def create_reply_draft(
        self,
        user_id: str,
        message_id: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Cria rascunho de resposta a um email.
        
        Args:
            user_id: ID do usuário
            message_id: ID do email original
            body: Corpo da resposta
            
        Returns:
            Dados do rascunho criado
        """
        try:
            # Buscar email original
            original = await self.get_email_full(user_id, message_id)
            
            # Extrair remetente para responder
            from_address = original['from']
            # Limpar formato "Nome <email@domain.com>"
            if '<' in from_address:
                from_address = from_address.split('<')[1].rstrip('>')
            
            # Montar assunto com Re:
            subject = original['subject']
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"
            
            return await self.create_draft(
                user_id=user_id,
                to=from_address,
                subject=subject,
                body=body,
                reply_to_message_id=message_id,
                thread_id=original['thread_id']
            )
            
        except Exception as e:
            logger.error("create_reply_draft_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    async def send_draft(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict[str, Any]:
        """
        Envia um rascunho.
        
        Args:
            user_id: ID do usuário
            draft_id: ID do rascunho
            
        Returns:
            Dados da mensagem enviada
        """
        try:
            service = await self._get_service(user_id)
            
            result = service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            
            logger.info("draft_sent", user_id=user_id, draft_id=draft_id, message_id=result['id'])
            
            return {
                'message_id': result['id'],
                'thread_id': result.get('threadId'),
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error("send_draft_failed", user_id=user_id, draft_id=draft_id, error=str(e))
            raise
    
    async def send_email(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Envia email diretamente (sem criar rascunho).
        
        Args:
            user_id: ID do usuário
            to: Destinatário
            subject: Assunto
            body: Corpo do email
            
        Returns:
            Dados da mensagem enviada
        """
        try:
            service = await self._get_service(user_id)
            
            # Criar mensagem
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            # Codificar
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(
                "email_sent",
                user_id=user_id,
                message_id=result['id'],
                to=to,
                subject=subject
            )
            
            return {
                'message_id': result['id'],
                'thread_id': result.get('threadId'),
                'to': to,
                'subject': subject,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error("send_email_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # LABELS
    # ==========================================
    
    async def list_labels(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista todas as labels/pastas do Gmail."""
        try:
            service = await self._get_service(user_id)
            
            results = service.users().labels().list(userId='me').execute()
            
            labels = []
            for label in results.get('labels', []):
                labels.append({
                    'id': label['id'],
                    'name': label['name'],
                    'type': label.get('type', 'user')
                })
            
            return labels
            
        except Exception as e:
            logger.error("list_labels_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # SEARCH
    # ==========================================
    
    async def search_emails(
        self,
        user_id: str,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca emails com query do Gmail.
        
        Args:
            user_id: ID do usuário
            query: Query de busca (ex: "from:pessoa@email.com", "subject:reunião")
            max_results: Máximo de resultados
            
        Returns:
            Lista de emails encontrados
        """
        try:
            service = await self._get_service(user_id)
            
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_data = await self._get_email_details(service, msg['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info("search_emails_completed", user_id=user_id, query=query, count=len(emails))
            
            return emails
            
        except Exception as e:
            logger.error("search_emails_failed", user_id=user_id, query=query, error=str(e))
            raise
    
    # ==========================================
    # SUMMARY
    # ==========================================
    
    async def get_inbox_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém resumo do inbox.
        
        Returns:
            Contagem de emails por status
        """
        try:
            service = await self._get_service(user_id)
            
            # Contar não lidos
            unread_result = service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=1
            ).execute()
            unread_count = unread_result.get('resultSizeEstimate', 0)
            
            # Contar total no inbox
            inbox_result = service.users().messages().list(
                userId='me',
                q='in:inbox',
                maxResults=1
            ).execute()
            inbox_count = inbox_result.get('resultSizeEstimate', 0)
            
            # Contar starred
            starred_result = service.users().messages().list(
                userId='me',
                q='is:starred',
                maxResults=1
            ).execute()
            starred_count = starred_result.get('resultSizeEstimate', 0)
            
            return {
                'unread_count': unread_count,
                'inbox_count': inbox_count,
                'starred_count': starred_count
            }
            
        except Exception as e:
            logger.error("get_inbox_summary_failed", user_id=user_id, error=str(e))
            raise


# Singleton
gmail_service = GmailService()
