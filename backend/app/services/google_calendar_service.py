"""
TB Personal OS - Google Calendar Service
Integração com Google Calendar API
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import pytz

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from supabase import Client, create_client
from app.core.config import settings
from app.services.google_auth_service import google_auth_service

logger = structlog.get_logger(__name__)


class GoogleCalendarService:
    """
    Serviço de integração com Google Calendar.
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
        """Obtém serviço do Calendar autenticado."""
        credentials = await google_auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError("Google não conectado. Use /connect para autorizar.")
        
        return build('calendar', 'v3', credentials=credentials)
    
    # ==========================================
    # CALENDARS
    # ==========================================
    
    async def list_calendars(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista calendários do usuário."""
        try:
            service = await self._get_service(user_id)
            
            calendar_list = service.calendarList().list().execute()
            
            calendars = []
            for cal in calendar_list.get('items', []):
                calendars.append({
                    'id': cal['id'],
                    'summary': cal.get('summary', 'Sem nome'),
                    'primary': cal.get('primary', False),
                    'background_color': cal.get('backgroundColor'),
                    'access_role': cal.get('accessRole')
                })
            
            return calendars
            
        except Exception as e:
            logger.error("list_calendars_failed", user_id=user_id, error=str(e))
            raise
    
    # ==========================================
    # EVENTS - READ
    # ==========================================
    
    async def get_today_events(
        self,
        user_id: str,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Obtém eventos de hoje."""
        tz = pytz.timezone(settings.OWNER_TIMEZONE)
        today = datetime.now(tz).date()
        
        return await self.get_events_for_date(user_id, today, calendar_id)
    
    async def get_events_for_date(
        self,
        user_id: str,
        target_date: date,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Obtém eventos para uma data específica."""
        tz = pytz.timezone(settings.OWNER_TIMEZONE)
        
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        start_of_day = tz.localize(start_of_day)
        end_of_day = tz.localize(end_of_day)
        
        return await self.get_events_range(
            user_id,
            start_of_day,
            end_of_day,
            calendar_id
        )
    
    async def get_events_range(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = 'primary',
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém eventos em um período.
        """
        try:
            service = await self._get_service(user_id)
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                events.append(self._parse_event(event))
            
            logger.info(
                "events_fetched",
                user_id=user_id,
                count=len(events),
                start=start_time.isoformat(),
                end=end_time.isoformat()
            )
            
            return events
            
        except Exception as e:
            logger.error("get_events_failed", user_id=user_id, error=str(e))
            raise
    
    async def get_upcoming_events(
        self,
        user_id: str,
        hours: int = 24,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Obtém eventos das próximas X horas."""
        tz = pytz.timezone(settings.OWNER_TIMEZONE)
        now = datetime.now(tz)
        end = now + timedelta(hours=hours)
        
        return await self.get_events_range(user_id, now, end, calendar_id)
    
    async def get_week_events(
        self,
        user_id: str,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Obtém eventos da semana."""
        tz = pytz.timezone(settings.OWNER_TIMEZONE)
        now = datetime.now(tz)
        
        # Início da semana (segunda)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Fim da semana (domingo)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return await self.get_events_range(user_id, start, end, calendar_id)
    
    # ==========================================
    # EVENTS - CREATE/UPDATE
    # ==========================================
    
    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = 'primary',
        all_day: bool = False,
        reminders: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Cria um evento no calendário.
        
        Args:
            title: Título do evento
            start_time: Horário de início
            end_time: Horário de fim (padrão: 1 hora após início)
            description: Descrição
            location: Local
            all_day: Se é evento de dia inteiro
            reminders: Lista de minutos antes para lembrete
        """
        try:
            service = await self._get_service(user_id)
            
            if end_time is None:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': title,
                'description': description,
                'location': location,
            }
            
            if all_day:
                event['start'] = {'date': start_time.strftime('%Y-%m-%d')}
                event['end'] = {'date': end_time.strftime('%Y-%m-%d')}
            else:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': settings.OWNER_TIMEZONE
                }
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': settings.OWNER_TIMEZONE
                }
            
            if reminders:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': m} for m in reminders
                    ]
                }
            
            created = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            logger.info(
                "event_created",
                user_id=user_id,
                event_id=created['id'],
                title=title
            )
            
            return self._parse_event(created)
            
        except Exception as e:
            logger.error("create_event_failed", user_id=user_id, error=str(e))
            raise
    
    async def update_event(
        self,
        user_id: str,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Atualiza um evento."""
        try:
            service = await self._get_service(user_id)
            
            # Buscar evento atual
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Aplicar updates
            if 'title' in updates:
                event['summary'] = updates['title']
            if 'description' in updates:
                event['description'] = updates['description']
            if 'location' in updates:
                event['location'] = updates['location']
            if 'start_time' in updates:
                event['start'] = {
                    'dateTime': updates['start_time'].isoformat(),
                    'timeZone': settings.OWNER_TIMEZONE
                }
            if 'end_time' in updates:
                event['end'] = {
                    'dateTime': updates['end_time'].isoformat(),
                    'timeZone': settings.OWNER_TIMEZONE
                }
            
            updated = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info("event_updated", event_id=event_id)
            
            return self._parse_event(updated)
            
        except Exception as e:
            logger.error("update_event_failed", event_id=event_id, error=str(e))
            raise
    
    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> bool:
        """Deleta um evento."""
        try:
            service = await self._get_service(user_id)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info("event_deleted", event_id=event_id)
            return True
            
        except Exception as e:
            logger.error("delete_event_failed", event_id=event_id, error=str(e))
            return False
    
    # ==========================================
    # QUICK ADD
    # ==========================================
    
    async def quick_add(
        self,
        user_id: str,
        text: str,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        Adiciona evento usando linguagem natural.
        Ex: "Reunião com João amanhã às 14h"
        """
        try:
            service = await self._get_service(user_id)
            
            created = service.events().quickAdd(
                calendarId=calendar_id,
                text=text
            ).execute()
            
            logger.info("event_quick_added", text=text, event_id=created['id'])
            
            return self._parse_event(created)
            
        except Exception as e:
            logger.error("quick_add_failed", text=text, error=str(e))
            raise
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    def _parse_event(self, event: Dict) -> Dict[str, Any]:
        """Converte evento da API para formato interno."""
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Determinar se é all-day
        all_day = 'date' in start
        
        if all_day:
            start_time = start.get('date')
            end_time = end.get('date')
        else:
            start_time = start.get('dateTime')
            end_time = end.get('dateTime')
        
        return {
            'id': event['id'],
            'title': event.get('summary', 'Sem título'),
            'description': event.get('description'),
            'location': event.get('location'),
            'start': start_time,
            'end': end_time,
            'all_day': all_day,
            'status': event.get('status'),
            'html_link': event.get('htmlLink'),
            'created': event.get('created'),
            'updated': event.get('updated'),
            'creator': event.get('creator', {}).get('email'),
            'attendees': [
                {
                    'email': a.get('email'),
                    'response': a.get('responseStatus')
                }
                for a in event.get('attendees', [])
            ]
        }
    
    async def format_events_for_message(
        self,
        user_id: str,
        events: List[Dict[str, Any]]
    ) -> str:
        """Formata eventos para mensagem do bot."""
        if not events:
            return "📆 Nenhum evento encontrado."
        
        lines = ["📆 *Agenda:*", ""]
        
        for event in events:
            title = event['title']
            
            if event['all_day']:
                time_str = "Dia inteiro"
            else:
                try:
                    start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    time_str = start.strftime('%H:%M')
                except:
                    time_str = event['start']
            
            line = f"• {time_str} - {title}"
            if event.get('location'):
                line += f" 📍{event['location']}"
            
            lines.append(line)
        
        return "\n".join(lines)


# Instância global
google_calendar_service = GoogleCalendarService()
